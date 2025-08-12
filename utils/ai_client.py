# utils/ai_client.py
import os
import requests
import logging
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_AI_API_KEY")

# --- CORRECTED: Updated to the stable v1 API endpoint ---
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

HEADERS = {
    "Content-Type": "application/json"
}

def generate_dsa_info(topic):
    """
    Uses the AI model to generate a full breakdown of a DSA topic.
    """
    if not API_KEY:
        logging.error("GOOGLE_AI_API_KEY is not set. Please check your .env file.")
        return None

    # The prompt is well-engineered and does not need to be changed.
    prompt = f"""
    As an expert computer science professor, provide a detailed and accurate guide on the data structure or algorithm: "{topic}".

    Your response MUST be a single, valid JSON object. Do not include any text or markdown formatting before or after the JSON object.

    The JSON object must have the following structure:
    {{
      "title": "The official name of the topic",
      "short_description": "A concise, one-paragraph explanation of what it is, how it works, and its primary use case. Should be around 3-4 sentences.",
      "time_complexity": "Provide the Big O notation for average, best, and worst cases for major operations (e.g., Access, Search, Insertion, Deletion). Format as a simple string.",
      "space_complexity": "Provide the Big O notation for the space complexity. Format as a simple string.",
      "cpp_code": "A clean, well-commented, and complete C++ implementation of the algorithm or data structure. The code must be fully functional and demonstrate a common use case. Do not include any explanation outside of the code comments.",
      "resource_links": [
        {{
          "name": "GeeksforGeeks Article",
          "url": "A direct URL to the most relevant GeeksforGeeks article for this topic."
        }},
        {{
          "name": "YouTube Tutorial",
          "url": "A direct URL to a high-quality, popular YouTube video tutorial explaining this topic."
        }},
        {{
          "name": "LeetCode Problems",
          "url": "A direct URL to the LeetCode tag page for this topic (e.g., https://leetcode.com/tag/binary-search/)."
        }}
      ]
    }}

    Ensure all information, especially the code and complexities, is correct and follows best practices. The C++ code should be self-contained and ready to compile.
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, timeout=60) # Increased timeout for AI generation
        response.raise_for_status()
        
        response_data = response.json()
        json_string = response_data['candidates'][0]['content']['parts'][0]['text']
        cleaned_json = json_string.strip().replace("```json", "").replace("```", "").strip()
        
        return json.loads(cleaned_json)

    except requests.RequestException as e:
        logging.error(f"AI API request failed for topic {topic}: {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error(f"Failed to parse AI response for topic {topic}: {e}")
        logging.error(f"Raw response was: {response.text}")
        return None