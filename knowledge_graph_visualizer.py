import json
import sys
from collections import defaultdict

def generate_html_visualization(json_file, output_html):
    """Generate an interactive HTML visualization of the knowledge graph."""
    
    # Load knowledge graph
    with open(json_file, 'r', encoding='utf-8') as f:
        kg = json.load(f)
    
    # Extract data - handle new structure
    entities = kg.get("entities", [])
    relationships = kg.get("relationships", [])
    metadata = kg.get("metadata", {})
    
    # Pre-process nodes
    nodes = []
    
    # If list is empty, exit gracefully
    if not entities:
        print("No entities found in JSON.")
        return

    # Prepare Nodes
    for e in entities:
        # Check if it's new flat format or old nested
        id_val = e.get("id", e.get("canonical_name", "Unknown"))
        label_val = e.get("label", e.get("canonical_name", "Unknown"))
        type_val = e.get("type", "Unknown")
        mentions = e.get("mentions", 1)
        
        # Color by entity type
        type_colors = {
            "Person": "#FF6B6B",
            "Organization": "#4ECDC4",
            "Location": "#45B7D1",
            "Product": "#FFA07A",
            "Event": "#98D8C8",
            "Concept": "#C7CEEA",
            "Financial": "#FFD93D",
            "Unknown": "#95A5A6"
        }
        color = type_colors.get(type_val, "#95A5A6")
        
        nodes.append({
            "id": id_val,
            "label": label_val,
            "title": f"<b>{label_val}</b><br>Type: {type_val}<br>Mentions: {mentions}",
            "value": mentions, # standard vis.js size property
            "color": color,
            "group": type_val
        })
        
    # Prepare Edges
    edges = []
    for rel in relationships:
        src = rel.get("source")
        tgt = rel.get("target")
        label = rel.get("relationship", "related_to")
        context = rel.get("context", "")
        sentiment = rel.get("sentiment", "neutral")
        
        # Color edge by sentiment
        edge_color = "#95A5A6" # neutral gray
        if sentiment == "positive": edge_color = "#2ECC71"
        elif sentiment == "negative": edge_color = "#E74C3C"
        
        edges.append({
            "from": src,
            "to": tgt,
            "title": f"Relation: {label}<br>Context: {context}<br>Sentiment: {sentiment}",
            "color": {"color": edge_color, "highlight": edge_color},
            "arrows": "to"
        })

    # Only include unique nodes
    unique_nodes = list({v['id']:v for v in nodes}.values())

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Visualization</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; background: #f0f2f5; }}
        #network {{ width: 100vw; height: 100vh; background: #ffffff; }}
        .controls {{ position: absolute; top: 10px; left: 10px; z-index: 100; background: rgba(255,255,255,0.9); padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h2 {{ margin-top: 0; font-size: 1.2rem; }}
        .stats {{ margin-top: 10px; font-size: 0.9rem; color: #555; }}
    </style>
</head>
<body>
    <div class="controls">
        <h2>Knowledge Graph</h2>
        <div class="stats">
            Nodes: {len(unique_nodes)}<br>
            Edges: {len(edges)}<br>
            Source: {metadata.get('source_file', 'Unknown')}
        </div>
        <div style="margin-top:10px; font-size:0.8rem;">
            <span style="color:#FF6B6B">● Person</span> 
            <span style="color:#4ECDC4">● Org</span> 
            <span style="color:#45B7D1">● Loc</span>
        </div>
    </div>
    <div id="network"></div>
    <script>
        const nodes = new vis.DataSet({json.dumps(unique_nodes)});
        const edges = new vis.DataSet({json.dumps(edges)});
        
        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            nodes: {{
                shape: 'dot',
                scaling: {{
                    min: 10,
                    max: 30,
                    label: {{ enabled: true }}
                }},
                font: {{ size: 14, face: 'Tahoma' }}
            }},
            edges: {{
                width: 1.5,
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    springConstant: 0.04,
                    springLength: 150
                }}
            }},
            interaction: {{ hover: true, tooltipDelay: 200 }}
        }};
        
        const network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Visualization generated: {output_html}")
    print(f"Open this file in a web browser to view the interactive knowledge graph.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        pass
    else:
        generate_html_visualization(sys.argv[1], sys.argv[2])
