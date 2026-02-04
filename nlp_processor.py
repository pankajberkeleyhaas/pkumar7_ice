import csv
import json
import requests
import time
import os
import urllib3
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
API_URL = "https://llama3-inference.uat.glacio.intcx.net/v1/chat/completions"

SYSTEM_PROMPT = """You are a multilingual NLP expert. Analyze the provided text and return ONLY a JSON object with the following structure:
{
  "sentiment": "positive/negative/neutral",
  "probabilities": {
    "positive": 0.0-1.0,
    "negative": 0.0-1.0,
    "neutral": 0.0-1.0
  },
  "summary": "string",
  "entities": [{"text": "string", "label": "string"}],
  "rewording": "string",
  "urls": ["string"],
  "topics": ["string"]
}

Instructions:
1. Sentiment: Determine the overall tone.
2. Probabilities: Provide numerical confidence scores for positive, negative, and neutral sentiments. These should ideally sum to 1.0.
3. Summary: Provide a comprehensive 2-3 sentence summary of the text.
4. Entities: Extract named entities (People, Organizations, Locations, Products, Dates). Provide both the text and its label.
5. Rewording: Provide a concise, clear rephrasing of the main point.
6. URLs: Extract all raw URLs found in the text.
7. Topics: Identify the main themes or categories being discussed."""

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_requests_session():
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

def extract_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = text[start:end]
            return json.loads(json_str)
        return None
    except Exception:
        return None

def analyze_content(session, text):
    if not text or not str(text).strip():
        return {"sentiment": "neutral", "probabilities": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}, "summary": "N/A", "entities": [], "rewording": "Empty text", "urls": [], "topics": []}

    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this text: \"{text}\""}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        response = session.post(API_URL, json=payload, verify=False, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        result = extract_json(content)
        if result:
            # Flatten entities for easier CSV output if needed
            entities_str = "; ".join([f"{e['text']} ({e.get('label', 'N/A')})" for e in result.get("entities", [])])
            result["entities_flat"] = entities_str
            result["topics_flat"] = "; ".join(result.get("topics", []))
            result["urls_flat"] = "; ".join(result.get("urls", []))
            return result
        else:
            return {"sentiment": "error", "probabilities": {"positive": 0.0, "negative": 0.0, "neutral": 0.0}, "summary": "Error", "entities_flat": "Error", "rewording": "Parsing Error", "urls_flat": "", "topics_flat": ""}
            
    except Exception as e:
        return {"sentiment": "error", "probabilities": {"positive": 0.0, "negative": 0.0, "neutral": 0.0}, "summary": "Error", "entities_flat": "Error", "rewording": f"API Error: {str(e)}", "urls_flat": "", "topics_flat": ""}

def process_analysis(input_file, output_file, limit=None):
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    session = setup_requests_session()
    
    data_to_process = []
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        col_name = next((c for c in reader.fieldnames if c.lower() == 'comments'), reader.fieldnames[0])
        for row in reader:
            data_to_process.append(row[col_name])

    if limit:
        data_to_process = data_to_process[:limit]

    print(f"Processing {len(data_to_process)} entries...")
    
    results = []
    for i, content in enumerate(data_to_process):
        print(f"[{i+1}/{len(data_to_process)}] Analyzing...")
        analysis = analyze_content(session, content)
        
        probs = analysis.get("probabilities", {})
        results.append({
            "Original_Text": content,
            "Sentiment": analysis.get("sentiment"),
            "Prob_Positive": probs.get("positive"),
            "Prob_Negative": probs.get("negative"),
            "Prob_Neutral": probs.get("neutral"),
            "Summary": analysis.get("summary"),
            "Rewording": analysis.get("rewording"),
            "Entities": analysis.get("entities_flat"),
            "Topics": analysis.get("topics_flat"),
            "URLs": analysis.get("urls_flat")
        })
        time.sleep(0.1)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["Original_Text", "Sentiment", "Prob_Positive", "Prob_Negative", "Prob_Neutral", "Summary", "Rewording", "Entities", "Topics", "URLs"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Extraction complete! Results saved to {output_file}")

if __name__ == "__main__":
    import sys
    # Example usage: python script.py input.csv output.csv [limit]
    inp = sys.argv[1] if len(sys.argv) > 1 else "nlp_test_input.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "nlp_analysis_results.csv"
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    process_analysis(inp, out, lim)
