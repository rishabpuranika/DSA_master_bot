# utils/cp_algorithms_scraper.py
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def search_cp_algorithms(topic):
    try:
        query = f"site:cp-algorithms.com {topic}"
        google_url = f"https://www.google.com/search?q={quote(query)}"
        
        response = requests.get(google_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "cp-algorithms.com" in href and "/url?q=" in href:
                actual_url = href.split("/url?q=")[1].split("&")[0]
                if actual_url.startswith("https://cp-algorithms.com/") and actual_url.endswith(".html"):
                    return actual_url
        return None
    except Exception as e:
        logging.warning(f"CP-Algorithms search failed for {topic}: {e}")
        return None

def parse_cp_algorithms(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        article = soup.find("article")
        if not article:
            return {"theory": "", "code": ""}
            
        paragraphs = article.find_all("p", limit=3)
        theory = " ".join(p.get_text().strip() for p in paragraphs)
        
        # --- C++ CODE EXTRACTION (already robust for this site) ---
        # CP-Algorithms primarily uses C++, so finding the first <pre> block is reliable.
        code_block = article.find("pre")
        code = ""
        if code_block:
            # Verify it looks like C++
            text = code_block.get_text()
            if "#include" in text or "using namespace" in text:
                code = text.strip()
        
        return {
            "theory": theory[:800],
            "code": code[:1500]
        }
    except Exception as e:
        logging.warning(f"Failed to parse CP-Algorithms page {url}: {e}")
        return {"theory": "", "code": ""}