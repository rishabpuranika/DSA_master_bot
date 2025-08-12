# utils/notion_client.py
import os
import requests
from bs4 import BeautifulSoup

NOTION_TOKEN = os.getenv("NOTION_TOKEN")  # if provided
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # optional

HEADERS = {"User-Agent": "DSA-Master-Bot/1.0 (+https://github.com/)"}

def get_topics_from_notion_api():
    """Preferred: use Notion API (requires integration token and DB id)"""
    token = NOTION_TOKEN
    dbid = NOTION_DATABASE_ID
    if not token or not dbid:
        return None

    url = f"https://api.notion.com/v1/databases/{dbid}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    res = requests.post(url, headers=headers, json={})
    res.raise_for_status()
    j = res.json()
    topics = []
    for r in j.get("results", []):
        props = r.get("properties", {})
        # You might need to adapt this block to your Notion DB schema.
        # Try common property names 'Name' or 'Topic'
        name = None
        if "Name" in props and props["Name"].get("title"):
            name = "".join([t.get("plain_text", "") for t in props["Name"]["title"]])
        elif "Topic" in props and props["Topic"].get("title"):
            name = "".join([t.get("plain_text", "") for t in props["Topic"]["title"]])
        if name:
            topics.append(name.strip())
    return topics

def get_topics_from_public_page(notion_public_url):
    """Fallback: parse a public Notion page and extract likely topic lines"""
    res = requests.get(notion_public_url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    candidates = []
    # find list items and headings
    for tag in soup.find_all(["h1","h2","h3","h4","li","p"]):
        text = tag.get_text().strip()
        if not text:
            continue
        if len(text) < 60 and len(text.split()) <= 6:
            candidates.append(text)
    # dedupe + heuristics
    seen = []
    for c in candidates:
        s = c.strip()
        if s and s.lower() not in seen:
            seen.append(s.lower())
    return [s for s in seen]
