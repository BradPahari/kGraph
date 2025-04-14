# upload_csv.py
from flask import Blueprint, request, jsonify
import csv
import os
import uuid

upload_bp = Blueprint('upload', __name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@upload_bp.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

            for i, row in enumerate(rows, start=2):
                if len(row) != len(headers):
                    return jsonify({'error': f'Invalid CSV format at row {i}.'}), 400
                if any(cell.strip() == '' for cell in row):
                    return jsonify({'error': f'Missing or blank value in row {i}.'}), 400

        return jsonify({
            'message': 'File uploaded and converted to JSON-LD successfully.',
            'filename': filename,
            'headers': headers,
            'rows': rows
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
