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
    "positive": 0.000-1.000,
    "negative": 0.000-1.000,
    "neutral": 0.000-1.000
  },
  "summary": "string",
  "entities": [
    {
      "text": "string",
      "label": "string",
      "canonical_name": "string",
      "confidence": 0.000-1.000,
      "sentiment": "positive/negative/neutral",
      "probabilities": {
        "positive": 0.000-1.000,
        "negative": 0.000-1.000,
        "neutral": 0.000-1.000
      }
    }
  ],
  "rewording": "string",
  "urls": ["string"],
  "topics": ["string"]
}

Instructions:
1. Sentiment: Determine the primary tone of the overall text.
2. Probabilities: Provide a nuanced numerical distribution (summing to 1.000) for the overall text.
3. Summary: Provide a comprehensive 2-3 sentence summary.
4. Entities: Extract named entities. For each entity, provide:
   - text: The original text from the input.
   - label: The entity type (e.g., Person, Organization, Location).
   - canonical_name: The formal, full real-world name of the entity (e.g., if text is 'musk' and label is 'Person', canonical_name is 'Elon Musk'; if 'google', canonical_name is 'Google Inc.'). Use the context to resolve abbreviations or shortened names.
   - confidence: A numerical confidence score (0.000-1.000).
   - sentiment & probabilities: The sentiment distribution for the entity within the context.
5. Rewording: Provide a concise, clear rephrasing.
6. URLs: Extract all raw URLs.
7. Topics: Identify main themes.

Note: All numerical distributions must sum exactly to 1.000 and use three decimal places."""

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
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = session.post(API_URL, json=payload, verify=False, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Robust JSON cleaning
        result = extract_json(content)
        if not result:
            # Try once more with aggressive cleaning of non-printable characters
            clean_content = "".join(char for char in content if char.isprintable() or char in ['\n', '\r', '\t'])
            result = extract_json(clean_content)

        if result:
            # Flatten entities for easier CSV output if needed
            entities_list = []
            for e in result.get("entities", []):
                text_val = e.get('text', 'N/A')
                label = e.get('label', 'N/A')
                canon = e.get('canonical_name', text_val)
                conf = e.get('confidence', 'N/A')
                sent = e.get('sentiment', 'N/A')
                probs = e.get('probabilities', {})
                p_pos = probs.get('positive', 0.0)
                p_neg = probs.get('negative', 0.0)
                p_neu = probs.get('neutral', 0.0)
                
                entities_list.append(f"{text_val} [{canon}] ({label}, Overall: {sent}, [Pos: {p_pos}, Neg: {p_neg}, Neu: {p_neu}], Conf: {conf})")
            
            result["entities_flat"] = "; ".join(entities_list)
            result["topics_flat"] = "; ".join(result.get("topics", []))
            result["urls_flat"] = "; ".join(result.get("urls", []))
            return result
        else:
            print(f"DEBUG: Parsing failed for response: {content[:200]}...")
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
        # Dynamic column detection
        target_cols = ['body', 'comment', 'comments', 'text', 'content']
        col_name = None
        
        # Check fieldnames case-insensitively
        for target in target_cols:
            found = next((c for c in reader.fieldnames if c.lower() == target), None)
            if found:
                col_name = found
                break
        
        if not col_name:
            col_name = reader.fieldnames[0]
            
        print(f"Using column: '{col_name}'")
        for row in reader:
            if row.get(col_name):
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
