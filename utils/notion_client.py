# utils/notion_client.py
import os
import requests
from bs4 import BeautifulSoup
import logging
import re

NOTION_TOKEN = os.getenv("NOTION_TOKEN")  # if provided
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_topics_from_notion_api():
    """Preferred: use Notion API (requires integration token and DB id)"""
    token = NOTION_TOKEN
    dbid = NOTION_DATABASE_ID
    
    if not token or not dbid:
        logging.info("No Notion API credentials provided, skipping API method")
        return None

    try:
        url = f"https://api.notion.com/v1/databases/{dbid}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={}, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        topics = []
        
        for result in data.get("results", []):
            properties = result.get("properties", {})
            
            # Try different common property names
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
            
            if name:
                topics.append(name.strip())
        
        logging.info(f"Retrieved {len(topics)} topics from Notion API")
        return topics if topics else None
        
    except Exception as e:
        logging.error(f"Notion API request failed: {e}")
        return None

def get_topics_from_public_page(notion_public_url):
    """Fallback: parse a public Notion page and extract likely topic lines"""
    try:
        logging.info(f"Attempting to parse public Notion page: {notion_public_url}")
        
        response = requests.get(notion_public_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        candidates = []
        
        # Look for various text containers that might contain topics
        selectors = [
            "div[data-block-id]",  # Notion blocks
            ".notion-page-content div",
            "[role='textbox']",
            "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                
                # Skip empty or very long text
                if not text or len(text) > 100:
                    continue
                
                # Skip common page elements
                if any(skip_phrase in text.lower() for skip_phrase in [
                    "notion", "page", "untitled", "created", "edited", "share",
                    "duplicate", "follow", "subscribe", "comment"
                ]):
                    continue
                
                # Look for DSA-like topics
                if any(keyword in text.lower() for keyword in [
                    "array", "list", "tree", "graph", "sort", "search", "hash", 
                    "stack", "queue", "heap", "algorithm", "dynamic", "greedy",
                    "binary", "linear", "dfs", "bfs", "dp", "backtrack"
                ]):
                    candidates.append(text)
                elif len(text.split()) <= 5 and len(text) >= 5:  # Short phrases
                    candidates.append(text)
        
        # Clean and deduplicate
        seen = set()
        clean_topics = []
        
        for candidate in candidates:
            # Clean the text
            cleaned = re.sub(r'[^\w\s\(\)\[\]/-]', '', candidate).strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
            
            if not cleaned or len(cleaned) < 3:
                continue
                
            # Skip duplicates
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                clean_topics.append(cleaned)
        
        logging.info(f"Extracted {len(clean_topics)} potential topics from public page")
        
        # Return the most promising candidates
        return clean_topics[:50] if clean_topics else None
        
    except Exception as e:
        logging.error(f"Failed to parse public Notion page: {e}")
        return None