# utils/data_updater.py
import os
import json
import random
import logging
import re
import time
from pathlib import Path
from .notion_client import get_topics_from_public_page
from .ai_client import generate_dsa_info # <-- IMPORT THE NEW AI CLIENT

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DSA_FILE = DATA_DIR / "dsa_topics.json"
RES_FILE = DATA_DIR / "resources.json"

NOTION_PUBLIC_URL = "https://www.notion.so/List-of-important-topics-for-DSA-227e396a4f53806da717c4d2134f37e2?source=copy_link"

DEFAULT_DSA_TOPICS = [
    "Arrays", "Linked Lists", "Stacks", "Queues", "Binary Search", "Merge Sort", "Heaps", "Graphs", "Dynamic Programming"
]

def update_all_data():
    """
    Updates all data sources by calling the AI model for each topic
    and then creates the JSON files for the bot.
    """
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

    # Clean the topics extracted from Notion
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
            # Generate all data for the topic using the AI
            ai_data = generate_dsa_info(topic)
            
            if ai_data:
                key = topic.lower().replace(" ", "-")
                # Populate the database for the !dsa command
                dsa_db[key] = {
                    "title": ai_data.get("title", topic.title()),
                    "short": ai_data.get("short_description", ""),
                    "time": ai_data.get("time_complexity", "N/A"),
                    "space": ai_data.get("space_complexity", "N/A"),
                    "code": ai_data.get("cpp_code", ""),
                    "links": [(link["name"], link["url"]) for link in ai_data.get("resource_links", [])]
                }
                # Populate the resources for the !resources command
                res_db[key] = [(link["name"], link["url"]) for link in ai_data.get("resource_links", [])]
                logging.info(f"Successfully generated data for {topic}")
            else:
                logging.warning(f"Could not generate AI data for topic: {topic}")

            # Add a polite delay to respect API rate limits
            logging.info("Waiting for 8 seconds before the next topic...")
            time.sleep(8)
            
        except Exception as e:
            logging.error(f"An error occurred while processing topic {topic}: {e}")

    # Write the collected data to files
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

def get_random_leetcode_problem(limit=50):
    """Fetch a random LeetCode problem"""
    # This function remains the same.
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