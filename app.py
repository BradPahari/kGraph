from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
from rdflib import Graph, URIRef, Literal, Namespace

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Convert CSV to RDF from custom format
    g = Graph()
    EX = Namespace("http://example.org/")

    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            brand = row['Brand Name'].strip()
            brand_type = row['Brand Type'].strip()
            description = row['Description'].strip()

            brand_uri = URIRef(EX[brand.replace(" ", "_")])

            g.add((brand_uri, URIRef(EX['BrandType']), Literal(brand_type)))
            g.add((brand_uri, URIRef(EX['Description']), Literal(description)))

    rdf_file = filepath.replace('.csv', '.ttl')
    g.serialize(destination=rdf_file, format='turtle')

    # Prepare nodes and edges for visualization
    nodes = set()
    edges = []
    for s, p, o in g:
        nodes.add(str(s))
        nodes.add(str(o))
        edges.append({"from": str(s), "to": str(o), "label": str(p).split('/')[-1]})

    node_list = [{"id": n, "label": n.split('/')[-1] if '/' in n else n} for n in nodes]

    return jsonify({"nodes": node_list, "edges": edges})

if __name__ == '__main__':
    app.run(debug=True)