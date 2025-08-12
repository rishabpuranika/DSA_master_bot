# utils/data_updater.py
import os
import json
import random
import logging
import re
import time
import requests # Make sure requests is imported
from pathlib import Path
from .notion_client import get_topics_from_public_page
from .ai_client import generate_dsa_info

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DSA_FILE = DATA_DIR / "dsa_topics.json"
RES_FILE = DATA_DIR / "resources.json"
UPDATE_INTERVAL_HOURS = 24

NOTION_PUBLIC_URL = "https://www.notion.so/List-of-important-topics-for-DSA-227e396a4f53806da717c4d2134f37e2?source=copy_link"

DEFAULT_DSA_TOPICS = [
    "Arrays", "Linked Lists", "Stacks", "Queues", "Binary Search", "Merge Sort", "Heaps", "Graphs", "Dynamic Programming"
]

def should_update():
    """
    Checks if the data files need to be updated.
    Returns True if files don't exist or are older than UPDATE_INTERVAL_HOURS.
    """
    if not DSA_FILE.exists() or not RES_FILE.exists():
        logging.info("Data files not found. Update is required.")
        return True
    
    try:
        last_modified_time = DSA_FILE.stat().st_mtime
        age_seconds = time.time() - last_modified_time
        age_hours = age_seconds / 3600
        
        if age_hours > UPDATE_INTERVAL_HOURS:
            logging.info(f"Data is older than {UPDATE_INTERVAL_HOURS} hours. Update is required.")
            return True
        else:
            logging.info(f"Data is fresh (updated {age_hours:.2f} hours ago). Skipping update.")
            return False
            
    except Exception as e:
        logging.error(f"Could not check file age, forcing update. Error: {e}")
        return True

def update_all_data(force_update=False):
    """
    Updates all data sources by calling the AI model for each topic
    and then creates the JSON files for the bot.
    """
    if not force_update and not should_update():
        return False

    logging.info("Starting AI-powered data update process...")
    
    topics = []
    try:
        topics = get_topics_from_public_page(NOTION_PUBLIC_URL)
        if topics:
            logging.info(f"Got {len(topics)} topics from public Notion page")
    except Exception as e:
        logging.error(f"Failed to get topics from Notion: {e}")
    
    if not topics:
        logging.info("Using default DSA topics as fallback")
        topics = DEFAULT_DSA_TOPICS

    clean_topics = []
    seen = set()
    for topic in topics:
        if not topic: continue
        match = re.match(r"([\w\s-]+)", topic)
        if match:
            clean_topic = match.group(1).strip()
            topic_key = clean_topic.lower().replace(" ", "-")
            if topic_key not in seen and len(topic_key) > 2:
                seen.add(topic_key)
                clean_topics.append(clean_topic)

    logging.info(f"Processing {len(clean_topics)} clean topics: {clean_topics[:5]}")

    dsa_db = {}
    res_db = {}
    
    for i, topic in enumerate(clean_topics):
        logging.info(f"Processing topic {i+1}/{len(clean_topics)}: {topic}")
        try:
            ai_data = generate_dsa_info(topic)
            
            if ai_data:
                key = topic.lower().replace(" ", "-")
                dsa_db[key] = {
                    "title": ai_data.get("title", topic.title()),
                    "short": ai_data.get("short_description", ""),
                    "time": ai_data.get("time_complexity", "N/A"),
                    "space": ai_data.get("space_complexity", "N/A"),
                    "code": ai_data.get("cpp_code", ""),
                    "links": [(link["name"], link["url"]) for link in ai_data.get("resource_links", [])]
                }
                res_db[key] = [(link["name"], link["url"]) for link in ai_data.get("resource_links", [])]
                logging.info(f"Successfully generated data for {topic}")
            else:
                logging.warning(f"Could not generate AI data for topic: {topic}")

            logging.info("Waiting for 8 seconds before the next topic...")
            time.sleep(8)
            
        except Exception as e:
            logging.error(f"An error occurred while processing topic {topic}: {e}")

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

    logging.info("AI-powered data update process completed")
    return True

# --- ADD THIS FUNCTION BACK ---
def get_random_leetcode_problem(limit=50):
    """Fetch a random LeetCode problem"""
    try:
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
              title
              titleSlug
              paidOnly: isPaidOnly
            }
          }
        }
        """
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