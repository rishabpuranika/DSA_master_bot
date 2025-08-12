# utils/data_updater.py
import os
import json
import random
from pathlib import Path
from .notion_client import get_topics_from_notion_api, get_topics_from_public_page
from .gfg_scraper import search_gfg, parse_gfg
from .tuf_scraper import search_tuf, parse_tuf

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DSA_FILE = DATA_DIR / "dsa_topics.json"
RES_FILE = DATA_DIR / "resources.json"

NOTION_PUBLIC_URL = "https://www.notion.so/List-of-important-topics-for-DSA-227e396a4f53806da717c4d2134f37e2?source=copy_link"  # replace if needed

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

    # Try GFG
    try:
        gfg_link = search_gfg(topic)
        if gfg_link:
            gfg = parse_gfg(gfg_link)
            # fill blanks
            result["short"] = result["short"] or gfg.get("theory","")
            result["time"] = result["time"] or gfg.get("time","")
            result["space"] = result["space"] or gfg.get("space","")
            result["code"] = result["code"] or gfg.get("code","")
            result["links"].append(("GeeksforGeeks", gfg_link))
    except Exception:
        pass

    # Try Take U Forward
    try:
        tuf_link = search_tuf(topic)
        if tuf_link:
            tuf = parse_tuf(tuf_link)
            result["short"] = result["short"] or tuf.get("theory","")
            result["code"] = result["code"] or tuf.get("code","")
            result["links"].append(("Take U Forward", tuf_link))
    except Exception:
        pass

    # Add YouTube search link as fallback resource
    yt_q = topic.replace(" ", "+")
    result["links"].append(("YouTube - Search", f"https://www.youtube.com/results?search_query={yt_q}"))
    return result

def update_all_data():
    # get topics from Notion API preferred, else public page
    topics = get_topics_from_notion_api()
    if not topics:
        topics = get_topics_from_public_page(NOTION_PUBLIC_URL)
    # further sanitize: keep short ones and remove extra headings
    clean = []
    for t in topics:
        if not t: continue
        t = t.strip()
        if len(t) < 120:
            clean.append(t)
    clean = list(dict.fromkeys(clean))  # dedupe, keep order

    dsa_db = {}
    res_db = {}
    for topic in clean:
        key = topic.lower().replace(" ", "")
        enriched = enrich_topic(topic)
        dsa_db[key] = {
            "title": enriched.get("title", topic),
            "short": enriched.get("short", ""),
            "time": enriched.get("time", ""),
            "space": enriched.get("space", ""),
            "code": enriched.get("code",""),
            "links": enriched.get("links", [])
        }
        res_db[key] = enriched.get("links", [])

    # write files
    with open(DSA_FILE, "w") as f:
        json.dump(dsa_db, f, indent=2)

    with open(RES_FILE, "w") as f:
        json.dump(res_db, f, indent=2)

    return True

# LeetCode fetch (simple, synchronous)
import requests
def get_random_leetcode_problem(limit=50):
    try:
        query = """
        query problemsetQuestionList($limit: Int, $skip: Int) {
          problemsetQuestionList: questionList: problemsetQuestionList(limit: $limit, skip: $skip, categorySlug: "") {
            questions {
              title
              difficulty
              titleSlug
            }
          }
        }
        """
        payload = {"query": query, "variables": {"limit": limit, "skip": 0}}
        res = requests.post("https://leetcode.com/graphql", json=payload, timeout=15)
        j = res.json()
        # fallback path navigation; API shape can change — guard it
        questions = []
        # try multiple keys
        if "data" in j:
            # find any list of dicts that include titleSlug
            def extract_questions(obj):
                if isinstance(obj, dict):
                    for k,v in obj.items():
                        if isinstance(v, list):
                            if v and isinstance(v[0], dict) and "titleSlug" in v[0]:
                                return v
                            for item in v:
                                res = extract_questions(item)
                                if res:
                                    return res
                        else:
                            res = extract_questions(v)
                            if res:
                                return res
                return None
            questions = extract_questions(j["data"]) or []
        if not questions:
            return None
        q = random.choice(questions)
        return {"title": q.get("title"), "difficulty": q.get("difficulty"), "url": f"https://leetcode.com/problems/{q.get('titleSlug')}/"}
    except Exception:
        return None
