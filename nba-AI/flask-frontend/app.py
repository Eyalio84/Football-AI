"""
NBA-AI Flask Frontend
Simple Python server serving HTML/CSS/JS
Talks to FastAPI backend on port 8001
"""

from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

BACKEND_URL = os.getenv("NBA_BACKEND_URL", "http://localhost:8001")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    team = request.args.get('team', 'lakers')
    return render_template('chat.html', team=team)

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    """Proxy chat requests to backend."""
    try:
        data = request.get_json()
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat",
            json=data,
            timeout=30
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/teams')
def proxy_teams():
    """Proxy teams request to backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/teams", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("NBA-AI Flask Frontend")
    print(f"Backend: {BACKEND_URL}")
    print("Starting on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
