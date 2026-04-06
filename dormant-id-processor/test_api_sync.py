#!/usr/bin/env python3
"""
Synchronous API test using requests library.
This will help us determine if the issue is specific to aiohttp.
"""

import requests
from config import Config

def test_token_fetch_sync():
    """Test token fetch using synchronous requests library."""
    config = Config()
    
    print(f"Testing connection to: {config.TOKEN_URL}")
    print(f"Client ID: {config.CLIENT_ID[:10]}...")
    
    data = {
        'client_id': config.CLIENT_ID,
        'client_secret': config.CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    try:
        print("\n🔄 Attempting to fetch token with requests library...")
        response = requests.post(
            config.TOKEN_URL,
            data=data,
            timeout=30
        )
        
        print(f"✅ Response status: {response.status_code}")
        print(f"✅ Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            if 'access_token' in result:
                token = result['access_token']
                print(f"✅ SUCCESS! Token received: {token[:20]}...")
                print(f"Token type: {result.get('token_type', 'N/A')}")
                print(f"Expires in: {result.get('expires_in', 'N/A')} seconds")
                return True
            else:
                print(f"❌ No access_token in response: {result}")
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.Timeout:
        print("❌ TIMEOUT: Connection timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("IBM LOGIN API CONNECTION TEST (SYNC)")
    print("=" * 60)
    
    success = test_token_fetch_sync()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API CONNECTION SUCCESSFUL WITH REQUESTS")
        print("Issue is specific to aiohttp - we can work around this!")
    else:
        print("❌ API CONNECTION FAILED WITH REQUESTS TOO")
        print("This is a network/credentials issue, not a code issue")
    print("=" * 60)

# Made with Bob
