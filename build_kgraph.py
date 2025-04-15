# build_kgraph.py
from flask import Blueprint, request, jsonify

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/build-graph', methods=['POST'])
def build_graph():
    data = request.get_json()
    triples = data.get('triples', [])

    nodes = []
    edges = []
    seen = {}

    def get_node_id(label):
        if label not in seen:
            seen[label] = len(seen) + 1
            nodes.append({ 'id': seen[label], 'label': label })
        return seen[label]

    for triple in triples:
        from_id = get_node_id(triple['subject'])
        to_id = get_node_id(triple['object'])
        edges.append({
            'from': from_id,
            'to': to_id,
            'label': triple['predicate']
        })

    return jsonify({ 'nodes': nodes, 'edges': edges })
