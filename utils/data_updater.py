# utils/data_updater.py
import os
import json
import random
import logging
from pathlib import Path
from urllib.parse import quote
from .notion_client import get_topics_from_public_page, get_topics_from_notion_api
from .gfg_scraper import search_gfg, parse_gfg
from .tuf_scraper import search_tuf, parse_tuf
from .cp_algorithms_scraper import search_cp_algorithms, parse_cp_algorithms # <-- IMPORT NEW SCRAPER

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DSA_FILE = DATA_DIR / "dsa_topics.json"
RES_FILE = DATA_DIR / "resources.json"

NOTION_PUBLIC_URL = "https://www.notion.so/List-of-important-topics-for-DSA-227e396a4f53806da717c4d2134f37e2?source=copy_link"

DEFAULT_DSA_TOPICS = [
    "Arrays", "Linked Lists", "Stacks", "Queues", "Binary Search", "Linear Search",
    "Bubble Sort", "Selection Sort", "Insertion Sort", "Merge Sort", "Quick Sort", "Heap Sort",
    "Binary Trees", "Binary Search Trees", "Heaps", "Graphs", "DFS", "BFS",
    "Dynamic Programming", "Greedy Algorithms", "Backtracking"
]

def get_youtube_video_link(topic):
    """
    Uses Google Search to find the most relevant YouTube video link for a topic.
    """
    try:
        from googlesearch import search
    except ImportError:
        logging.warning("googlesearch-python library not found. Skipping Youtube.")
        return None
        
    try:
        query = f"site:youtube.com {topic} data structure algorithm tutorial"
        # Get the first result from the search generator
        search_results = search(query, num=1, stop=1, pause=2)
        first_result = next(search_results, None)
        return first_result
    except Exception as e:
        logging.warning(f"Youtube via Google failed for {topic}: {e}")
        return f"https://www.youtube.com/results?search_query={quote(topic)}+algorithm+tutorial"

def enrich_topic(topic):
    """Try multiple sources, return an aggregated dict."""
    result = {
        "title": topic,
        "short": "",
        "time": "",
        "space": "",
        "code": "",
        "links": []
    }
    
    # --- NEW: CP-Algorithms Integration ---
    try:
        cp_link = search_cp_algorithms(topic)
        if cp_link:
            logging.info(f"Found CP-Algorithms link for {topic}: {cp_link}")
            cp_data = parse_cp_algorithms(cp_link)
            if cp_data:
                result["short"] = result["short"] or cp_data.get("theory", "")
                result["code"] = result["code"] or cp_data.get("code", "")
                result["links"].append(("CP-Algorithms", cp_link))
    except Exception as e:
        logging.warning(f"CP-Algorithms scraping failed for {topic}: {e}")

    # Try GFG
    try:
        gfg_link = search_gfg(topic)
        if gfg_link:
            logging.info(f"Found GFG link for {topic}: {gfg_link}")
            gfg_data = parse_gfg(gfg_link)
            if gfg_data:
                result["short"] = result["short"] or gfg_data.get("theory", "")
                result["time"] = result["time"] or gfg_data.get("time", "")
                result["space"] = result["space"] or gfg_data.get("space", "")
                result["code"] = result["code"] or gfg_data.get("code", "")
                result["links"].append(("GeeksforGeeks", gfg_link))
    except Exception as e:
        logging.warning(f"GFG scraping failed for {topic}: {e}")

    # Try Take U Forward
    try:
        tuf_link = search_tuf(topic)
        if tuf_link:
            logging.info(f"Found TUF link for {topic}: {tuf_link}")
            tuf_data = parse_tuf(tuf_link)
            if tuf_data:
                result["short"] = result["short"] or tuf_data.get("theory", "")
                result["code"] = result["code"] or tuf_data.get("code", "")
                result["links"].append(("Take U Forward", tuf_link))
    except Exception as e:
        logging.warning(f"TUF scraping failed for {topic}: {e}")

    # --- NEW: Improved YouTube Video Search ---
    yt_link = get_youtube_video_link(topic)
    if yt_link:
        result["links"].append(("YouTube Tutorial", yt_link))
    
    # Add LeetCode problems link
    lc_query = topic.replace(" ", "-").lower()
    result["links"].append(("LeetCode Problems", f"https://leetcode.com/tag/{lc_query}/"))

    return result

def update_all_data():
    """Update all data sources and create JSON files"""
    logging.info("Starting data update process...")
    
    topics = []
    try:
        topics = get_topics_from_public_page(NOTION_PUBLIC_URL)
        if topics:
            logging.info(f"Got {len(topics)} topics from public Notion page")
        else:
            logging.info("Public page scraping failed, trying Notion API...")
            topics = get_topics_from_notion_api()
            if topics:
                logging.info(f"Got {len(topics)} topics from Notion API")
    except Exception as e:
        logging.error(f"Failed to get topics from any source: {e}")
    
    if not topics:
        logging.info("Using default DSA topics as fallback")
        topics = DEFAULT_DSA_TOPICS

    # Clean and deduplicate topics (same as before)
    clean_topics = []
    seen = set()
    
    for topic in topics:
        if not topic: continue
        topic = topic.strip().replace("[x]", "").replace("[]", "").replace("[ ]", "").replace("(", "").replace(")", "").strip()
        if len(topic) < 2 or len(topic) > 50 or topic.isdigit() or topic.startswith(tuple("0123456789")): continue
        topic_key = topic.lower().replace(" ", "")
        if topic_key not in seen and len(topic_key) > 2:
            seen.add(topic_key)
            clean_topics.append(topic)

    logging.info(f"Processing {len(clean_topics)} clean topics")

    dsa_db = {}
    res_db = {}
    
    for i, topic in enumerate(clean_topics):
        logging.info(f"Processing topic {i+1}/{len(clean_topics)}: {topic}")
        try:
            key = topic.lower().replace(" ", "").replace("-", "").replace("_", "")
            enriched = enrich_topic(topic)
            dsa_db[key] = enriched
            res_db[key] = enriched.get("links", [])
        except Exception as e:
            logging.error(f"Failed to process topic {topic}: {e}")

    # Write files (same as before)
    try:
        with open(DSA_FILE, "w", encoding='utf-8') as f:
            json.dump(dsa_db, f, indent=2, ensure_ascii=False)
        logging.info(f"Wrote {len(dsa_db)} entries to {DSA_FILE}")
    except Exception as e:
        logging.error(f"Failed to write DSA file: {e}")

    try:
        with open(RES_FILE, "w", encoding='utf-8') as f:
            json.dump(res_db, f, indent=2, ensure_ascii=False)
        logging.info(f"Wrote {len(res_db)} entries to {RES_FILE}")
    except Exception as e:
        logging.error(f"Failed to write resources file: {e}")

    logging.info("Data update process completed")
    return True

# LeetCode fetch function remains the same
def get_random_leetcode_problem(limit=50):
    """Fetch a random LeetCode problem"""
    try:
        query = "..." # GraphQL query is the same
        variables = {"limit": limit, "skip": random.randint(0, 2000)}
        payload = {"query": query, "variables": variables}
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        response = requests.post("https://leetcode.com/graphql/", json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
        if not questions: return None
        free_questions = [q for q in questions if not q.get("paidOnly", True)]
        question = random.choice(free_questions or questions)
        return {
            "title": question.get("title", "Unknown Problem"),
            "difficulty": question.get("difficulty", "Unknown"),
            "url": f"https://leetcode.com/problems/{question.get('titleSlug', '')}/"
        }
    except Exception as e:
        logging.error(f"Error fetching LeetCode problem: {e}")
        return None