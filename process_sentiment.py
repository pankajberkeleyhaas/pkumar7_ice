import csv
import json
import requests
import time
import os

# Configuration
INPUT_FILE = "AICOE_api_endpoint.csv"
OUTPUT_FILE = "sentiment_results.csv"
API_URL = "https://llama3-inference.uat.glacio.intcx.net/v1/chat/completions"
SYSTEM_PROMPT = "You are a sentiment analysis expert. Analyze the sentiment and return ONLY a JSON object with format: {\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0, \"reason\": \"brief explanation\"}"

def analyze_sentiment(comment):
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze: \"{comment}\""}
        ],
        "temperature": 0.1,
        "max_tokens": 150
    }
    
    try:
        # Using verify=False as per --insecure in curl command
        response = requests.post(API_URL, json=payload, verify=False, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the content from the assistant's message
        content = data['choices'][0]['message']['content'].strip()
        
        # Find the actual JSON object within the string (handles conversational prefixes)
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
        else:
            raise ValueError(f"No JSON object found in response: {content}")
            
    except Exception as e:
        print(f"Error analyzing comment: {e}")
        return {"sentiment": "error", "score": 0.0, "reason": str(e)}

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"File {INPUT_FILE} not found.")
        return

    # Disable insecure request warnings for the local endpoint
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    comments = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Comments'].strip():
                comments.append(row['Comments'].strip())

    print(f"Found {len(comments)} comments. Processing sample of 5...")
    comments = comments[:5]

    results = []
    for i, comment in enumerate(comments):
        print(f"[{i+1}/{len(comments)}] Analyzing: {comment[:50]}...")
        sentiment = analyze_sentiment(comment)
        results.append({
            "comment": comment,
            "sentiment": sentiment.get("sentiment"),
            "score": sentiment.get("score"),
            "reason": sentiment.get("reason")
        })
        # Small delay to be polite to the endpoint if needed
        time.sleep(0.1)

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["comment", "sentiment", "score", "reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Analysis complete! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
