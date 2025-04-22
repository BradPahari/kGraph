from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import uuid
import os
import json

# Blueprint for graph building
graph_bp = Blueprint('graph', __name__)

HISTORY_FILE = 'kgraph_history.json'
HISTORY_RETENTION_DAYS = 20

# Ensure history file exists
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

def clean_old_history():
    with open(HISTORY_FILE, 'r') as f:
        data = json.load(f)

    cutoff = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
    filtered = [entry for entry in data if datetime.fromisoformat(entry['timestamp']) >= cutoff]

    with open(HISTORY_FILE, 'w') as f:
        json.dump(filtered, f, indent=2)

def save_to_history(entry):
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)

    history.append(entry)

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@graph_bp.route('/build-graph', methods=['POST'])
def build_graph():
    data = request.get_json()
    triples = data.get('triples', [])
    filename = data.get('filename', 'unknown.csv')

    nodes = []
    edges = []
    node_map = {}
    node_sources = {}  # node label -> filename
    node_id = 1

    for t in triples:
        subj = t['subject']
        obj = t['object']
        pred = t['predicate']
        def clean_filename(f):
            return f.split("_", 1)[1] if "_" in f else f

        subj_file = clean_filename(t.get('subjectFile', 'unknown.csv'))
        obj_file = clean_filename(t.get('objectFile', 'unknown.csv'))


        if subj not in node_map:
            node_map[subj] = node_id
            nodes.append({"id": node_id, "label": subj})
            node_sources[subj] = subj_file
            node_id += 1
        if obj not in node_map:
            node_map[obj] = node_id
            nodes.append({"id": node_id, "label": obj})
            node_sources[obj] = obj_file
            node_id += 1

        edges.append({
            "from": node_map[subj],
            "to": node_map[obj],
            "label": pred
        })

    # Build node relationship data
    nodeRelationships = {}
    for edge in edges:
        from_id = edge['from']
        to_id = edge['to']
        label = edge['label']

        from_label = next(n['label'] for n in nodes if n['id'] == from_id)
        to_label = next(n['label'] for n in nodes if n['id'] == to_id)

        if str(from_id) not in nodeRelationships:
            nodeRelationships[str(from_id)] = []
        if str(to_id) not in nodeRelationships:
            nodeRelationships[str(to_id)] = []

        nodeRelationships[str(from_id)].append({
            "label": label,
            "direction": "→",
            "target": to_label,
            "file": node_sources.get(to_label, "")
        })

        nodeRelationships[str(to_id)].append({
            "label": label,
            "direction": "←",
            "target": from_label,
            "file": node_sources.get(from_label, "")
        })

    graphData = {
        "nodes": nodes,
        "edges": edges,
        "nodeSources": node_sources  # ✅ added
    }

    entry = {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "triples": triples,
        "graphData": graphData,
        "nodeRelationships": nodeRelationships
    }

    clean_old_history()
    save_to_history(entry)

    return jsonify(graphData)


@graph_bp.route('/graph-history', methods=['GET'])
def get_graph_history():
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)

    # Keep only entries within last 20 days
    cutoff = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
    filtered = [
        h for h in history
        if datetime.fromisoformat(h['timestamp']) >= cutoff
    ]

    return jsonify(filtered)
