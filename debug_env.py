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

print("\n=== Testing Notion API Connection (with formatted UUID) ===")
try:
    import requests
    
    token = os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_DATABASE_ID')
    
    if token and db_id:
        formatted_id = format_notion_id(db_id)
        
        # Try page retrieval with formatted ID
        page_url = f"https://api.notion.com/v1/pages/{formatted_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28"
        }
        
        print("Testing page retrieval...")
        response = requests.get(page_url, headers=headers, timeout=10)
        print(f"Page response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Successfully connected to Notion page!")
            
            # Try getting blocks
            blocks_url = f"https://api.notion.com/v1/blocks/{formatted_id}/children"
            response = requests.get(blocks_url, headers=headers, timeout=10)
            print(f"Blocks response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                blocks = data.get('results', [])
                print(f"✅ Found {len(blocks)} blocks on the page!")
                
                # Extract and show sample content
                topics = []
                for i, block in enumerate(blocks[:10]):  # First 10 blocks
                    block_type = block.get('type', 'unknown')
                    print(f"Block {i+1}: {block_type}")
                    
                    # Extract text based on block type
                    text = ""
                    if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                        rich_text = block.get(block_type, {}).get("rich_text", [])
                        text = "".join([rt.get("plain_text", "") for rt in rich_text])
                    
                    if text and len(text.strip()) > 2:
                        topics.append(text.strip())
                        print(f"  Content: {text[:50]}...")
                
                print(f"\n✅ Extracted {len(topics)} potential topics:")
                for i, topic in enumerate(topics[:5]):
                    print(f"  {i+1}. {topic}")
                    
            else:
                print(f"❌ Cannot access blocks: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        elif response.status_code == 403:
            print("❌ Permission denied - make sure you've shared the page with your integration!")
            print("Go to your Notion page → Share → Invite → Search for 'DSA Bot Scraper'")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Error details: {response.text[:200]}")
    else:
        print("❌ Missing credentials")
        
except Exception as e:
    print(f"❌ Connection test failed: {e}")

print("\n=== Fix for your bot ===")
print("Update your .env file with the formatted UUID:")
print(f"NOTION_DATABASE_ID={format_notion_id(os.getenv('NOTION_DATABASE_ID', ''))}")
print("\nOr the bot code will auto-format it for you with the updated notion_client.py")