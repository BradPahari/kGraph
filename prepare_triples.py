# prepare_triples.py
from flask import Blueprint, request, jsonify
import os
import csv

triples_bp = Blueprint('triples', __name__)
UPLOAD_FOLDER = 'uploads'

@triples_bp.route('/prepare-triples', methods=['POST'])
def prepare_triples():
    data = request.get_json()
    filename = data.get('filename')
    subject_col = data.get('subject')
    object_col = data.get('object')

    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Uploaded file not found.'}), 404

    triples = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj = row.get(subject_col)
            obj = row.get(object_col)
            if not subj or not obj:
                continue
            triples.append({'subject': subj, 'predicate': 'hasType', 'object': obj})

    return jsonify({'triples': triples})
