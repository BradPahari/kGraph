# prepare_triples.py
from flask import Blueprint, request, jsonify
import os
import csv

triples_bp = Blueprint('triples', __name__)
UPLOAD_FOLDER = 'uploads'

@triples_bp.route('/prepare-triples', methods=['POST'])
def prepare_triples():
    data = request.get_json()
    subject_file = data.get('subject_file')
    object_file = data.get('object_file')
    subject_col = data.get('subject')
    object_col = data.get('object')

    if not subject_file or not object_file or not subject_col or not object_col:
        return jsonify({'error': 'Missing input parameters.'}), 400

    def extract_column_values(filename, column):
        path = os.path.join(UPLOAD_FOLDER, filename)
        values = []
        if os.path.exists(path):
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    val = row.get(column, "").strip()
                    values.append(val if val else "-")
        return values

    subject_vals = extract_column_values(subject_file, subject_col)
    object_vals = extract_column_values(object_file, object_col)

    # Pad shorter list with dashes
    max_len = max(len(subject_vals), len(object_vals))
    subject_vals += ["-"] * (max_len - len(subject_vals))
    object_vals += ["-"] * (max_len - len(object_vals))

    triples = []
    for i in range(max_len):
        triples.append({
            'subject': subject_vals[i],
            'predicate': 'hasType',
            'object': object_vals[i],
            'subjectFile': subject_file,
            'objectFile': object_file
        })

    return jsonify({'triples': triples})
