from flask import Flask, render_template
from flask_cors import CORS
from upload_csv import upload_bp
from prepare_triples import triples_bp
from build_kgraph import graph_bp

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/')
def index():
    return render_template('index.html')

app.register_blueprint(upload_bp)
app.register_blueprint(triples_bp)
app.register_blueprint(graph_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
