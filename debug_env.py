# debug_env_fixed.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

def format_notion_id(notion_id):
    """Convert 32-char hex string to UUID format"""
    if not notion_id or len(notion_id) != 32:
        return notion_id
    
    # Remove any existing dashes
    clean_id = notion_id.replace('-', '')
    
    # Format as UUID: 8-4-4-4-12
    formatted = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
    return formatted

print("=== Environment Variables Debug ===")
print(f"DISCORD_TOKEN: {'✅ Set' if os.getenv('DISCORD_TOKEN') else '❌ Missing'}")
print(f"NOTION_TOKEN: {'✅ Set' if os.getenv('NOTION_TOKEN') else '❌ Missing'}")
print(f"NOTION_DATABASE_ID: {'✅ Set' if os.getenv('NOTION_DATABASE_ID') else '❌ Missing'}")

if os.getenv('NOTION_TOKEN'):
    token = os.getenv('NOTION_TOKEN')
    print(f"NOTION_TOKEN preview: {token[:10]}...")

if os.getenv('NOTION_DATABASE_ID'):
    db_id = os.getenv('NOTION_DATABASE_ID')
    print(f"NOTION_DATABASE_ID: {db_id}")
    formatted_id = format_notion_id(db_id)
    print(f"Formatted UUID: {formatted_id}")

print("\n=== Testing Notion API Connection (Checking Both Page and Database) ===")
try:
    import requests
    import os
    from utils.notion_client import format_notion_id

    token = os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_DATABASE_ID')
    
    if token and db_id:
        formatted_id = format_notion_id(db_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28"
        }

        # 1. Test as a Page
        page_url = f"https://api.notion.com/v1/pages/{formatted_id}"
        print("Testing as a page...")
        page_response = requests.get(page_url, headers=headers, timeout=10)
        print(f"Page response status: {page_response.status_code}")

        if page_response.status_code == 200:
            print("✅ Successfully connected to Notion as a PAGE.")
        else:
            print("❌ Not a page. Trying as a database...")

            # 2. Test as a Database
            db_url = f"https://api.notion.com/v1/databases/{formatted_id}/query"
            db_response = requests.post(db_url, headers=headers, json={}, timeout=10)
            print(f"Database response status: {db_response.status_code}")

            if db_response.status_code == 200:
                print("✅ Successfully connected to Notion as a DATABASE.")
                results = db_response.json().get("results", [])
                print(f"✅ Found {len(results)} items in the database!")
            else:
                print(f"❌ Failed to connect as either a page or a database.")
                print(f"Error details: {db_response.text[:200]}")

    else:
        print("❌ Missing credentials")
        
except Exception as e:
    print(f"❌ Connection test failed: {e}")

print("\n=== Fix for your bot ===")
print("Update your .env file with the formatted UUID:")
print(f"NOTION_DATABASE_ID={format_notion_id(os.getenv('NOTION_DATABASE_ID', ''))}")
print("\nOr the bot code will auto-format it for you with the updated notion_client.py")