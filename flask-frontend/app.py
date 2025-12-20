"""
Soccer-AI Flask Frontend
Simple Python server serving static HTML/CSS/JS
Talks to FastAPI backend on port 8000

COMPLETE API INTEGRATION:
- Chat with compound intelligence
- Standings (league tables)
- Fixtures (games schedule)
- Predictions (match predictor)
- Trivia (quiz game)
- Teams (full details)
"""

from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

@app.route('/')
def index():
    """Home page with all 20 club personas."""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Chat interface with fluent conversation support."""
    return render_template('chat.html')

@app.route('/standings')
def standings():
    """Premier League standings table."""
    return render_template('standings.html')

@app.route('/fixtures')
def fixtures():
    """Upcoming fixtures and recent results."""
    return render_template('fixtures.html')

@app.route('/predictions')
def predictions():
    """Match predictor with Third Knowledge patterns."""
    return render_template('predictions.html')

@app.route('/teams')
def teams():
    """Browse all teams with details."""
    return render_template('teams.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
