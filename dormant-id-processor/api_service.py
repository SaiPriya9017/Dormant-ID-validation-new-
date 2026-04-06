"""
API Service Module - Handles all external API interactions.

This module is responsible for:
- OAuth token generation and caching
- Automatic token refresh on 401 errors
- Email retrieval from user IDs (batch processing)
- User status checking (ACTIVE/DORMANT) via Blue Pages
- Retry logic with exponential backoff
- Rate limiting and error handling

All API interactions are isolated in this module for clean separation of concerns.
"""

import asyncio
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import logging

logger = logging.getLogger(__name__)


class APIService:
    """Handles all API interactions with token management and retry logic."""

    def __init__(self, config):
        """
        Initialize API service with configuration.

        Args:
            config: Configuration object containing API credentials and endpoints
        """
        self.config = config
        self.session: Optional[requests.Session] = None
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        # Create requests session for connection pooling
        self.session = requests.Session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            self.session.close()

    async def _ensure_token(self) -> str:
        """
        Ensure we have a valid token, refreshing if necessary.

        Returns:
            str: Valid OAuth token

        Raises:
            Exception: If token generation fails
        """
        async with self._token_lock:
            # Check if token is still valid (with 5-minute buffer)
            if self.token and self.token_expires_at:
                if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                    return self.token

            # Token expired or doesn't exist, fetch new one
            logger.info("Fetching new OAuth token")
            self.token = await self._fetch_token()
            # Token valid for 2 hours (7200 seconds from IBM API)
            self.token_expires_at = datetime.now() + timedelta(seconds=7200)
            logger.info("Successfully obtained new token")
            return self.token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, asyncio.TimeoutError)),
    )
    async def _fetch_token(self) -> str:
        """
        Fetch OAuth token from IBM Login API.
        
        Uses the endpoint configured in TOKEN_URL environment variable.
        Default: POST https://login.ibm.com/v1.0/endpoint/default/token
        With form data: client_id, client_secret, grant_type=client_credentials

        Returns:
            str: OAuth access token

        Raises:
            Exception: If token fetch fails after retries
        """
        # Prepare URL-encoded form data for token request
        data = {
            'client_id': self.config.CLIENT_ID,
            'client_secret': self.config.CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }

        try:
            # Run synchronous request in thread pool
            response = await asyncio.to_thread(
                self.session.post,
                self.config.TOKEN_URL,
                data=data,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            # IBM API returns access_token in response
            if 'access_token' not in result:
                raise ValueError("No access_token in response")
            
            logger.info("Successfully fetched OAuth token")
            return result["access_token"]
            
        except requests.RequestException as e:
            logger.error(f"Error fetching token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching token: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, asyncio.TimeoutError)),
    )
    async def get_emails(self, user_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Retrieve emails for a batch of user IDs using IBM Login API.
        
        Uses the endpoint configured in USERS_API_URL environment variable.
        Default: GET https://login.ibm.com/v2.0/Users
        With query params: filter=userName eq "email@ibm.com", attributes=userName

        Args:
            user_ids: List of user IDs (usernames/emails) to fetch

        Returns:
            Dict mapping user_id -> email (or None if not found)

        Raises:
            Exception: If API call fails after retries
        """
        token = await self._ensure_token()
        result = {}
        
        # Process in smaller sub-batches to avoid URL length limits
        batch_size = 20
        
        for i in range(0, len(user_ids), batch_size):
            sub_batch = user_ids[i:i + batch_size]
            
            # Build OR filter for sub-batch using 'id' field (not userName)
            # userName expects email, id expects user ID
            filter_parts = [f'id eq "{uid}"' for uid in sub_batch]
            filter_query = " or ".join(filter_parts)

            params = {
                "filter": filter_query,
                "attributes": "id,userName,active"
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "dormant-id-processor/1.0"
            }

            try:
                response = await asyncio.to_thread(
                    self.session.get,
                    self.config.USERS_API_URL,
                    params=params,
                    headers=headers,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                # Handle 401 (token expired)
                if response.status_code == 401:
                    logger.warning("Token expired, refreshing...")
                    async with self._token_lock:
                        self.token = None
                    token = await self._ensure_token()
                    headers["Authorization"] = f"Bearer {token}"

                    # Retry with new token
                    response = await asyncio.to_thread(
                        self.session.get,
                        self.config.USERS_API_URL,
                        params=params,
                        headers=headers,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                
                response.raise_for_status()
                data = response.json()

                # Parse response - Accept ALL emails returned by API
                for user in data.get("Resources", []):
                    user_id = user.get("id")
                    user_name = user.get("userName")
                    
                    if user_id and user_name:
                        # Match by ID (exact match)
                        if user_id in sub_batch:
                            result[user_id] = user_name
                            logger.info(f"✅ Found email for {user_id}: {user_name}")

                # Mark users not found as None
                for uid in sub_batch:
                    if uid not in result:
                        result[uid] = None

            except requests.RequestException as e:
                logger.error(f"Error fetching emails for batch: {e}")
                for uid in sub_batch:
                    if uid not in result:
                        result[uid] = None

        logger.info(f"Retrieved emails for {len([v for v in result.values() if v])} out of {len(user_ids)} users")
        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, asyncio.TimeoutError)),
    )
    async def get_user_status(self, email: str) -> Optional[str]:
        """
        Check if a user is ACTIVE or DORMANT via BluePages API.
        
        Uses the endpoint configured in BLUEPAGES_API_URL environment variable.
        Default: https://bluepages.ibm.com/BpHttpApisv3/slaphapi
        
        BluePages API returns LDIF format with:
        - "# rc=0, count=1, message=Success" → User found in BluePages (ACTIVE)
        - "# rc=0, count=0, message=Success" → User NOT found in BluePages (DORMANT)

        Args:
            email: User email to check status for

        Returns:
            str: "ACTIVE" if count>0, "DORMANT" if count=0, None on error

        Raises:
            Exception: If API call fails after retries
        """
        # BluePages API endpoint (public, no authentication required)
        bluepages_url = f"{self.config.BLUEPAGES_API_URL}?ibmperson/(mail={email}).list/bytext?*"

        try:
            response = await asyncio.to_thread(
                self.session.get,
                bluepages_url,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            response_text = response.text
            
            # Parse LDIF response for rc and count
            # Look for line like: "# rc=0, count=1, message=Success"
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('# rc='):
                    # Extract count value
                    if 'count=' in line:
                        try:
                            # Parse: "# rc=0, count=1, message=Success"
                            count_part = line.split('count=')[1].split(',')[0].strip()
                            count = int(count_part)
                            
                            if count > 0:
                                logger.info(f"✅ ACTIVE (BluePages count={count}): {email}")
                                return "ACTIVE"
                            else:
                                logger.info(f"❌ DORMANT (BluePages count=0): {email}")
                                return "DORMANT"
                        except (ValueError, IndexError) as e:
                            logger.error(f"Error parsing count from BluePages response: {e}")
                            return None
            
            # If we couldn't find the rc/count line, log the response
            logger.warning(f"Could not parse BluePages response for {email}")
            logger.debug(f"Response text: {response_text[:500]}")
            return None

        except requests.RequestException as e:
            logger.error(f"Error checking BluePages status for {email}: {e}")
            return None

    async def process_batch(
        self, batch_data: List[Tuple[str, dict]]
    ) -> Dict[str, List[dict]]:
        """
        Process a complete batch: get emails and check status, return original records with email added.

        Args:
            batch_data: List of (user_id, original_record) tuples

        Returns:
            Dict with "active" and "dormant" keys containing lists of records
        """
        # Extract user IDs and create mapping to original records
        user_ids = [user_id for user_id, _ in batch_data]
        record_map = {user_id: record for user_id, record in batch_data}
        
        # Step 1: Get emails for all user IDs
        email_map = await self.get_emails(user_ids)

        # Step 2: Check status for users with emails
        results_active = []
        results_dormant = []
        status_tasks = []
        user_email_pairs = []
        
        for user_id, email in email_map.items():
            if email:
                status_tasks.append(self.get_user_status(email))
                user_email_pairs.append((user_id, email))

        # Execute status checks concurrently
        if status_tasks:
            statuses = await asyncio.gather(*status_tasks, return_exceptions=True)
            
            # Match statuses back to users and add email to original records
            for idx, (user_id, email) in enumerate(user_email_pairs):
                status = statuses[idx]
                if isinstance(status, Exception):
                    logger.error(f"Error getting status for {email}: {status}")
                    status = None
                
                # Get original record and add email field
                original_record = record_map[user_id].copy()
                original_record["email"] = email  # ALWAYS keep the email
                
                # Classify ONLY based on 'active' status from API
                if status == "ACTIVE":
                    results_active.append(original_record)
                    logger.info(f"✅ ACTIVE: {user_id} → {email}")
                elif status == "DORMANT":
                    results_dormant.append(original_record)
                    logger.info(f"❌ DORMANT: {user_id} → {email}")
                else:
                    # Error case - keep email but default to dormant
                    results_dormant.append(original_record)
                    logger.warning(f"⚠️  ERROR (defaulting to DORMANT): {user_id} → {email}")
        
        # Handle users without emails
        for user_id, email in email_map.items():
            if not email:
                original_record = record_map[user_id].copy()
                original_record["email"] = ""
                results_dormant.append(original_record)

        logger.info(f"Processed batch: {len(results_active)} active, {len(results_dormant)} dormant")
        return {"active": results_active, "dormant": results_dormant}

# Made with Bob
