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
    # Find the first result link
    a = soup.select_one("a[href*='/'] .entry-title") or soup.select_one("a[href*='/']")
    link = None
    if a:
        parent = a
        # try to climb to anchor
        anchor = a.find_parent("a")
        if anchor and anchor.has_attr("href"):
            link = anchor["href"]
    # fallback: look for first article card
    if not link:
        first = soup.select_one("article a[href]")
        if first:
            link = first["href"]
    return link

def parse_gfg(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # short theory: first paragraph under article
    p = soup.select_one("article p")
    theory = p.get_text().strip() if p else ""

    # complexities: look for text mentioning 'Time Complexity' or 'Complexity'
    time = "N/A"
    space = "N/A"
    text = soup.get_text()
    m_time = re.search(r"(Time Complexity[:\s]*[^\n\r]+)", text, re.IGNORECASE)
    m_space = re.search(r"(Space Complexity[:\s]*[^\n\r]+)", text, re.IGNORECASE)
    if m_time:
        time = m_time.group(1).split(":",1)[-1].strip()
    if m_space:
        space = m_space.group(1).split(":",1)[-1].strip()

    # code: look for first <pre> or code block that looks like c++
    code = ""
    for pre in soup.find_all(["pre","code"]):
        txt = pre.get_text()
        if "#include" in txt or "std::" in txt or "int main" in txt or "using namespace std" in txt:
            code = txt.strip()
            break

    return {"theory": theory, "time": time, "space": space, "code": code, "link": url}
