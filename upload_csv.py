# upload_csv.py
from flask import Blueprint, request, jsonify
import csv
import os
import uuid

upload_bp = Blueprint('upload', __name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@upload_bp.route('/upload', methods=['POST'])
@upload_bp.route('/upload', methods=['POST'])
def upload_csv():
    files = request.files.getlist('files')
    if not files or not all(f.filename.endswith('.csv') for f in files):
        return jsonify({'error': 'Invalid file type. Only CSV files allowed.'}), 400

    file_infos = []

    for file in files[:5]:  # Accept up to 5 files
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

        file_infos.append({
            'filename': filename,
            'headers': headers,
            'rows': rows
        })

    return jsonify({'message': 'Files uploaded successfully.', 'files': file_infos})
