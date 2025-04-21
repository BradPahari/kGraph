# prepare_triples.py
from flask import Blueprint, request, jsonify
import os
import csv

triples_bp = Blueprint('triples', __name__)
UPLOAD_FOLDER = 'uploads'

@triples_bp.route('/prepare-triples', methods=['POST'])
def prepare_triples():
    data = request.get_json()
    subject_file = data.get('subjectFile')
    object_file = data.get('objectFile')
    subject_col = data.get('subject')
    object_col = data.get('object')

    if not subject_file or not object_file or not subject_col or not object_col:
        return jsonify({'error': 'Missing input parameters.'}), 400

    subject_path = os.path.join(UPLOAD_FOLDER, subject_file)
    object_path = os.path.join(UPLOAD_FOLDER, object_file)

    if not os.path.exists(subject_path) or not os.path.exists(object_path):
        return jsonify({'error': 'One or both files not found.'}), 404

    triples = []

    with open(subject_path, newline='', encoding='utf-8') as subj_f, \
         open(object_path, newline='', encoding='utf-8') as obj_f:

        subj_reader = csv.DictReader(subj_f)
        obj_reader = csv.DictReader(obj_f)

        for subj_row, obj_row in zip(subj_reader, obj_reader):
            subj_val = subj_row.get(subject_col, "").strip()
            obj_val = obj_row.get(object_col, "").strip()

            triples.append({
                'subject': subj_val if subj_val else "-",
                'predicate': 'hasType',
                'object': obj_val if obj_val else "-"
            })

    return jsonify({'triples': triples})

