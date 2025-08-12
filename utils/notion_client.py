# utils/notion_client.py - NOW WITH RETRIES
import os
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import logging
import re
import json

# ... (format_notion_id function is the same) ...
def format_notion_id(notion_id):
    if not notion_id: return notion_id
    clean_id = notion_id.replace('-', '').replace(' ', '')
    if len(clean_id) != 32: return notion_id
    return f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_topics_from_public_page(notion_public_url):
    """
    Scrapes a public Notion page by mimicking the internal API call it uses
    to load its content. This is more reliable than parsing raw HTML.
    """
    try:
        logging.info(f"Attempting robust scrape of public Notion page: {notion_public_url}")
        
        page_id_match = re.search(r'([a-f0-9]{32})', notion_public_url)
        if not page_id_match:
            page_id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', notion_public_url)
        
        if not page_id_match:
            logging.error("Could not find a valid Notion page ID in the URL.")
            return None

        page_id = page_id_match.group(1).replace('-', '')
        logging.info(f"Extracted page ID: {page_id}")

        api_url = "https://www.notion.so/api/v3/loadPageChunk"
        
        payload = {
            "pageId": format_notion_id(page_id),
            "limit": 100,
            "cursor": {"stack": []},
            "chunkNumber": 0,
            "verticalColumns": False
        }
        
        # --- NEW: Retry Logic ---
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        # --- END: Retry Logic ---

        session.headers.update(HEADERS)
        
        # Increased timeout to 30 seconds
        response = session.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        blocks = data.get("recordMap", {}).get("block", {})
        
        if not blocks:
            logging.error("No content blocks found in the API response.")
            return None
            
        topics = []
        for block_id, block_value in blocks.items():
            if 'properties' in block_value.get('value', {}):
                properties = block_value['value']['properties']
                if 'title' in properties:
                    text_segments = properties['title']
                    full_text = "".join(segment[0] for segment in text_segments if segment)
                    cleaned_text = re.sub(r'^\d+\.\s*', '', full_text).strip()
                    if is_likely_dsa_topic(cleaned_text):
                        topics.append(cleaned_text)

        logging.info(f"Extracted {len(topics)} potential topics using the internal API method.")
        return topics if topics else None
        
    except Exception as e:
        logging.error(f"Failed to parse public Notion page with robust method: {e}", exc_info=True)
        return None

# ... (is_likely_dsa_topic and other unused functions can be removed or left as is) ...
def is_likely_dsa_topic(text):
    if not text or len(text.strip()) < 3 or len(text) > 100:
        return False
    clean_text = re.sub(r'[^\w\s\(\)\[\]/-]', '', text.strip()).lower()
    skip_keywords = ['list of important topics for dsa', 'core foundations', 'basic searching', 'basic sorting', 'complex sorting', 'hashing']
    if clean_text in skip_keywords:
        return False
    if not any(char.isalpha() for char in clean_text):
        return False
    return True