# utils/tuf_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def search_tuf(topic):
    # Using Google search is more effective for TUF
    try:
        google_query = f"site:takeuforward.org {topic}"
        google_url = f"https://www.google.com/search?q={requests.utils.quote(google_query)}"
        
        response = requests.get(google_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "takeuforward.org/data-structure" in href and "/url?q=" in href:
                actual_url = href.split("/url?q=")[1].split("&")[0]
                return actual_url
        return None
    except Exception as e:
        logging.warning(f"TUF search failed for {topic}: {e}")
        return None

def parse_tuf(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract theory from content
        theory = ""
        content_div = soup.select_one(".entry-content")
        if content_div:
            paragraphs = content_div.find_all("p", limit=3)
            theory = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # --- MODIFIED C++ CODE EXTRACTION ---
        code = ""
        # TUF often labels its code blocks clearly.
        cpp_heading = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and 'C++' in tag.get_text())
        
        if cpp_heading:
            code_block = cpp_heading.find_next("pre")
            if code_block:
                code = code_block.get_text().strip()
                
        # Fallback to finding the first C++-like code block
        if not code:
            code_blocks = soup.find_all("pre")
            for block in code_blocks:
                text = block.get_text()
                if "#include" in text or "std::" in text or "int main" in text:
                    code = text.strip()
                    break
        
        return {
            "theory": theory[:800],
            "code": code[:1500],
            "link": url
        }
    except Exception as e:
        logging.warning(f"Failed to parse TUF page {url}: {e}")
        return {"theory": "", "code": "", "link": url}