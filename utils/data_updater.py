# utils/data_updater.py
import os
import json
import random
import logging
from pathlib import Path
from .notion_client import get_topics_from_notion_api, get_topics_from_public_page
from .gfg_scraper import search_gfg, parse_gfg
from .tuf_scraper import search_tuf, parse_tuf

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DSA_FILE = DATA_DIR / "dsa_topics.json"
RES_FILE = DATA_DIR / "resources.json"

NOTION_PUBLIC_URL = "https://www.notion.so/List-of-important-topics-for-DSA-227e396a4f53806da717c4d2134f37e2?source=copy_link"

# Default DSA topics if scraping fails
DEFAULT_DSA_TOPICS = [
    "Arrays", "Linked Lists", "Stacks", "Queues", "Binary Search", "Linear Search",
    "Bubble Sort", "Selection Sort", "Insertion Sort", "Merge Sort", "Quick Sort", "Heap Sort",
    "Binary Trees", "Binary Search Trees", "AVL Trees", "Red-Black Trees", "Heaps",
    "Hash Tables", "Graphs", "DFS", "BFS", "Dijkstra", "Bellman Ford", "Floyd Warshall",
    "Dynamic Programming", "Greedy Algorithms", "Backtracking", "Divide and Conquer",
    "Two Pointers", "Sliding Window", "Fast and Slow Pointers", "Merge Intervals",
    "Cyclic Sort", "Tree DFS", "Tree BFS", "Graph DFS", "Graph BFS", "Trie",
    "Union Find", "Topological Sort", "Minimum Spanning Tree", "Shortest Path"
]

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

    # Try GFG first
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

    # Add YouTube search link as fallback resource
    yt_query = topic.replace(" ", "+")
    result["links"].append(("YouTube Search", f"https://www.youtube.com/results?search_query={yt_query}+algorithm+tutorial"))
    
    # Add LeetCode search
    lc_query = topic.replace(" ", "-").lower()
    result["links"].append(("LeetCode Problems", f"https://leetcode.com/tag/{lc_query}/"))

    return result

def update_all_data():
    """Update all data sources and create JSON files"""
    logging.info("Starting data update process...")
    
    # Try to get topics from Notion
    topics = []
    try:
        topics = get_topics_from_notion_api()
        if topics:
            logging.info(f"Got {len(topics)} topics from Notion API")
        else:
            topics = get_topics_from_public_page(NOTION_PUBLIC_URL)
            if topics:
                logging.info(f"Got {len(topics)} topics from public Notion page")
    except Exception as e:
        logging.error(f"Failed to get topics from Notion: {e}")
    
    # Fallback to default topics if Notion scraping fails
    if not topics:
        logging.info("Using default DSA topics as fallback")
        topics = DEFAULT_DSA_TOPICS

    # Clean and deduplicate topics
    clean_topics = []
    seen = set()
    
    for topic in topics:
        if not topic:
            continue
        
        # Clean the topic string
        topic = topic.strip()
        topic = topic.replace("[x]", "").replace("[]", "").replace("[ ]", "")
        topic = topic.replace("(", "").replace(")", "")
        topic = topic.strip()
        
        # Skip very long or very short topics
        if len(topic) < 2 or len(topic) > 50:
            continue
            
        # Skip numbers and section headers
        if topic.isdigit() or topic.startswith(tuple("0123456789")):
            continue
            
        # Deduplicate
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
            
            dsa_db[key] = {
                "title": enriched.get("title", topic),
                "short": enriched.get("short", ""),
                "time": enriched.get("time", ""),
                "space": enriched.get("space", ""),
                "code": enriched.get("code", ""),
                "links": enriched.get("links", [])
            }
            
            res_db[key] = enriched.get("links", [])
            
        except Exception as e:
            logging.error(f"Failed to process topic {topic}: {e}")
            # Add basic entry even if enrichment fails
            key = topic.lower().replace(" ", "")
            dsa_db[key] = {
                "title": topic,
                "short": f"Learn about {topic} algorithm and data structure.",
                "time": "N/A",
                "space": "N/A", 
                "code": "",
                "links": [("YouTube Search", f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+algorithm")]
            }
            res_db[key] = dsa_db[key]["links"]

    # Write files with error handling
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

# LeetCode fetch (improved with better error handling)
import requests

def get_random_leetcode_problem(limit=50):
    """Fetch a random LeetCode problem"""
    try:
        # Updated GraphQL query for LeetCode API
        query = """
        query problemsetQuestionList($limit: Int!, $skip: Int!) {
          problemsetQuestionList: questionList(
            categorySlug: ""
            limit: $limit
            skip: $skip
            filters: {}
          ) {
            questions: data {
              acRate
              difficulty
              freqBar
              frontendQuestionId: questionFrontendId
              isFavor
              paidOnly: isPaidOnly
              status
              title
              titleSlug
              topicTags {
                name
                id
                slug
              }
            }
          }
        }
        """
        
        variables = {
            "limit": limit,
            "skip": random.randint(0, 2000)  # Random offset
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.post(
            "https://leetcode.com/graphql/", 
            json=payload, 
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            logging.error(f"LeetCode API returned status {response.status_code}")
            return None
            
        data = response.json()
        
        # Navigate the response structure safely
        questions = []
        if "data" in data and data["data"]:
            problem_list = data["data"].get("problemsetQuestionList")
            if problem_list and "questions" in problem_list:
                questions = problem_list["questions"]
        
        if not questions:
            logging.error("No questions found in LeetCode response")
            return None
            
        # Filter out paid problems
        free_questions = [q for q in questions if not q.get("paidOnly", True)]
        
        if not free_questions:
            free_questions = questions  # Fallback to all questions
            
        question = random.choice(free_questions)
        
        return {
            "title": question.get("title", "Unknown Problem"),
            "difficulty": question.get("difficulty", "Unknown"),
            "url": f"https://leetcode.com/problems/{question.get('titleSlug', '')}/"
        }
        
    except requests.RequestException as e:
        logging.error(f"Network error fetching LeetCode problem: {e}")
        return None
    except Exception as e:
        logging.error(f"Error fetching LeetCode problem: {e}")
        return None