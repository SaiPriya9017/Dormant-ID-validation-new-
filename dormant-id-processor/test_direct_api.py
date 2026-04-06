#!/usr/bin/env python3
"""
Test direct API call to match Insomnia request exactly.
"""

import asyncio
import requests
from config import Config

async def test_direct_api():
    """Test API with exact same format as Insomnia."""
    config = Config()
    
    # Get token first
    print("🔄 Getting token...")
    token_response = requests.post(
        config.TOKEN_URL,
        data={
            'client_id': config.CLIENT_ID,
            'client_secret': config.CLIENT_SECRET,
            'grant_type': 'client_credentials'
        },
        timeout=30
    )
    
    token = token_response.json()['access_token']
    print(f"✅ Token: {token[:20]}...\n")
    
    # Test different query formats
    user_id = "W270NAS7KC2"
    
    print(f"Testing user ID: {user_id}\n")
    
    # Format 1: userName eq "ID"
    print("📋 Format 1: userName eq \"ID\"")
    response1 = requests.get(
        config.USERS_API_URL,
        params={
            "filter": f'userName eq "{user_id}"',
            "attributes": "userName,id,active"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "*/*"
        },
        timeout=30
    )
    print(f"Status: {response1.status_code}")
    print(f"Response: {response1.json()}\n")
    
    # Format 2: id eq "ID"  
    print("📋 Format 2: id eq \"ID\"")
    response2 = requests.get(
        config.USERS_API_URL,
        params={
            "filter": f'id eq "{user_id}"',
            "attributes": "userName,id,active"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "*/*"
        },
        timeout=30
    )
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.json()}\n")
    
    # Format 3: Just get by ID in URL
    print("📋 Format 3: Direct ID in URL")
    response3 = requests.get(
        f"{config.USERS_API_URL}/{user_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "*/*"
        },
        timeout=30
    )
    print(f"Status: {response3.status_code}")
    try:
        print(f"Response: {response3.json()}\n")
    except:
        print(f"Response: {response3.text}\n")

if __name__ == "__main__":
    asyncio.run(test_direct_api())

# Made with Bob
