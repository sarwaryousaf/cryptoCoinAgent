from flask import Flask, request, jsonify, send_from_directory
from agent.core import CryptoAgent
import os

app = Flask(__name__, static_folder='static')
agent = CryptoAgent()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('static', 'style.css')
    
@app.route('/script.js')
def script():
    return send_from_directory('static', 'script.js')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    response = agent.process_query(query)
    
    return jsonify({
        'answer': response.answer,
        'source': response.source,
        'confidence': response.confidence
    })

if __name__ == '__main__':
    print("Starting Crypto Agent Web UI on http://localhost:5000")
    app.run(debug=True, port=5000)
