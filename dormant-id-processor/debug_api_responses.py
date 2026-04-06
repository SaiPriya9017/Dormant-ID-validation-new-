#!/usr/bin/env python3
"""
Debug script to show API responses for each user ID.
This will help identify why emails are empty.
"""

import asyncio
import json
from config import Config
from api_service import APIService
from file_processor import FileProcessor

async def debug_api_responses():
    """Test API responses for sample user IDs and save to debug file."""
    config = Config()
    
    print("=" * 60)
    print("DEBUG: API Response Analysis")
    print("=" * 60)
    
    # Read first 10 user IDs from sample file
    from pathlib import Path
    file_path = Path("./input/sample_users.jsonl")
    user_ids = []
    
    print(f"\n📂 Reading user IDs from: {file_path}")
    
    # Create FileProcessor instance
    processor = FileProcessor()
    async for user_id, record in processor.stream_records(file_path, skip_lines=0):
        user_ids.append((user_id, record))
        if len(user_ids) >= 10:  # Test first 10
            break
    
    print(f"✅ Found {len(user_ids)} user IDs to test\n")
    
    # Test API for each user ID
    debug_results = []
    
    async with APIService(config) as api_service:
        print("🔄 Fetching token...")
        token = await api_service._ensure_token()
        print(f"✅ Token: {token[:20]}...\n")
        
        print("🔍 Testing each user ID:\n")
        
        for idx, (user_id, record) in enumerate(user_ids, 1):
            print(f"[{idx}/{len(user_ids)}] Testing: {user_id}")
            
            # Get email
            email_map = await api_service.get_emails([user_id])
            email = email_map.get(user_id)
            
            result = {
                "user_id": user_id,
                "original_record": record,
                "email_found": email,
                "status": None,
                "api_response": "No email found"
            }
            
            if email:
                print(f"  ✅ Email found: {email}")
                
                # Get status
                status = await api_service.get_user_status(email)
                result["status"] = status
                result["api_response"] = f"Email: {email}, Status: {status}"
                
                print(f"  📊 Status: {status}")
            else:
                print(f"  ❌ No email found")
            
            debug_results.append(result)
            print()
    
    # Save to debug file
    debug_file = "./output/debug_api_responses.json"
    with open(debug_file, 'w') as f:
        json.dump(debug_results, f, indent=2)
    
    print("=" * 60)
    print(f"✅ Debug results saved to: {debug_file}")
    print("=" * 60)
    
    # Summary
    emails_found = sum(1 for r in debug_results if r["email_found"])
    print(f"\n📊 Summary:")
    print(f"  Total tested: {len(debug_results)}")
    print(f"  Emails found: {emails_found}")
    print(f"  No email: {len(debug_results) - emails_found}")
    
    if emails_found == 0:
        print("\n⚠️  No emails found for any user ID!")
        print("   This means:")
        print("   1. User IDs don't exist in IBM system")
        print("   2. OR API endpoint/credentials are incorrect")
        print("   3. OR user IDs need different format")
    
    return debug_results

if __name__ == "__main__":
    print("\n🔍 Starting API Response Debug...\n")
    results = asyncio.run(debug_api_responses())
    print("\n✅ Debug complete! Check output/debug_api_responses.json\n")

# Made with Bob
