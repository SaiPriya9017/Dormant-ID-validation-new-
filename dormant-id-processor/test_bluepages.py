#!/usr/bin/env python3
"""
Test script to verify BluePages API integration.
Tests with known emails to check ACTIVE/DORMANT classification.
"""

import asyncio
import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bluepages_sync(email: str):
    """Test BluePages API with a single email (synchronous)."""
    bluepages_base_url = os.getenv("BLUEPAGES_API_URL", "https://bluepages.ibm.com/BpHttpApisv3/slaphapi")
    url = f"{bluepages_base_url}?ibmperson/(mail={email}).list/bytext?*"
    
    print(f"\n{'='*80}")
    print(f"Testing BluePages API for: {email}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        response_text = response.text
        print(f"Response Status: {response.status_code}")
        print(f"Response Length: {len(response_text)} bytes\n")
        
        # Parse for rc and count
        found_status = False
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('# rc='):
                print(f"Status Line: {line}")
                found_status = True
                
                # Extract count
                if 'count=' in line:
                    try:
                        count_part = line.split('count=')[1].split(',')[0].strip()
                        count = int(count_part)
                        
                        if count > 0:
                            print(f"✅ Result: ACTIVE (count={count})")
                            print(f"   → User found in BluePages")
                        else:
                            print(f"❌ Result: DORMANT (count=0)")
                            print(f"   → User NOT found in BluePages")
                        
                        return count > 0
                    except (ValueError, IndexError) as e:
                        print(f"❌ Error parsing count: {e}")
                        return None
        
        if not found_status:
            print("⚠️  Warning: Could not find status line in response")
            print("\nFirst 500 chars of response:")
            print(response_text[:500])
        
        return None
        
    except requests.RequestException as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Test with multiple emails."""
    
    # Test emails (mix of potentially active and dormant)
    test_emails = [
        "Sai.Priya@ibm.com",  # Your email (should be ACTIVE)
        "RAHULJPSHUKLA@GMAIL.COM",  # From test data (might be DORMANT)
        "biz1950@gmail.com",  # From test data (was classified as DORMANT)
        "pajduch@o2.pl",  # From test data (non-IBM domain)
    ]
    
    print("\n" + "="*80)
    print("BluePages API Test Suite")
    print("="*80)
    
    results = {}
    for email in test_emails:
        result = test_bluepages_sync(email)
        results[email] = result
        print()  # Blank line between tests
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for email, is_active in results.items():
        if is_active is True:
            status = "✅ ACTIVE"
        elif is_active is False:
            status = "❌ DORMANT"
        else:
            status = "⚠️  ERROR"
        print(f"{status:15} {email}")
    
    print("\n" + "="*80)
    print("Classification Logic:")
    print("  - count > 0  → ACTIVE (user found in BluePages)")
    print("  - count = 0  → DORMANT (user NOT in BluePages)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob
