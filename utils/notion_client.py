# utils/notion_client.py - ROBUST SCRAPING VERSION
import os
import requests
from bs4 import BeautifulSoup
import logging
import re
import json

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def format_notion_id(notion_id):
    """Convert 32-char hex string to UUID format that Notion API expects"""
    if not notion_id:
        return notion_id
    clean_id = notion_id.replace('-', '').replace(' ', '')
    if len(clean_id) != 32:
        return notion_id
    return f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- This is the new, more robust scraping function ---
def get_topics_from_public_page(notion_public_url):
    """
    Scrapes a public Notion page by mimicking the internal API call it uses
    to load its content. This is more reliable than parsing raw HTML.
    """
    try:
        logging.info(f"Attempting robust scrape of public Notion page: {notion_public_url}")
        
        # Extract the page ID from the URL
        page_id_match = re.search(r'([a-f0-9]{32})', notion_public_url)
        if not page_id_match:
             # Fallback for UUID format with dashes
            page_id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', notion_public_url)
        
        if not page_id_match:
            logging.error("Could not find a valid Notion page ID in the URL.")
            return None

        page_id = page_id_match.group(1).replace('-', '')
        logging.info(f"Extracted page ID: {page_id}")

        # This is the internal API endpoint Notion uses to load page data
        api_url = "https://www.notion.so/api/v3/loadPageChunk"
        
        payload = {
            "pageId": format_notion_id(page_id), # Use the formatted UUID
            "limit": 100, # Increased limit to get more blocks
            "cursor": {"stack": []},
            "chunkNumber": 0,
            "verticalColumns": False
        }
        
        session = requests.Session()
        session.headers.update(HEADERS)
        
        response = session.post(api_url, json=payload, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # The content is stored in the 'block' key
        blocks = data.get("recordMap", {}).get("block", {})
        
        if not blocks:
            logging.error("No content blocks found in the API response.")
            return None
            
        topics = []
        for block_id, block_value in blocks.items():
            # Look for blocks that have a 'properties' attribute, which usually contains text
            if 'properties' in block_value.get('value', {}):
                properties = block_value['value']['properties']
                if 'title' in properties:
                    # The text is stored in a list of lists format, e.g., [['Arrays (operations, applications)']]
                    text_segments = properties['title']
                    full_text = "".join(segment[0] for segment in text_segments if segment)
                    # Clean the text and check if it's a likely topic
                    cleaned_text = re.sub(r'^\d+\.\s*', '', full_text).strip() # Remove numbering
                    if is_likely_dsa_topic(cleaned_text):
                        topics.append(cleaned_text)

        logging.info(f"Extracted {len(topics)} potential topics using the internal API method.")
        if topics:
            logging.info(f"Sample topics: {topics[:5]}")
        
        return topics if topics else None
        
    except Exception as e:
        logging.error(f"Failed to parse public Notion page with robust method: {e}", exc_info=True)
        return None


def get_topics_from_notion_api():
    """Try both database query and page retrieval with proper UUID formatting"""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logging.info("Missing NOTION_TOKEN or NOTION_DATABASE_ID - skipping API method")
        return None
    
    formatted_id = format_notion_id(NOTION_DATABASE_ID)
    logging.info(f"Using formatted ID: {formatted_id}")
    
    try:
        topics = try_page_retrieval(formatted_id)
        if topics:
            logging.info(f"Successfully retrieved {len(topics)} topics from page")
            return topics
    except Exception as e:
        logging.warning(f"Page retrieval failed: {e}")
    
    try:
        topics = try_database_query(formatted_id)
        if topics:
            logging.info(f"Successfully retrieved {len(topics)} topics from database")
            return topics
    except Exception as e:
        logging.warning(f"Database query failed: {e}")
    
    return None

def try_database_query(formatted_id):
    url = f"https://api.notion.com/v1/databases/{formatted_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={}, timeout=15)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    topics = []
    for result in data.get("results", []):
        properties = result.get("properties", {})
        for prop_name in ["Name", "Topic", "Title", "name", "topic", "title"]:
            if prop_name in properties:
                prop_data = properties[prop_name]
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    name = "".join([text.get("plain_text", "") for text in prop_data["title"]])
                    if name and name.strip():
                        topics.append(name.strip())
                        break
    return topics if topics else None

def try_page_retrieval(formatted_id):
    page_url = f"https://api.notion.com/v1/pages/{formatted_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.get(page_url, headers=headers, timeout=15)
    response.raise_for_status()
    blocks_url = f"https://api.notion.com/v1/blocks/{formatted_id}/children"
    response = requests.get(blocks_url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    topics = []
    for block in data.get("results", []):
        text = extract_text_from_block(block)
        if text and is_likely_dsa_topic(text):
            topics.append(text.strip())
    return topics if topics else None

def extract_text_from_block(block):
    block_type = block.get("type", "")
    if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do"]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        return "".join([text.get("plain_text", "") for text in rich_text])
    return ""

def is_likely_dsa_topic(text):
    """Check if text looks like a DSA topic (made slightly less strict)"""
    if not text or len(text.strip()) < 3 or len(text) > 100:
        return False
    clean_text = re.sub(r'[^\w\s\(\)\[\]/-]', '', text.strip()).lower()
    skip_keywords = ['list of important topics for dsa', 'core foundations', 'basic searching', 'basic sorting', 'complex sorting', 'hashing']
    if clean_text in skip_keywords:
        return False
    # General check for alpha characters
    if not any(char.isalpha() for char in clean_text):
        return False
    return True