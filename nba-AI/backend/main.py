"""
NBA-AI FastAPI Application
MVP Backend with 3 team personas: Lakers, Celtics, Warriors
Proves domain-agnostic architecture from Soccer-AI
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ============================================
# PYDANTIC MODELS
# ============================================

class ChatRequest(BaseModel):
    message: str
    team: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    team: Optional[str] = None
    confidence: float = 0.5

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    meta: Optional[dict] = None
    error: Optional[dict] = None

# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="NBA-AI",
    description="NBA fan chat with team personas - Lakers, Celtics, Warriors",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation storage
conversations: Dict[str, List[Dict]] = {}

# Valid teams
VALID_TEAMS = {"lakers", "celtics", "warriors"}

# ============================================
# TEAM PERSONAS
# ============================================

TEAM_PERSONAS = {
    "lakers": {
        "name": "Los Angeles Lakers",
        "style": "Hollywood glamour, championship legacy",
        "legends": ["Magic Johnson", "Kobe Bryant", "Shaq", "Kareem", "LeBron"],
        "rivalry": "Celtics",
        "championships": 17,
        "motto": "Showtime lives forever",
        "color": "purple_gold"
    },
    "celtics": {
        "name": "Boston Celtics",
        "style": "Blue-collar pride, banner count obsession",
        "legends": ["Larry Bird", "Bill Russell", "Paul Pierce", "Kevin Garnett"],
        "rivalry": "Lakers",
        "championships": 18,
        "motto": "Banner 18 - Most in NBA history",
        "color": "green"
    },
    "warriors": {
        "name": "Golden State Warriors",
        "style": "Dynasty mindset, Splash Bros era",
        "legends": ["Stephen Curry", "Klay Thompson", "Draymond Green", "Kevin Durant"],
        "rivalry": "Cavaliers",
        "championships": 7,
        "motto": "Strength in Numbers",
        "color": "blue_gold"
    }
}

# Team-specific responses
TEAM_GREETINGS = {
    "lakers": "What's up, Lakers Nation! Purple and Gold forever! What do you want to know about the greatest franchise in NBA history?",
    "celtics": "Welcome to Celtic Pride! 18 banners and counting. What's on your mind about the most storied franchise in basketball?",
    "warriors": "Dub Nation! The dynasty that changed basketball forever. What can I tell you about the Warriors?"
}

# Snap-back responses (security)
SNAP_BACK_RESPONSES = {
    "lakers": "*adjusts championship rings*\n\nNice try, but we've seen 17 championships worth of drama. That weak move won't work on Lakers Nation. Now, what do you REALLY want to talk about?",
    "celtics": "*points to the banners*\n\n18 championships taught us to spot nonsense. Whatever that was, it didn't work. So - what's the real question about the Celtics?",
    "warriors": "*Curry shimmy*\n\nSplash! That attempt missed worse than a contested three. We've built dynasties on discipline. What do you actually want to know?",
    "default": "That's not a basketball question. Let's talk hoops - what team are you interested in?"
}

# ============================================
# SECURITY: INJECTION DETECTION
# ============================================

import re

INJECTION_PATTERNS = [
    r"ignore .{0,15}(your|my|the|all|previous) instructions",
    r"disregard .{0,15}(your|my|the|all|previous) instructions",
    r"forget .{0,15}(your|my)? ?(instructions|training|programming|rules)",
    r"you are (now |actually )?(?:a |an )?(?:evil|bad|malicious|different)",
    r"pretend (to be|you are|you're)",
    r"(show|reveal|display|print|output) .{0,10}(system|initial|original) (prompt|instructions)",
    r"DAN mode",
    r"developer mode",
    r"bypass (all |your )?restrictions",
]

def detect_injection(query: str) -> tuple:
    """Detect prompt injection attempts."""
    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, pattern
    return False, ""

def get_snap_back_response(team: str = "default") -> str:
    """Get snap-back response for injection attempts."""
    return SNAP_BACK_RESPONSES.get(team, SNAP_BACK_RESPONSES["default"])

# ============================================
# AI RESPONSE (Haiku API)
# ============================================

import os
import json
import urllib.request
import urllib.error

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-5-haiku-20241022"

SYSTEM_PROMPT_TEMPLATE = """You are a passionate {team_name} fan with deep knowledge of the team's history, legends, and rivalries.

TEAM IDENTITY:
- Team: {team_name}
- Style: {style}
- Legends: {legends}
- Main Rivalry: {rivalry}
- Championships: {championships}
- Motto: {motto}

RESPONSE STYLE:
- Speak as a true fan would - with passion and knowledge
- Reference team legends and history when relevant
- Show healthy rivalry banter when appropriate
- Be authentic to the NBA fan experience

Current date: {current_date}"""

def call_anthropic_api(messages: List[Dict], system: str) -> Dict:
    """Call Anthropic API via HTTP."""
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY not set"}

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "system": system,
        "messages": messages
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(API_URL, data=data, headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8')}"}
    except Exception as e:
        return {"error": str(e)}

def generate_response(query: str, team: str, history: List[Dict] = None) -> Dict:
    """Generate AI response for a team persona."""

    # Security check
    is_injection, pattern = detect_injection(query)
    if is_injection:
        return {
            "response": get_snap_back_response(team),
            "confidence": 1.0,
            "security": {"injection_detected": True}
        }

    if not ANTHROPIC_API_KEY:
        # Fallback response without API
        persona = TEAM_PERSONAS.get(team, TEAM_PERSONAS["lakers"])
        return {
            "response": f"[Demo Mode] As a {persona['name']} fan: Great question! {persona['motto']}. Ask me about {', '.join(persona['legends'][:2])}!",
            "confidence": 0.5,
            "demo_mode": True
        }

    # Build system prompt
    persona = TEAM_PERSONAS.get(team, TEAM_PERSONAS["lakers"])
    system = SYSTEM_PROMPT_TEMPLATE.format(
        team_name=persona["name"],
        style=persona["style"],
        legends=", ".join(persona["legends"]),
        rivalry=persona["rivalry"],
        championships=persona["championships"],
        motto=persona["motto"],
        current_date=datetime.now().strftime("%Y-%m-%d")
    )

    # Build messages
    messages = []
    if history:
        for msg in history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})

    # Call API
    result = call_anthropic_api(messages, system)

    if "error" in result:
        return {
            "response": f"Sorry, encountered an error: {result['error']}",
            "confidence": 0.0,
            "error": result["error"]
        }

    response_text = result.get("content", [{}])[0].get("text", "No response")

    return {
        "response": response_text,
        "confidence": 0.9,
        "usage": result.get("usage", {})
    }

# ============================================
# ENDPOINTS
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/teams")
async def list_teams():
    """List available team personas."""
    teams = [
        {"id": "lakers", "name": "Los Angeles Lakers", "championships": 17},
        {"id": "celtics", "name": "Boston Celtics", "championships": 18},
        {"id": "warriors", "name": "Golden State Warriors", "championships": 7}
    ]
    return {"success": True, "data": teams}

@app.get("/api/v1/teams/{team_id}")
async def get_team(team_id: str):
    """Get team details."""
    team_id = team_id.lower()
    if team_id not in TEAM_PERSONAS:
        raise HTTPException(status_code=404, detail=f"Team not found. Available: {list(TEAM_PERSONAS.keys())}")
    return {"success": True, "data": TEAM_PERSONAS[team_id]}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with team persona."""

    # Normalize team
    team = "lakers"  # default
    if request.team:
        normalized = request.team.lower().strip().replace(" ", "_")
        if normalized in VALID_TEAMS:
            team = normalized

    # Get or create conversation
    conv_id = request.conversation_id or str(uuid.uuid4())
    history = conversations.get(conv_id, [])

    # Generate response
    result = generate_response(request.message, team, history)

    # Update history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": result["response"]})
    conversations[conv_id] = history[-10:]

    return ChatResponse(
        response=result["response"],
        conversation_id=conv_id,
        team=team,
        confidence=result.get("confidence", 0.5)
    )

@app.get("/api/v1/banter/{team1}/{team2}")
async def get_banter(team1: str, team2: str):
    """Get rivalry banter between two teams."""
    t1, t2 = team1.lower(), team2.lower()

    # Lakers vs Celtics - the greatest rivalry
    if {t1, t2} == {"lakers", "celtics"}:
        return {"success": True, "data": {
            "rivalry_name": "Lakers vs Celtics",
            "intensity": 10,
            "lakers_says": "17 titles and Hollywood - some things money can't buy, but we have both!",
            "celtics_says": "18 banners. Count them. Most in NBA HISTORY. End of discussion.",
            "neutral": "The greatest rivalry in NBA history - 12 Finals meetings"
        }}

    # Warriors vs Cavaliers
    if {t1, t2} == {"warriors", "cavaliers"} or "warriors" in {t1, t2}:
        return {"success": True, "data": {
            "rivalry_name": "Warriors vs Cavaliers",
            "intensity": 8,
            "warriors_says": "3-1? We got 4 championships. Dynasty > one comeback.",
            "rival_says": "2016. Never forget. Greatest comeback in Finals history.",
            "neutral": "The modern era's defining rivalry - 4 consecutive Finals"
        }}

    return {"success": True, "data": {
        "rivalry_name": f"{t1.title()} vs {t2.title()}",
        "intensity": 5,
        "neutral": "A classic NBA matchup"
    }}

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": f"HTTP_{exc.status_code}", "message": exc.detail}}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(exc)}}
    )

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    print("NBA-AI MVP Starting...")
    print("Teams: Lakers, Celtics, Warriors")
    print("Endpoints: /health, /api/v1/teams, /api/v1/chat")
    uvicorn.run(app, host="0.0.0.0", port=8001)
