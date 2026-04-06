#!/usr/bin/env python3
"""
Final API test using the actual APIService class.
"""

import asyncio
from config import Config
from api_service import APIService

async def test_api_service():
    """Test the APIService with requests library."""
    config = Config()
    
    print(f"Testing connection to: {config.TOKEN_URL}")
    print(f"Client ID: {config.CLIENT_ID[:10]}...")
    
    async with APIService(config) as api_service:
        try:
            print("\n🔄 Attempting to fetch token...")
            token = await api_service._fetch_token()
            print(f"✅ SUCCESS! Token received: {token[:20]}...")
            return True
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("IBM LOGIN API CONNECTION TEST (FINAL)")
    print("=" * 60)
    
    success = asyncio.run(test_api_service())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API SERVICE WORKING!")
        print("Ready to process dormant IDs!")
    else:
        print("❌ API SERVICE FAILED")
    print("=" * 60)

# Made with Bob
