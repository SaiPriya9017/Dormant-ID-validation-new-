#!/usr/bin/env python3
"""
Quick API connection test script.
Tests if we can successfully fetch a token from IBM Login API.
"""

import asyncio
import aiohttp
import ssl
from config import Config

async def test_token_fetch():
    """Test token fetch with improved SSL/connector settings."""
    config = Config()
    
    print(f"Testing connection to: {config.TOKEN_URL}")
    print(f"Client ID: {config.CLIENT_ID[:10]}...")
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    
    # Create connector
    connector = aiohttp.TCPConnector(
        ssl=ssl_context,
        limit=100,
        ttl_dns_cache=300,
        force_close=False,
        enable_cleanup_closed=True
    )
    
    # Create session
    timeout = aiohttp.ClientTimeout(
        total=30,
        connect=30,
        sock_connect=30,
        sock_read=30
    )
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        data = {
            'client_id': config.CLIENT_ID,
            'client_secret': config.CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        
        try:
            print("\n🔄 Attempting to fetch token...")
            async with session.post(config.TOKEN_URL, data=data) as response:
                print(f"✅ Response status: {response.status}")
                print(f"✅ Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    if 'access_token' in result:
                        token = result['access_token']
                        print(f"✅ SUCCESS! Token received: {token[:20]}...")
                        return True
                    else:
                        print(f"❌ No access_token in response: {result}")
                        return False
                else:
                    text = await response.text()
                    print(f"❌ Failed with status {response.status}")
                    print(f"Response: {text}")
                    return False
                    
        except asyncio.TimeoutError:
            print("❌ TIMEOUT: Connection timed out after 30 seconds")
            return False
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("IBM LOGIN API CONNECTION TEST")
    print("=" * 60)
    
    success = asyncio.run(test_token_fetch())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API CONNECTION SUCCESSFUL")
        print("The main processor should work now!")
    else:
        print("❌ API CONNECTION FAILED")
        print("Please check:")
        print("  1. Network connectivity")
        print("  2. Credentials in .env file")
        print("  3. Firewall/VPN settings")
    print("=" * 60)

# Made with Bob
