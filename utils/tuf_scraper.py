# utils/tuf_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DSA-Master-Bot/1.0)"}

def search_tuf(topic):
    q = {"s": topic}
    url = f"https://takeuforward.org/?{urlencode(q)}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    a = soup.select_one("h2.entry-title a[href]") or soup.select_one("a[href*='takeuforward.org']")
    if a:
        return a["href"]
    return None

def parse_tuf(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    p = soup.select_one(".entry-content p")
    theory = p.get_text().strip() if p else ""

    # search for cpp snippet
    code = ""
    for pre in soup.find_all(["pre","code"]):
        txt = pre.get_text()
        if "#include" in txt or "int main" in txt or "std::" in txt:
            code = txt.strip()
            break
    return {"theory": theory, "code": code, "link": url}
