# utils/tuf_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def search_tuf(topic):
    """Search Take U Forward for a topic and return the first relevant article URL"""
    try:
        # Use Google search for better results
        google_query = f"site:takeuforward.org {topic}"
        google_url = f"https://www.google.com/search?q={requests.utils.quote(google_query)}"
        
        response = requests.get(google_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for TUF links in Google search results
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "takeuforward.org" in href and "/url?q=" in href:
                # Extract the actual URL from Google's redirect
                actual_url = href.split("/url?q=")[1].split("&")[0]
                if "takeuforward.org" in actual_url:
                    return actual_url
        
        # Fallback: Direct TUF search
        query_params = {"s": topic}
        search_url = f"https://takeuforward.org/?{urlencode(query_params)}"
        
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for article links
        article_links = soup.find_all("a", href=True)
        for link in article_links:
            href = link.get("href", "")
            if href and "takeuforward.org" in href:
                # Check if the link is relevant to the topic
                link_text = link.get_text().lower()
                if any(keyword in link_text or keyword in href.lower() for keyword in topic.lower().split()):
                    if href.startswith("/"):
                        return urljoin("https://takeuforward.org", href)
                    return href
        
        return None
        
    except Exception as e:
        logging.warning(f"TUF search failed for {topic}: {e}")
        return None

def parse_tuf(url):
    """Parse a Take U Forward article and extract relevant information"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract theory from content
        theory = ""
        
        # Try different content containers
        content_selectors = [
            ".entry-content",
            ".post-content", 
            ".content",
            "article .content",
            ".single-post-content"
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                paragraphs = content_div.find_all("p")[:3]  # First 3 paragraphs
                theory = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if theory:
                    break
        
        # If no theory found, try any paragraph
        if not theory:
            paragraphs = soup.find_all("p")[:3]
            theory = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Extract C++ code
        code = ""
        code_blocks = soup.find_all(["pre", "code"])
        
        for block in code_blocks:
            text = block.get_text()
            # Look for C++ indicators
            if any(indicator in text for indicator in ["#include", "std::", "int main", "using namespace std", "cout", "cin", "vector", "class"]):
                code = text.strip()
                break
        
        # Clean up the extracted data
        if theory:
            theory = theory[:500]  # Limit length
        
        if code:
            code = code[:2000]  # Limit code length
        
        return {
            "theory": theory,
            "code": code,
            "link": url
        }
        
    except Exception as e:
        logging.warning(f"Failed to parse TUF page {url}: {e}")
        return {
            "theory": "",
            "code": "",
            "link": url
        }