"""High-performance Cloudant client with bookmark-based pagination."""
import asyncio
import aiohttp
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime
import logging

from backend.config import config

logger = logging.getLogger(__name__)


class CloudantClient:
    """Async Cloudant client with bookmark pagination."""
    
    def __init__(self):
        """Initialize client with reusable session."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.API_BASE_URL
        self.auth = aiohttp.BasicAuth(config.API_KEY, config.API_PASSWORD)
        
    async def __aenter__(self):
        """Create session on context entry."""
        self.session = aiohttp.ClientSession(
            auth=self.auth,
            timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT),
            connector=aiohttp.TCPConnector(limit=config.MAX_CONCURRENT_REQUESTS)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session on context exit."""
        if self.session:
            await self.session.close()
            
    async def fetch_batch(
        self,
        start_date: str,
        end_date: str,
        bookmark: Optional[str] = None,
        limit: int = 5000
    ) -> Dict:
        """
        Fetch a single batch using bookmark pagination.
        
        Args:
            start_date: ISO format start date (e.g., "2026-03-18T00:00:00Z")
            end_date: ISO format end date (e.g., "2026-03-18T23:59:59Z")
            bookmark: Pagination bookmark (None for first page)
            limit: Batch size
            
        Returns:
            Dict with 'rows', 'bookmark', and 'has_more' keys
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use 'async with' context.")
        
        # Parse ISO dates and convert to view's array format: [true, year, month, day, hour, minute, second]
        from datetime import datetime
        import json
        
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Format: [true, year, month, day, hour, minute, second]
        start_key = [True, start_dt.year, start_dt.month, start_dt.day, start_dt.hour, start_dt.minute, start_dt.second]
        end_key = [True, end_dt.year, end_dt.month, end_dt.day, end_dt.hour, end_dt.minute, end_dt.second]
        
        params = {
            "limit": limit,
            "include_docs": "false",
            "reduce": "false",
            "startkey": json.dumps(start_key),
            "endkey": json.dumps(end_key)
        }
        
        if bookmark:
            params["bookmark"] = bookmark
            
        try:
            async with self.session.get(self.base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                return {
                    "rows": data.get("rows", []),
                    "bookmark": data.get("bookmark"),
                    "has_more": len(data.get("rows", [])) == limit
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Cloudant API error: {e}")
            raise
            
    async def stream_all(
        self,
        start_date: str,
        end_date: str,
        batch_size: int = 5000
    ) -> AsyncIterator[List[Dict]]:
        """
        Stream all records using bookmark pagination.
        
        Args:
            start_date: ISO format start date
            end_date: ISO format end date
            batch_size: Records per batch
            
        Yields:
            Batches of records
        """
        bookmark = None
        has_more = True
        
        while has_more:
            result = await self.fetch_batch(
                start_date=start_date,
                end_date=end_date,
                bookmark=bookmark,
                limit=batch_size
            )
            
            rows = result["rows"]
            if rows:
                yield rows
                
            bookmark = result["bookmark"]
            has_more = result["has_more"]
            
            # Prevent tight loop if no data
            if not rows:
                break

# Made with Bob
