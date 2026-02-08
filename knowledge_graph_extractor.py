import csv
import json
import os
import time
from itertools import combinations

def process_knowledge_graph_from_csv(input_file, output_file, limit=None):
    """
    Extract knowledge graph directly from the entities already found in the CSV.
    Creates relationships based on co-occurrence in the same text.
    """
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return
    
    # Data structures
    # Map 'Original_Text' -> list of entity objects
    text_to_entities = {}
    
    # Read CSV
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        row_count = 0
        for row in reader:
            text = row.get("Original_Text", "").strip()
            if not text:
                continue
            
            # If limit is applied, we only want to process the first N *texts*, 
            # but the CSV has multiple rows per text. 
            # We'll handle limit by tracking unique texts processed.
            
            if text not in text_to_entities:
                text_to_entities[text] = []
            
            # Extract entity info from this row
            e_name = row.get("Entity_Text", "").strip()
            e_canon = row.get("Entity_Canonical_Name", "").strip()
            e_label = row.get("Entity_Label", "Unknown").strip()
            e_sent = row.get("Entity_Sentiment", "neutral").strip()
            
            # Validate entity
            if not e_name or e_name in ["N/A"] or not e_canon or e_canon in ["N/A"]:
                continue

            entity_data = {
                "name": e_name,
                "canonical": e_canon,
                "label": e_label,
                "sentiment": e_sent,
                "overall_sentiment": row.get("Overall_Sentiment", "neutral")
            }
            text_to_entities[text].append(entity_data)
            row_count += 1

    # Apply limit
    unique_texts = list(text_to_entities.keys())
    if limit:
        unique_texts = unique_texts[:limit]
        print(f"Limiting to {limit} unique text entries.")

    print(f"Processing {len(unique_texts)} texts to build graph...")
    
    # Build Graph Nodes and Edges
    nodes = {}  # Canonical Name -> Node Data
    edges = []  # List of edge objects
    
    for text in unique_texts:
        entities = text_to_entities[text]
        
        # Deduplicate entities in this text (e.g. if "Musk" appears twice)
        unique_entities_in_text = {}
        for e in entities:
            unique_entities_in_text[e['canonical']] = e
        
        entity_list = list(unique_entities_in_text.values())
        
        # Add Nodes
        for e in entity_list:
            canon = e['canonical']
            if canon not in nodes:
                nodes[canon] = {
                    "id": canon,  # Use canonical name as ID
                    "label": canon,
                    "type": e['label'],
                    "mentions": 0
                }
            nodes[canon]["mentions"] += 1

        # Create Edges (Co-occurrence)
        # Any two entities in the same text are related
        if len(entity_list) > 1:
            for e1, e2 in combinations(entity_list, 2):
                edges.append({
                    "source": e1['canonical'],
                    "target": e2['canonical'],
                    "relationship": "co-occurs_with",
                    "context": text[:100] + "...",
                    "sentiment": e1['overall_sentiment'], # specific edge sentiment is hard, use overall
                    "confidence": 1.0 # Certain they appeared together
                })
    
    # Format output
    output_nodes = list(nodes.values())
    
    kg_data = {
        "entities": output_nodes,
        "relationships": edges,
        "metadata": {
            "source_file": input_file,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "node_count": len(output_nodes),
            "edge_count": len(edges)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(kg_data, f, indent=2)

    print(f"\nKnowledge graph built successfully!")
    print(f"Nodes: {len(output_nodes)}")
    print(f"Edges: {len(edges)}")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python knowledge_graph_extractor.py <input_csv> <output_json> [limit]")
        sys.exit(1)
        
    process_knowledge_graph_from_csv(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
