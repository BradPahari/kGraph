from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
import json

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files.get('file')

    # File type validation
    if not file or not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file type. Please upload a .csv file."}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            # Validate headers
            headers = reader.fieldnames
            if not headers or any(h is None or h.strip() == '' for h in headers):
                return jsonify({"error": "Invalid CSV format: headers are missing or malformed."}), 400

            # Check for inconsistent structure or missing required fields
            for i, row in enumerate(rows):
                if len(row) != len(headers):
                    return jsonify({"error": f"Invalid CSV format: inconsistent structure on row {i+2}."}), 400
                for field in ["ObjectID", "Brand_Name", "Brand_Type", "Description"]:
                    if field not in row or row[field].strip() == "":
                        return jsonify({"error": f"Invalid CSV format: missing or empty '{field}' in row {i+2}."}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400

    # Convert CSV rows to JSON-LD
    context = {
        "@context": {
            "ObjectID": "http://example.org/ObjectID",
            "Brand_Name": "http://example.org/Brand_Name",
            "Brand_Type": "http://example.org/Brand_Type",
            "Description": "http://example.org/Description"
        }
    }

    graph = []
    for row in rows:
        entry = {"@type": "Product"}
        for k, v in row.items():
            entry[k.strip()] = v.strip()
        graph.append(entry)

    jsonld = context.copy()
    jsonld["@graph"] = graph

    # Prepare nodes and edges for knowledge graph visualization
    nodes = set()
    edges = []

    for row in rows:
        subj = row.get("Brand_Name", "Unknown Brand").strip()
        subj_id = f"Brand::{subj}"
        nodes.add(subj_id)

        for key in ["Brand_Type", "ObjectID", "Description"]:
            if key in row and row[key].strip():
                obj = row[key].strip()
                obj_id = f"{key}::{obj}"
                nodes.add(obj_id)
                edges.append({"from": subj_id, "to": obj_id, "label": key})

    node_list = [{"id": n, "label": n.split("::", 1)[-1]} for n in nodes]

    return jsonify({
        "message": "File uploaded and converted to JSON-LD successfully.",
        "jsonld": jsonld,
        "nodes": node_list,
        "edges": edges
    })

if __name__ == '__main__':
    app.run(debug=True)
