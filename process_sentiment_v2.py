import csv
import json
import requests
import time
import os
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
API_URL = "https://llama3-inference.uat.glacio.intcx.net/v1/chat/completions"
SYSTEM_PROMPT = "You are a sentiment analysis expert. Analyze the sentiment and return ONLY a JSON object with format: {\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0, \"reason\": \"brief explanation\"}"

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_requests_session():
    """Sets up a requests session with retries for better resilience."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def clean_comment(comment):
    """Handles basic cleaning and edge cases for input text."""
    if not comment or not isinstance(comment, str):
        return ""
    
    cleaned = comment.strip()
    
    # Truncate extremely long comments to avoid token limit issues (approx 4k chars)
    if len(cleaned) > 4000:
        cleaned = cleaned[:4000] + "..."
        
    return cleaned

def extract_json(text):
    """Robustly extracts JSON from potentially conversational model output."""
    try:
        # Find the first '{' and last '}'
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = text[start:end]
            # Remove potential markdown formatting inside the matches
            json_str = json_str.replace("```json", "").replace("```", "").strip()
            return json.loads(json_str)
        return None
    except Exception:
        return None

def analyze_sentiment(session, comment):
    """Sends a single comment to the API with error handling."""
    comment = clean_comment(comment)
    
    if not comment:
        return {"sentiment": "skipped", "score": 0.0, "reason": "Empty or invalid comment content"}

    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze: \"{comment}\""}
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = session.post(API_URL, json=payload, verify=False, timeout=45)
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        result = extract_json(content)
        if result:
            return result
        else:
            return {
                "sentiment": "error", 
                "score": 0.0, 
                "reason": f"Failed to parse JSON from model output: {content[:100]}..."
            }
            
    except requests.exceptions.RequestException as e:
        return {"sentiment": "error", "score": 0.0, "reason": f"API Request failed: {str(e)}"}
    except Exception as e:
        return {"sentiment": "error", "score": 0.0, "reason": f"Unexpected error: {str(e)}"}

def process_csv(input_file, output_file, limit=None):
    """Processes the CSV file and saves results."""
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    session = setup_requests_session()
    
    comments_to_process = []
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            # Handle both comma and semicolon if needed, but stick to standard CSV initially
            reader = csv.DictReader(f)
            # Find the comment column (case-insensitive check)
            col_name = next((c for c in reader.fieldnames if c.lower() == 'comments'), None)
            
            if not col_name:
                print(f"Error: Could not find 'Comments' column in {input_file}. Available: {reader.fieldnames}")
                return

            for row in reader:
                comments_to_process.append(row[col_name])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if limit:
        comments_to_process = comments_to_process[:limit]

    print(f"Processing {len(comments_to_process)} comments from {input_file}...")
    
    results = []
    for i, comment in enumerate(comments_to_process):
        print(f"[{i+1}/{len(comments_to_process)}] Analyzing...")
        sentiment = analyze_sentiment(session, comment)
        
        results.append({
            "original_comment": comment,
            "sentiment": sentiment.get("sentiment"),
            "score": sentiment.get("score"),
            "reason": sentiment.get("reason")
        })
        time.sleep(0.1)  # Minimal delay

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["original_comment", "sentiment", "score", "reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Done! Results saved to {output_file}")

if __name__ == "__main__":
    # Standard run behavior
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        process_csv("edge_case_test.csv", "edge_case_results.csv")
    else:
        process_csv("AICOE_api_endpoint.csv", "sentiment_results.csv", limit=5)
