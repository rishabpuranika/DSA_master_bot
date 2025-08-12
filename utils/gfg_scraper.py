# utils/gfg_scraper.py
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DSA-Master-Bot/1.0)"}

def search_gfg(topic):
    # GFG has a search query parameter '?s=...'
    q = {"s": topic}
    url = f"https://www.geeksforgeeks.org/?{urlencode(q)}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Find the first result link in an article card
    first_result = soup.select_one("div.g-col-sm-6 a[href*='geeksforgeeks.org/']")
    if first_result and first_result.has_attr("href"):
        return first_result["href"]
    
    # Fallback to the old method if the new one fails
    a = soup.select_one("a[href*='/'] .entry-title") or soup.select_one("a[href*='/']")
    if a:
        anchor = a.find_parent("a")
        if anchor and anchor.has_attr("href"):
            return anchor["href"]
    return None

def parse_gfg(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Short theory: first paragraph under article
    p = soup.select_one("article .content > p")
    theory = p.get_text().strip() if p else ""

    # Complexities: look for text mentioning 'Time Complexity' or 'Complexity'
    time = "N/A"
    space = "N/A"
    text = soup.get_text()
    m_time = re.search(r"(Time Complexity[:\s]*[^\n\r]+)", text, re.IGNORECASE)
    m_space = re.search(r"(Space Complexity[:\s]*[^\n\r]+)", text, re.IGNORECASE)
    if m_time:
        time = m_time.group(1).split(":", 1)[-1].strip()
    if m_space:
        space = m_space.group(1).split(":", 1)[-1].strip()

    # --- MODIFIED C++ CODE EXTRACTION ---
    # Look for a heading that says "C++" and get the next code block
    code = ""
    cpp_heading = soup.find(lambda tag: tag.name in ['h2', 'h3', 'strong'] and 'C++' in tag.get_text())
    
    if cpp_heading:
        code_block = cpp_heading.find_next("pre")
        if code_block:
            code = code_block.get_text().strip()

    # Fallback: if no C++ heading is found, use the old method
    if not code:
        for pre in soup.find_all("pre"):
            txt = pre.get_text()
            if "#include" in txt or "int main" in txt or "using namespace std" in txt:
                code = txt.strip()
                break

    return {"theory": theory, "time": time, "space": space, "code": code, "link": url}