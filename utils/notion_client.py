# utils/notion_client.py - IMPROVED VERSION
import os
import requests
from bs4 import BeautifulSoup
import logging
import re

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def format_notion_id(notion_id):
    """Convert 32-char hex string to UUID format that Notion API expects"""
    if not notion_id:
        return notion_id
    
    # Remove any existing dashes and spaces
    clean_id = notion_id.replace('-', '').replace(' ', '')
    
    # Must be exactly 32 hex characters
    if len(clean_id) != 32:
        return notion_id
    
    # Format as UUID: 8-4-4-4-12
    formatted = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
    return formatted

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_topics_from_notion_api():
    """Try both database query and page retrieval with proper UUID formatting"""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logging.info("Missing NOTION_TOKEN or NOTION_DATABASE_ID - skipping API method")
        return None
    
    # Format the ID properly
    formatted_id = format_notion_id(NOTION_DATABASE_ID)
    logging.info(f"Using formatted ID: {formatted_id}")
    
    # Try as page first (since most Notion links are pages)
    try:
        topics = try_page_retrieval(formatted_id)
        if topics:
            logging.info(f"Successfully retrieved {len(topics)} topics from page")
            return topics
    except Exception as e:
        logging.warning(f"Page retrieval failed: {e}")
    
    # Then try as database
    try:
        topics = try_database_query(formatted_id)
        if topics:
            logging.info(f"Successfully retrieved {len(topics)} topics from database")
            return topics
    except Exception as e:
        logging.warning(f"Database query failed: {e}")
    
    return None

def try_database_query(formatted_id):
    """Try to query as a database"""
    url = f"https://api.notion.com/v1/databases/{formatted_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json={}, timeout=15)
    
    if response.status_code == 404:
        logging.info("Resource is not a database, trying as page...")
        return None
        
    response.raise_for_status()
    data = response.json()
    
    topics = []
    for result in data.get("results", []):
        properties = result.get("properties", {})
        
        # Try different property names
        name = None
        for prop_name in ["Name", "Topic", "Title", "name", "topic", "title"]:
            if prop_name in properties:
                prop_data = properties[prop_name]
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    name = "".join([text.get("plain_text", "") for text in prop_data["title"]])
                    break
                elif prop_data.get("type") == "rich_text" and prop_data.get("rich_text"):
                    name = "".join([text.get("plain_text", "") for text in prop_data["rich_text"]])
                    break
        
        if name and name.strip():
            topics.append(name.strip())
    
    return topics if topics else None

def try_page_retrieval(formatted_id):
    """Try to retrieve as a page and extract blocks"""
    # First get the page
    page_url = f"https://api.notion.com/v1/pages/{formatted_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(page_url, headers=headers, timeout=15)
    response.raise_for_status()
    
    # Then get the blocks
    blocks_url = f"https://api.notion.com/v1/blocks/{formatted_id}/children"
    response = requests.get(blocks_url, headers=headers, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    topics = []
    
    for block in data.get("results", []):
        # Extract text from different block types
        text = extract_text_from_block(block)
        if text and is_likely_dsa_topic(text):
            topics.append(text.strip())
    
    return topics if topics else None

def extract_text_from_block(block):
    """Extract text from a Notion block"""
    block_type = block.get("type", "")
    
    if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        return "".join([text.get("plain_text", "") for text in rich_text])
    
    return ""

def is_likely_dsa_topic(text):
    """Check if text looks like a DSA topic"""
    if not text or len(text.strip()) < 3 or len(text) > 100:
        return False
    
    # Clean text
    clean_text = re.sub(r'[^\w\s\(\)\[\]/-]', '', text.strip())
    
    # Skip obvious non-topics
    skip_patterns = [
        r'^\d+\.',  # Numbers
        r'notion',  # Notion-related
        r'^(page|created|edited|share|duplicate)',
        r'^(introduction|overview|conclusion)',
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, clean_text.lower()):
            return False
    
    # Look for DSA keywords
    dsa_keywords = [
        'array', 'list', 'tree', 'graph', 'sort', 'search', 'hash', 
        'stack', 'queue', 'heap', 'algorithm', 'dynamic', 'greedy',
        'binary', 'linear', 'dfs', 'bfs', 'dp', 'backtrack', 'trie',
        'linked', 'merge', 'quick', 'bubble', 'insertion', 'selection'
    ]
    
    text_lower = clean_text.lower()
    if any(keyword in text_lower for keyword in dsa_keywords):
        return True
    
    # Short phrases might be topics
    words = clean_text.split()
    if 1 <= len(words) <= 4:
        return True
    
    return False

def get_topics_from_public_page(notion_public_url):
    """Enhanced public page scraping with better selectors"""
    try:
        logging.info(f"Attempting to parse public Notion page: {notion_public_url}")
        
        # Try different approaches to get the page
        session = requests.Session()
        session.headers.update(HEADERS)
        
        response = session.get(notion_public_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Debug: Save HTML for inspection (remove in production)
        # with open("debug_notion_page.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)
        
        candidates = []
        
        # Enhanced selectors for Notion pages
        selectors = [
            # Notion-specific selectors
            'div[data-block-id] div[data-content-editable-leaf="true"]',
            'div[data-block-id] [role="textbox"]',
            'div[contenteditable="true"]',
            '[data-block-id] .notranslate',
            
            # General content selectors
            'div[data-block-id]',
            '.notion-page-content div',
            'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                
                if not text or len(text) > 100:
                    continue
                
                # Enhanced filtering
                if is_likely_dsa_topic(text):
                    candidates.append(text)
        
        # Also try getting all text and splitting by lines
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split('\n')]
        for line in lines:
            if is_likely_dsa_topic(line):
                candidates.append(line)
        
        # Clean and deduplicate
        seen = set()
        clean_topics = []
        
        for candidate in candidates:
            # Enhanced cleaning
            cleaned = re.sub(r'[^\w\s\(\)\[\]/-]', '', candidate).strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.replace('[x]', '').replace('[]', '').replace('[ ]', '')
            cleaned = cleaned.strip()
            
            if not cleaned or len(cleaned) < 3:
                continue
                
            # Skip duplicates
            key = cleaned.lower().replace(' ', '')
            if key not in seen and len(key) > 2:
                seen.add(key)
                clean_topics.append(cleaned)
        
        logging.info(f"Extracted {len(clean_topics)} potential topics from public page")
        
        # Log first few topics for debugging
        if clean_topics:
            logging.info(f"Sample topics: {clean_topics[:5]}")
        
        return clean_topics[:50] if clean_topics else None
        
    except Exception as e:
        logging.error(f"Failed to parse public Notion page: {e}")
        return None