"""
Soccer-AI FastAPI Application
Main entry point for the backend API
"""

import os
import uuid
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import database
import rag
import ai_response
import conversation_intelligence as ci
import fan_enhancements
from rate_limiter import check_rate_limit, get_budget_status

# 4D Persona Architecture (feature-flagged)
from config import USE_4D_PERSONA
if USE_4D_PERSONA:
    from persona_bridge import get_persona_bridge
from predictor.prediction_engine import PredictionEngine
from predictor.tri_lens_predictor import TriLensPredictor
from models import (
    ChatRequest, ChatResponse, ChatSource,
    ApiResponse, PaginatedMeta, SearchResults, DbStats,
    TeamBase, TeamDetail, PlayerBase, PlayerDetail, PlayerStats,
    GameBase, GameDetail, InjuryBase, TransferBase, StandingEntry,
    NewsArticle, ErrorResponse, ErrorDetail
)

# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="Soccer-AI",
    description="Living knowledge base with AI-powered chat for soccer information",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
_cors_origins = [
    "http://localhost:5173",   # React dev server
    "http://localhost:5000",   # Flask frontend
    "http://localhost:8000",   # Self-reference
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]
# Add production origins from environment
_extra_origins = os.environ.get("CORS_ORIGINS", "")
if _extra_origins:
    _cors_origins.extend(o.strip() for o in _extra_origins.split(",") if o.strip())
# Always allow verbalogix.com
_cors_origins.extend([
    "https://www.verbalogix.com",
    "https://verbalogix.com",
    "https://football-ai.vercel.app",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation storage (use Redis in production)
conversations = {}

# Valid club names for fan personas (validated against database)
# "analyst" is a special case - neutral predictor persona (The Analyst)
VALID_CLUBS = {
    "arsenal", "chelsea", "manchester_united", "liverpool",
    "manchester_city", "tottenham", "newcastle", "west_ham", "everton",
    "brighton", "aston_villa", "wolves", "crystal_palace", "fulham",
    "nottingham_forest", "brentford", "bournemouth", "leicester",
    "ipswich", "southampton",
    "analyst"  # Special neutral predictor persona
}

# Club name to team ID mapping (for persona data loading)
CLUB_TO_TEAM_ID = {
    "manchester_city": 1,
    "liverpool": 2,
    "arsenal": 3,
    "chelsea": 4,
    "manchester_united": 5,
    "tottenham": 6,
    "newcastle": 7,
    "brighton": 8,
    "aston_villa": 9,
    "west_ham": 10,
    "everton": 16,
    "wolves": 13,
    "crystal_palace": 14,
    "fulham": 15,
    "nottingham_forest": 17,
    "brentford": 11,
    "bournemouth": 20,
    "leicester": 12,
    "ipswich": 22,
    "southampton": 23
}


# ============================================
# STARTUP/SHUTDOWN
# ============================================

REFRESH_INTERVAL_HOURS = 6

async def _run_data_refresh():
    """Run refresh_season_data.py in a subprocess."""
    script = Path(__file__).parent / "scripts" / "refresh_season_data.py"
    if not script.exists():
        logging.warning("refresh_season_data.py not found — skipping auto-refresh")
        return
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            logging.info("Data refresh completed successfully")
        else:
            logging.warning("Data refresh exited with code %d: %s",
                            proc.returncode, stdout.decode()[-300:])
    except Exception as e:
        logging.warning("Data refresh failed: %s", e)


async def _periodic_refresh():
    """Background loop: refresh data every REFRESH_INTERVAL_HOURS."""
    # Initial refresh 30s after startup (let the server settle)
    await asyncio.sleep(30)
    while True:
        logging.info("Running scheduled data refresh...")
        await _run_data_refresh()
        await asyncio.sleep(REFRESH_INTERVAL_HOURS * 3600)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    if not Path(database.DB_PATH).exists():
        database.init_db()
    # Initialize analytics table (CP6)
    database.init_analytics()
    # Initialize gap tracker table (Phase 0)
    database.init_gap_tracker()
    # Initialize security tables (Phase 1)
    database.init_security_tables()
    # Initialize trivia table (Phase 6)
    database.init_trivia_table()
    # Start periodic data refresh (standings, fixtures, moods)
    asyncio.create_task(_periodic_refresh())
    print(f"Soccer-AI started. Database: {database.DB_PATH}")


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    """Root redirect to API docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============================================
# CHAT ENDPOINT (Primary Interface)
# ============================================

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request = None):
    """
    Main chat endpoint. User asks natural language question, gets AI response.
    Uses KG-RAG hybrid retrieval and logs analytics.
    """
    start_time = time.time()

    # Rate limit check
    client_ip = req.client.host if req and req.client else "unknown"
    allowed, limit_msg = check_rate_limit(client_ip, "chat")
    if not allowed:
        return ChatResponse(
            response=limit_msg,
            conversation_id=request.conversation_id or "",
            sources=[],
            confidence=0.0,
        )

    try:
        # Get or create conversation (hybrid: in-memory cache + SQLite persistence)
        conv_id = request.conversation_id or str(uuid.uuid4())
        history = conversations.get(conv_id)
        if history is None:
            history = database.load_conversation(conv_id)
            if history:
                conversations[conv_id] = history

        # Normalize and validate club name (security: prevent injection via club field)
        club = None
        if request.club:
            # Normalize: lowercase, replace spaces/hyphens with underscores
            normalized_club = request.club.lower().strip().replace(" ", "_").replace("-", "_")
            # Resolve common aliases (man_united -> manchester_united, etc.)
            normalized_club = TEAM_NAME_MAP.get(normalized_club, normalized_club)
            # Only accept known valid clubs
            if normalized_club in VALID_CLUBS:
                club = normalized_club
            # else: silently fall back to generic (don't expose valid club list)

        # Check for injection attempt first
        is_injection, pattern = ai_response.detect_injection(request.message)

        if is_injection:
            # Log injection attempt
            database.log_query(
                query=request.message,
                was_injection_attempt=True,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            # Return snap-back response
            snap_back = ai_response.get_snap_back_response(club or "default")
            return ChatResponse(
                response=snap_back,
                conversation_id=conv_id,
                sources=[],
                confidence=0.0
            )

        # ===== COMPOUND INTELLIGENT CONVERSATION SYSTEM =====
        # Get conversation state for fluency
        conv_state = ci.get_conversation_state(conv_id, club=club)

        # CRITICAL: Load persona data on first turn (COST OPTIMIZATION: cached for session!)
        if conv_state.persona_data is None and club and club in CLUB_TO_TEAM_ID:
            team_id = CLUB_TO_TEAM_ID[club]
            conv_state.persona_data = database.load_full_persona(team_id)
            print(f"[PERSONA] Loaded personality data for {club} (team_id={team_id})")

        # ===== FAN ENHANCEMENTS: Dynamic Mood + Rivalry + Dialect =====
        if club:
            # ===== 4D PERSONA PATH (Feature-flagged) =====
            if USE_4D_PERSONA:
                # Compute 4D state from LIVE match data
                bridge = get_persona_bridge()
                state_4d = bridge.compute_4d_state(
                    club_id=club,
                    user_message=request.message,
                    conversation_history=history
                )

                # Store 4D state for ai_response.py to use
                conv_state.use_4d = True
                conv_state.persona_4d = state_4d
                conv_state.conversation_topics = bridge.get_conversation_topics(club)

                # Log 4D position
                print(f"[4D] X={state_4d.x.mood} ({state_4d.x.intensity:.2f}) | "
                      f"Y={'✓' if state_4d.y.activated else '○'} | "
                      f"Z={state_4d.z.dialect} | T={state_4d.t.step}")

                # Still load persona_data for backwards compatibility with other systems
                if conv_state.persona_data:
                    # Inject 4D computed values
                    conv_state.persona_data["mood"] = {
                        "current_mood": state_4d.x.mood,
                        "intensity": state_4d.x.intensity,
                        "reason": state_4d.x.reason,
                        "form": ""  # Will be populated by ground truth if needed
                    }

            # ===== LEGACY PATH (fan_enhancements) =====
            else:
                conv_state.use_4d = False

                # Get enhanced persona (mood from results, rivalry detection, dialect)
                enhanced = fan_enhancements.get_enhanced_persona(club, request.message)

                # Override mood with dynamic calculation from recent results
                if conv_state.persona_data:
                    conv_state.persona_data["mood"] = enhanced["mood"]
                    conv_state.persona_data["rivalry"] = enhanced.get("rivalry")
                    conv_state.persona_data["dialect"] = enhanced.get("dialect")
                else:
                    conv_state.persona_data = enhanced

                # Log rivalry trigger if detected
                if enhanced.get("has_rivalry_trigger"):
                    rivalry = enhanced["rivalry"]
                    print(f"[RIVALRY] ⚔️ {rivalry['derby_name']} triggered! ({rivalry['rival_display']})")

                # Log dynamic mood
                mood = enhanced["mood"]
                print(f"[MOOD] {mood['current_mood'].upper()} {enhanced['mood_emoji']} - Form: {mood['form']}")

        # Detect and resolve follow-up queries
        query_to_process = request.message
        is_follow_up, resolved_query = ci.detect_follow_up(request.message, conv_state)
        if is_follow_up and resolved_query:
            query_to_process = resolved_query
            # Log follow-up detection for analytics
            print(f"[FOLLOW-UP] Resolved: '{request.message}' -> '{resolved_query}'")

        # KG-RAG hybrid retrieval (upgraded from basic RAG)
        # Use resolved query for better context retrieval
        context, sources, metadata = rag.retrieve_hybrid(query_to_process, club=club)

        # Build compound context (anti-repetition, emotional continuity)
        enriched_context, sources, ci_metadata = ci.build_compound_context(
            query=query_to_process,
            base_context=context,
            base_sources=sources,
            state=conv_state
        )

        # ===== USER FAN MEMORY: Recall stored memories for this session/club =====
        enriched_context = _maybe_inject_fan_memories(conv_id, club, enriched_context)

        # ===== PREDICTOR EXPLAINABILITY: Inject Dixon-Coles prediction into context =====
        enriched_context = _maybe_inject_prediction(request.message, enriched_context, club)

        # Generate AI response (KG-aware, with compound intelligence + mood framing)
        result = ai_response.generate_response(
            query=request.message,
            context=enriched_context,  # Use enriched context with compound intelligence
            sources=sources,
            conversation_history=history,
            club=club or "default",
            session_id=conv_id,  # Enable session-based escalation
            persona_data=conv_state.persona_data,  # CRITICAL: Pass cached persona for mood framing
            # 4D Persona parameters (feature-flagged)
            use_4d=getattr(conv_state, 'use_4d', False),
            persona_4d=getattr(conv_state, 'persona_4d', None),
            conversation_topics=getattr(conv_state, 'conversation_topics', None)
        )

        # Update conversation state after response
        entities = metadata.get('entities', {})
        intent = metadata.get('kg_intent', metadata.get('intent', 'general'))
        ci.update_conversation_state(
            state=conv_state,
            query=request.message,
            entities=entities,
            intent=intent,
            response=result["response"]
        )

        # ===== USER FAN MEMORY: Detect and store personal memories =====
        _maybe_store_fan_memory(request.message, conv_id, club)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log query analytics (CP6)
        try:
            # Extract first club from entities if available
            club_detected = None
            entities = metadata.get('entities', {})
            teams = entities.get('teams', [])
            if teams:
                club_detected = teams[0]

            database.log_query(
                query=request.message,
                kg_intent=metadata.get('kg_intent'),
                club_detected=club_detected,
                kg_nodes_used=entities.get('kg_nodes', 0) if isinstance(entities.get('kg_nodes'), int) else len(entities.get('kg_nodes', [])),
                source_count=len(sources),
                confidence=result.get('confidence'),
                response_time_ms=response_time_ms,
                was_injection_attempt=False
            )
        except Exception:
            pass  # Don't fail on analytics errors

        # Update conversation history (in-memory + persist to SQLite)
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": result["response"]})
        conversations[conv_id] = history[-10:]  # Keep last 10 messages
        database.save_conversation(conv_id, conversations[conv_id])

        # Format sources
        formatted_sources = [
            ChatSource(type=s["type"], id=s.get("id"))
            for s in sources
        ]

        return ChatResponse(
            response=result["response"],
            conversation_id=conv_id,
            sources=formatted_sources,
            confidence=result.get("confidence", 0.5),
            usage=result.get("usage")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STREAMING CHAT ENDPOINT
# ============================================

@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns tokens as Server-Sent Events.

    Same logic as /api/v1/chat but streams response in real-time.
    Frontend receives chunks as they arrive for a "typing" effect.
    """
    import time
    import json as json_lib

    try:
        # Get or create conversation (hybrid: in-memory cache + SQLite persistence)
        conv_id = request.conversation_id or str(uuid.uuid4())
        history = conversations.get(conv_id)
        if history is None:
            history = database.load_conversation(conv_id)
            if history:
                conversations[conv_id] = history

        # Normalize and validate club name
        club = None
        if request.club:
            normalized_club = request.club.lower().strip().replace(" ", "_").replace("-", "_")
            if normalized_club in VALID_CLUBS:
                club = normalized_club

        # Check for injection attempt first
        is_injection, pattern = ai_response.detect_injection(request.message)

        if is_injection:
            # Return snap-back as a single SSE event
            snap_back = ai_response.get_snap_back_response(club or "default")

            async def injection_response():
                yield f"data: {json_lib.dumps({'text': snap_back})}\n\n"
                yield f"data: {json_lib.dumps({'done': True, 'conversation_id': conv_id})}\n\n"

            return StreamingResponse(
                injection_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        # Get conversation state for fluency
        conv_state = ci.get_conversation_state(conv_id, club=club)

        # Load persona data on first turn
        if conv_state.persona_data is None and club and club in CLUB_TO_TEAM_ID:
            team_id = CLUB_TO_TEAM_ID[club]
            conv_state.persona_data = database.load_full_persona(team_id)

        # ===== FAN ENHANCEMENTS: Dynamic Mood + Rivalry + Dialect =====
        if club:
            enhanced = fan_enhancements.get_enhanced_persona(club, request.message)
            if conv_state.persona_data:
                conv_state.persona_data["mood"] = enhanced["mood"]
                conv_state.persona_data["rivalry"] = enhanced.get("rivalry")
                conv_state.persona_data["dialect"] = enhanced.get("dialect")
            else:
                conv_state.persona_data = enhanced

        # Detect and resolve follow-up queries
        query_to_process = request.message
        is_follow_up, resolved_query = ci.detect_follow_up(request.message, conv_state)
        if is_follow_up and resolved_query:
            query_to_process = resolved_query

        # KG-RAG hybrid retrieval
        context, sources, metadata = rag.retrieve_hybrid(query_to_process, club=club)

        # Build compound context
        enriched_context, sources, ci_metadata = ci.build_compound_context(
            query=query_to_process,
            base_context=context,
            base_sources=sources,
            state=conv_state
        )

        # Generator for SSE stream
        async def generate_stream():
            full_response = ""

            # Stream from AI
            for chunk in ai_response.generate_response_stream(
                query=request.message,
                context=enriched_context,
                sources=sources,
                conversation_history=history,
                club=club or "default",
                persona_data=conv_state.persona_data
            ):
                if "error" in chunk:
                    yield f"data: {json_lib.dumps({'error': chunk['error']})}\n\n"
                    return

                if "text" in chunk:
                    full_response += chunk["text"]
                    yield f"data: {json_lib.dumps({'text': chunk['text']})}\n\n"

                if chunk.get("done"):
                    # Update conversation state
                    entities = metadata.get('entities', {})
                    intent = metadata.get('kg_intent', metadata.get('intent', 'general'))
                    ci.update_conversation_state(
                        state=conv_state,
                        query=request.message,
                        entities=entities,
                        intent=intent,
                        response=full_response
                    )

                    # Update conversation history (in-memory + persist to SQLite)
                    history.append({"role": "user", "content": request.message})
                    history.append({"role": "assistant", "content": full_response})
                    conversations[conv_id] = history[-10:]
                    database.save_conversation(conv_id, conversations[conv_id])

                    # Send done event with metadata
                    yield f"data: {json_lib.dumps({'done': True, 'conversation_id': conv_id})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except Exception as e:
        async def error_stream():
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream"
        )


# ============================================
# FAN ENHANCEMENTS ENDPOINTS
# ============================================

@app.get("/api/v1/fan/{club}/mood")
async def get_fan_mood(club: str):
    """Get current mood for a club based on recent results."""
    if club not in VALID_CLUBS or club == "analyst":
        raise HTTPException(status_code=404, detail=f"Unknown club: {club}")

    mood_data = fan_enhancements.calculate_mood_from_results(club)
    dialect = fan_enhancements.get_dialect_config(club)

    return {
        "club": club,
        "mood": mood_data,
        "dialect": dialect.get("name") if dialect else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/fan/{club}/check-rivalry")
async def check_rivalry(club: str, message: str = Body("", embed=True)):
    """Check if a message triggers rivalry detection."""
    if club not in VALID_CLUBS or club == "analyst":
        raise HTTPException(status_code=404, detail=f"Unknown club: {club}")

    rivalry = fan_enhancements.detect_rivalry(club, message)

    return {
        "club": club,
        "message": message,
        "rivalry_detected": rivalry is not None,
        "rivalry": rivalry,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/fan/{club}/full")
async def get_fan_enhancements(club: str, message: str = ""):
    """Get full fan enhancements including mood, rivalry (if message provided), and dialect."""
    if club not in VALID_CLUBS or club == "analyst":
        raise HTTPException(status_code=404, detail=f"Unknown club: {club}")

    enhanced = fan_enhancements.get_enhanced_persona(club, message)

    return {
        "club": club,
        "mood": enhanced.get("mood"),
        "rivalry": enhanced.get("rivalry"),
        "dialect": enhanced.get("dialect"),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/fan/{club}/4d-state")
async def get_fan_4d_state(club: str, message: str = ""):
    """
    Get computed 4D persona state for a club.

    The 4D Position: P(t) = (x, y, z, t)
    - X (Emotional): Mood computed from live match results
    - Y (Relational): Rivalry activation from KG
    - Z (Linguistic): Regional dialect
    - T (Temporal): Conversation trajectory

    Requires USE_4D_PERSONA=True in config.py
    """
    if club not in VALID_CLUBS or club == "analyst":
        raise HTTPException(status_code=404, detail=f"Unknown club: {club}")

    if not USE_4D_PERSONA:
        return {
            "club": club,
            "enabled": False,
            "message": "4D Persona is disabled. Set USE_4D_PERSONA=True in config.py",
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        bridge = get_persona_bridge()
        state_4d = bridge.compute_4d_state(
            club_id=club,
            user_message=message or "Hello",
            conversation_history=[]
        )

        # Get conversation topics
        topics = bridge.get_conversation_topics(club)

        # Get ground truth for additional context
        ground_truth = bridge.get_ground_truth(club)

        return {
            "club": club,
            "enabled": True,
            "position_4d": {
                "x": {
                    "dimension": "emotional",
                    "mood": state_4d.x.mood,
                    "intensity": round(state_4d.x.intensity, 2),
                    "reason": state_4d.x.reason
                },
                "y": {
                    "dimension": "relational",
                    "activated": state_4d.y.activated,
                    "relation_type": state_4d.y.relation_type if state_4d.y.activated else None,
                    "target": state_4d.y.target if state_4d.y.activated else None,
                    "intensity": round(state_4d.y.intensity, 2) if state_4d.y.activated else 0
                },
                "z": {
                    "dimension": "linguistic",
                    "dialect": state_4d.z.dialect,
                    "distinctiveness": round(state_4d.z.distinctiveness, 2)
                },
                "t": {
                    "dimension": "temporal",
                    "step": state_4d.t.step,
                    "momentum": state_4d.t.momentum
                }
            },
            "topics": topics,
            "form_string": ground_truth.get("form_string", ""),
            "recent_result": ground_truth.get("recent_results", [{}])[0] if ground_truth.get("recent_results") else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        # Fallback to legacy if 4D fails
        print(f"[4D] Error computing state: {e}")
        return {
            "club": club,
            "enabled": True,
            "error": str(e),
            "fallback": True,
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================
# TEAMS ENDPOINTS
# ============================================

@app.get("/api/v1/teams")
async def list_teams(
    league: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List teams with optional filtering."""
    teams = database.get_teams(limit=limit, offset=offset, league=league)
    return ApiResponse(
        data=teams,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/teams/{team_id}")
async def get_team(team_id: int):
    """Get team by ID."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse(data=team)


@app.get("/api/v1/teams/{team_id}/squad")
async def get_team_squad(team_id: int):
    """Get team's player squad."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    players = database.get_players(team_id=team_id, limit=50)
    return ApiResponse(data={"team": team, "players": players})


@app.get("/api/v1/teams/{team_id}/fixtures")
async def get_team_fixtures(team_id: int, limit: int = 5):
    """Get team's upcoming fixtures."""
    fixtures = database.get_upcoming_games(team_id, limit=limit)
    return ApiResponse(data=fixtures)


@app.get("/api/v1/teams/{team_id}/results")
async def get_team_results(team_id: int, limit: int = 5):
    """Get team's recent results."""
    results = database.get_recent_games(team_id, limit=limit)
    return ApiResponse(data=results)


# ============================================
# PLAYERS ENDPOINTS
# ============================================

@app.get("/api/v1/players")
async def list_players(
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List players with optional filtering."""
    players = database.get_players(
        limit=limit, offset=offset,
        team_id=team_id, position=position
    )
    return ApiResponse(
        data=players,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/players/{player_id}")
async def get_player(player_id: int):
    """Get player by ID."""
    player = database.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return ApiResponse(data=player)


@app.get("/api/v1/players/{player_id}/stats")
async def get_player_stats(player_id: int, season: Optional[str] = None):
    """Get player statistics."""
    player = database.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stats = database.get_player_stats(player_id, season)
    return ApiResponse(data={"player": player, "stats": stats})


@app.get("/api/v1/players/search")
async def search_players(q: str, limit: int = 10):
    """Search players by name."""
    players = database.search_players(q, limit=limit)
    return ApiResponse(data=players)


# ============================================
# GAMES ENDPOINTS
# ============================================

@app.get("/api/v1/games")
async def list_games(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List games with optional filtering."""
    games = database.get_games(
        limit=limit, offset=offset,
        team_id=team_id, status=status,
        date_from=date_from, date_to=date_to
    )
    return ApiResponse(
        data=games,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/games/live")
async def get_live_games():
    """Get currently live games."""
    games = database.get_games(status="live", limit=20)
    return ApiResponse(data=games)


@app.get("/api/v1/games/today")
async def get_today_games():
    """Get today's games."""
    today = datetime.now().strftime("%Y-%m-%d")
    games = database.get_games(date_from=today, date_to=today, limit=50)
    return ApiResponse(data=games)


@app.get("/api/v1/games/upcoming")
async def get_upcoming_games(limit: int = 20):
    """Get upcoming games."""
    games = database.get_games(status="scheduled", limit=limit)
    return ApiResponse(data=games)


@app.get("/api/v1/games/{game_id}")
async def get_game(game_id: int):
    """Get game by ID with events."""
    game = database.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return ApiResponse(data=game)


# ============================================
# INJURIES ENDPOINTS
# ============================================

@app.get("/api/v1/injuries")
async def list_injuries(
    team_id: Optional[int] = None,
    status: str = "active",
    limit: int = 50
):
    """List injuries with optional filtering."""
    injuries = database.get_injuries(team_id=team_id, status=status, limit=limit)
    return ApiResponse(data=injuries)


@app.get("/api/v1/injuries/active")
async def get_active_injuries(limit: int = 50):
    """Get all active injuries."""
    injuries = database.get_injuries(status="active", limit=limit)
    return ApiResponse(data=injuries)


@app.get("/api/v1/injuries/team/{team_id}")
async def get_team_injuries(team_id: int):
    """Get injuries for a specific team."""
    injuries = database.get_injuries(team_id=team_id, status="active")
    return ApiResponse(data=injuries)


# ============================================
# TRANSFERS ENDPOINTS
# ============================================

@app.get("/api/v1/transfers")
async def list_transfers(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List transfers with optional filtering."""
    transfers = database.get_transfers(team_id=team_id, status=status, limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/recent")
async def get_recent_transfers(limit: int = 20):
    """Get recent completed transfers."""
    transfers = database.get_transfers(status="completed", limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/rumors")
async def get_transfer_rumors(limit: int = 20):
    """Get transfer rumors."""
    transfers = database.get_transfers(status="rumor", limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/team/{team_id}")
async def get_team_transfers(team_id: int):
    """Get transfers for a specific team."""
    transfers = database.get_transfers(team_id=team_id, limit=50)
    return ApiResponse(data=transfers)


# ============================================
# STANDINGS ENDPOINTS
# ============================================

@app.get("/api/v1/standings/{league}")
async def get_standings(league: str, season: str = "2024-25"):
    """Get league standings."""
    standings = database.get_standings(league, season)
    return ApiResponse(data=standings)


# ============================================
# LIVE API ENDPOINTS (football-data.org)
# ============================================

@app.get("/api/v1/live/standings")
async def get_live_standings():
    """Get live Premier League standings from football-data.org."""
    try:
        from football_api import get_football_api
        api = get_football_api()
        standings = api.get_standings("PL")
        return ApiResponse(data=standings)
    except Exception as e:
        return ApiResponse(data=[], error=str(e))


@app.get("/api/v1/live/fixtures")
async def get_live_fixtures(days: int = 7):
    """Get upcoming fixtures from football-data.org."""
    try:
        from football_api import get_football_api
        api = get_football_api()
        fixtures = api.get_upcoming_fixtures(days_ahead=days)
        return ApiResponse(data=fixtures)
    except Exception as e:
        return ApiResponse(data=[], error=str(e))


@app.get("/api/v1/live/results")
async def get_live_results(days: int = 7):
    """Get recent results from football-data.org."""
    try:
        from football_api import get_football_api
        api = get_football_api()
        results = api.get_recent_results(days_back=days)
        return ApiResponse(data=results)
    except Exception as e:
        return ApiResponse(data=[], error=str(e))


@app.get("/api/v1/live/team/{team_name}")
async def get_live_team_context(team_name: str):
    """Get live team context (position, form, next match) from football-data.org."""
    try:
        from football_api import get_football_api
        api = get_football_api()
        context = api.get_team_context(team_name)
        return ApiResponse(data=context)
    except Exception as e:
        return ApiResponse(data={}, error=str(e))


# ============================================
# FOOTBALL ORACLE ENDPOINTS
# ============================================

@app.get("/api/v1/oracle/predict")
async def oracle_predict(
    home_team: str = Query(..., description="Home team name"),
    away_team: str = Query(..., description="Away team name"),
    home_odds: Optional[float] = Query(None, description="Betting odds for home win"),
    draw_odds: Optional[float] = Query(None, description="Betting odds for draw"),
    away_odds: Optional[float] = Query(None, description="Betting odds for away win")
):
    """
    Get match prediction from the Football Oracle.

    The Oracle uses 230K+ historical matches to predict outcomes with
    calibrated probabilities based on:
    - ELO power ratings
    - Form differentials
    - Head-to-head history
    - Betting odds calibration
    - Modern era adjustments

    Returns three-way probabilities (home/draw/away) with confidence level.
    """
    try:
        from predictor.statistical_predictor import FootballOracle
        oracle = FootballOracle()
        prediction = oracle.predict(home_team, away_team, home_odds, draw_odds, away_odds)
        return ApiResponse(data=prediction.to_dict())
    except Exception as e:
        return ApiResponse(data={}, error=str(e))


@app.get("/api/v1/oracle/upcoming")
async def oracle_upcoming():
    """
    Get Oracle predictions for upcoming Premier League fixtures.

    Fetches next week's fixtures from live API and generates predictions.
    """
    try:
        from football_api import get_football_api
        from predictor.statistical_predictor import FootballOracle

        api = get_football_api()
        oracle = FootballOracle()

        fixtures = api.get_upcoming_fixtures(days=7)
        predictions = []

        for fixture in fixtures.get("matches", [])[:10]:  # Limit to 10
            home = fixture.get("home_team", "")
            away = fixture.get("away_team", "")
            if home and away:
                pred = oracle.predict(home, away)
                predictions.append({
                    "fixture": f"{home} vs {away}",
                    "date": fixture.get("date", ""),
                    "prediction": pred.to_dict()
                })

        return ApiResponse(data={"predictions": predictions, "count": len(predictions)})
    except Exception as e:
        return ApiResponse(data={"predictions": [], "count": 0}, error=str(e))


@app.get("/api/v1/oracle/accuracy")
async def oracle_accuracy():
    """
    Get Football Oracle accuracy statistics from backtesting.

    Returns accuracy breakdown by outcome type (home/draw/away).
    """
    try:
        from predictor.statistical_predictor import backtest_oracle, DB_PATH

        # Get last 100 matches for quick stats
        results = backtest_oracle(DB_PATH, "2024-08-01", "2024-12-31")

        if "error" in results:
            return ApiResponse(data={}, error=results["error"])

        return ApiResponse(data={
            "total_matches": results["total"],
            "overall_accuracy": round(results["overall_accuracy"] * 100, 1),
            "home_win_accuracy": round(results["home_accuracy"] * 100, 1),
            "draw_accuracy": round(results["draw_accuracy"] * 100, 1),
            "away_win_accuracy": round(results["away_accuracy"] * 100, 1),
            "breakdown": {
                "home_wins": f"{results['home_win_correct']}/{results['home_win_total']}",
                "draws": f"{results['draw_correct']}/{results['draw_total']}",
                "away_wins": f"{results['away_win_correct']}/{results['away_win_total']}"
            }
        })
    except Exception as e:
        return ApiResponse(data={}, error=str(e))


# ============================================
# LEGENDS ENDPOINTS
# ============================================

@app.get("/api/v1/legends")
async def list_legends(
    team_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=100)
):
    """List club legends with optional team filtering."""
    legends = database.get_legends(team_id=team_id, limit=limit)
    return ApiResponse(data=legends)


@app.get("/api/v1/legends/{legend_id}")
async def get_legend(legend_id: int):
    """Get legend by ID."""
    legend = database.get_legend(legend_id)
    if not legend:
        raise HTTPException(status_code=404, detail="Legend not found")
    return ApiResponse(data=legend)


@app.get("/api/v1/legends/search/{query}")
async def search_legends(query: str, limit: int = 10):
    """Search legends by name."""
    legends = database.search_legends(query, limit=limit)
    return ApiResponse(data=legends)


@app.get("/api/v1/teams/{team_id}/legends")
async def get_team_legends(team_id: int):
    """Get all legends for a team."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    legends = database.get_legends(team_id=team_id)
    return ApiResponse(data={"team": team, "legends": legends})


# ============================================
# CLUB PERSONALITY ENDPOINTS
# ============================================

@app.get("/api/v1/teams/{team_id}/identity")
async def get_team_identity(team_id: int):
    """Get club identity/personality."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    identity = database.get_club_identity(team_id)
    return ApiResponse(data={"team": team, "identity": identity})


@app.get("/api/v1/teams/{team_id}/moments")
async def get_team_moments(team_id: int, limit: int = 20):
    """Get iconic moments for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    moments = database.get_club_moments(team_id, limit=limit)
    return ApiResponse(data={"team": team, "moments": moments})


@app.get("/api/v1/teams/{team_id}/rivalries")
async def get_team_rivalries(team_id: int):
    """Get rivalries for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    rivalries = database.get_club_rivalries(team_id)
    return ApiResponse(data={"team": team, "rivalries": rivalries})


@app.get("/api/v1/teams/{team_id}/mood")
async def get_team_mood(team_id: int):
    """Get current mood for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    mood = database.get_club_mood(team_id)
    return ApiResponse(data={"team": team, "mood": mood})


@app.get("/api/v1/teams/{team_id}/personality")
async def get_team_full_personality(team_id: int):
    """Get complete club personality (identity + mood + rivalries + moments)."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return ApiResponse(data={
        "team": team,
        "identity": database.get_club_identity(team_id),
        "mood": database.get_club_mood(team_id),
        "rivalries": database.get_club_rivalries(team_id),
        "moments": database.get_club_moments(team_id, limit=5),
        "legends": database.get_legends(team_id=team_id, limit=5)
    })


# ============================================
# FAN PERSONA ENDPOINTS
# ============================================

# City derby mappings (battle of cities)
CITY_DERBIES = {
    "london": {
        "name": "London Derbies",
        "teams": ["Arsenal", "Chelsea", "Tottenham", "West Ham"],
        "key_matches": [
            {"name": "North London Derby", "teams": ["Arsenal", "Tottenham"], "intensity": 10},
            {"name": "West London Derby", "teams": ["Chelsea", "West Ham"], "intensity": 7},
            {"name": "London Derby", "teams": ["Arsenal", "Chelsea"], "intensity": 8}
        ],
        "description": "The capital's football war - 4 clubs, endless bragging rights"
    },
    "manchester": {
        "name": "Manchester Derby",
        "teams": ["Manchester United", "Manchester City"],
        "key_matches": [
            {"name": "Manchester Derby", "teams": ["Manchester United", "Manchester City"], "intensity": 10}
        ],
        "description": "Red vs Blue - the soul of Manchester"
    },
    "merseyside": {
        "name": "Merseyside Derby",
        "teams": ["Liverpool", "Everton"],
        "key_matches": [
            {"name": "Merseyside Derby", "teams": ["Liverpool", "Everton"], "intensity": 10}
        ],
        "description": "The friendly enemy - families divided across Stanley Park"
    },
    "tyne-wear": {
        "name": "Tyne-Wear Derby",
        "teams": ["Newcastle"],
        "key_matches": [
            {"name": "Tyne-Wear Derby (historic)", "teams": ["Newcastle", "Sunderland"], "intensity": 10}
        ],
        "description": "Geordies vs Mackems - the North East divide (Sunderland in Championship)"
    }
}

# Banter templates between rival clubs
CLUB_BANTER = {
    ("arsenal", "tottenham"): {
        "arsenal_says": "What's it like living in our shadow? 13 league titles vs 2... 🔴",
        "tottenham_says": "Bottled another season yet? At least we have a proper stadium! ⚪",
        "neutral": "The North London Derby - where history (Arsenal) meets hope (Spurs)"
    },
    ("arsenal", "chelsea"): {
        "arsenal_says": "Invincibles > Oil money. Some things can't be bought 🔴",
        "chelsea_says": "2 Champions Leagues and counting. Where's yours? 💙",
        "neutral": "London's biggest clash - class vs cash"
    },
    ("manchester_united", "manchester_city"): {
        "manchester_united_says": "20 league titles, 3 European Cups. History > Money 🔴",
        "manchester_city_says": "Treble winners 2023. Living in the present, not the past 💙",
        "neutral": "Red vs Blue Manchester - legacy meets new money"
    },
    ("manchester_united", "liverpool"): {
        "manchester_united_says": "Still more league titles mate. 20 > 19 🔴",
        "liverpool_says": "6 European Cups > 3. When it matters most... 🔴",
        "neutral": "England's biggest rivalry - the Northwest Corridor of hate"
    },
    ("liverpool", "everton"): {
        "liverpool_says": "6 European Cups vs 0. Same city, different class 🔴",
        "everton_says": "We're the original Merseyside club. 9 league titles, don't forget! 💙",
        "neutral": "The friendly derby - families split across Stanley Park"
    },
    ("chelsea", "west_ham"): {
        "chelsea_says": "West London > East London. Trophies prove it 💙",
        "west_ham_says": "We've got soul, you've got oil money. COYI! ⚒️",
        "neutral": "London class warfare in football form"
    },
    ("tottenham", "west_ham"): {
        "tottenham_says": "At least we regularly finish in European spots... ⚪",
        "west_ham_says": "At least we've won something recently! 2023 Conference League! ⚒️",
        "neutral": "East meets North - London's working class derby"
    },
    ("newcastle", "everton"): {
        "newcastle_says": "Back in the Champions League! Where's your European football? ⚫⚪",
        "everton_says": "At least we don't need Saudi money to compete! 💙",
        "neutral": "Two passionate fanbases, two clubs rebuilding"
    }
}


@app.get("/api/v1/clubs")
async def list_clubs():
    """
    List available club personas (simplified format for frontend).
    Returns club_key and display name.
    """
    clubs = [
        {"id": "arsenal", "name": "Arsenal"},
        {"id": "chelsea", "name": "Chelsea"},
        {"id": "manchester_united", "name": "Manchester United"},
        {"id": "liverpool", "name": "Liverpool"},
        {"id": "manchester_city", "name": "Manchester City"},
        {"id": "tottenham", "name": "Tottenham"},
        {"id": "newcastle", "name": "Newcastle United"},
        {"id": "west_ham", "name": "West Ham United"},
        {"id": "everton", "name": "Everton"},
        {"id": "brighton", "name": "Brighton"},
        {"id": "aston_villa", "name": "Aston Villa"},
        {"id": "wolves", "name": "Wolves"},
        {"id": "crystal_palace", "name": "Crystal Palace"},
        {"id": "fulham", "name": "Fulham"},
        {"id": "nottingham_forest", "name": "Nottingham Forest"},
        {"id": "brentford", "name": "Brentford"},
        {"id": "bournemouth", "name": "Bournemouth"},
        {"id": "leicester", "name": "Leicester City"},
        {"id": "analyst", "name": "The Analyst (Neutral)"},
    ]
    return ApiResponse(data=clubs)


@app.get("/api/v1/personas")
async def list_personas():
    """
    List all available fan personas with their current mood.
    Useful for frontend display and persona selection.
    """
    personas = []

    # Team ID mappings (verified from database)
    team_ids = {
        "arsenal": 3,
        "chelsea": 4,
        "manchester_united": 5,
        "liverpool": 2,
        "manchester_city": 1,
        "tottenham": 6,
        "newcastle": 7,
        "west_ham": 10,
        "everton": 16
    }

    for club_key, team_id in team_ids.items():
        team = database.get_team(team_id)
        identity = database.get_club_identity(team_id)
        mood = database.get_club_mood(team_id)

        personas.append({
            "club_key": club_key,
            "team_id": team_id,
            "display_name": team["name"] if team else club_key.replace("_", " ").title(),
            "identity": identity,
            "mood": mood
        })

    return ApiResponse(data={
        "personas": personas,
        "total": len(personas)
    })


@app.get("/api/v1/derby/{city}")
async def get_city_derby(city: str):
    """
    Get derby information for a city.
    Cities: london, manchester, merseyside, tyne-wear
    """
    city_lower = city.lower().replace(" ", "-")

    if city_lower not in CITY_DERBIES:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city}' not found. Available: {list(CITY_DERBIES.keys())}"
        )

    derby_info = CITY_DERBIES[city_lower]

    # Enrich with team data
    enriched_teams = []
    for team_name in derby_info["teams"]:
        teams = database.search_teams(team_name, limit=1)
        if teams:
            team = teams[0]
            mood = database.get_club_mood(team["id"])
            enriched_teams.append({
                "team": team,
                "mood": mood
            })

    return ApiResponse(data={
        "city": city_lower,
        "derby": derby_info,
        "teams": enriched_teams
    })


@app.get("/api/v1/banter/{team1}/{team2}")
async def get_banter(team1: str, team2: str):
    """
    Get banter between two rival clubs.
    Returns what each fan would say about the other.
    """
    t1 = team1.lower().replace("-", "_").replace(" ", "_")
    t2 = team2.lower().replace("-", "_").replace(" ", "_")

    # Try both orderings
    banter = CLUB_BANTER.get((t1, t2)) or CLUB_BANTER.get((t2, t1))

    if not banter:
        # Generate generic banter if not pre-defined
        return ApiResponse(data={
            "team1": t1,
            "team2": t2,
            "banter": {
                f"{t1}_says": f"We're better than {t2.replace('_', ' ').title()}!",
                f"{t2}_says": f"Please, {t1.replace('_', ' ').title()} wish they were us!",
                "neutral": "A classic Premier League rivalry"
            },
            "is_historic_rivalry": False
        })

    return ApiResponse(data={
        "team1": t1,
        "team2": t2,
        "banter": banter,
        "is_historic_rivalry": True
    })


# ============================================
# SEARCH ENDPOINT
# ============================================

@app.get("/api/v1/search")
async def search(
    q: str,
    type: str = "all",
    limit: int = 10
):
    """Unified search across all entities."""
    if type == "all":
        results = database.search_all(q, limit=limit)
    elif type == "players":
        results = {"players": database.search_players(q, limit=limit)}
    elif type == "teams":
        results = {"teams": database.search_teams(q, limit=limit)}
    elif type == "news":
        results = {"news": database.search_news(q, limit=limit)}
    else:
        results = database.search_all(q, limit=limit)

    total = sum(len(v) for v in results.values())

    return ApiResponse(
        data=SearchResults(query=q, results=results, total=total)
    )


# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.get("/api/v1/admin/stats")
async def get_db_stats():
    """Get database statistics."""
    stats = database.get_db_stats()
    return ApiResponse(data=stats)


# ============================================
# ANALYTICS ENDPOINTS (CP6)
# ============================================

@app.get("/api/v1/analytics")
async def get_analytics(days: int = Query(default=7, ge=1, le=30)):
    """Get query analytics summary."""
    try:
        summary = database.get_analytics_summary(days=days)
        return ApiResponse(data=summary)
    except Exception as e:
        # Table might not exist yet
        return ApiResponse(data={
            "error": "Analytics not initialized",
            "message": str(e)
        })


@app.get("/api/v1/analytics/recent")
async def get_recent_analytics(limit: int = Query(default=20, ge=1, le=100)):
    """Get recent queries for debugging."""
    try:
        queries = database.get_recent_queries(limit=limit)
        return ApiResponse(data=queries)
    except Exception:
        return ApiResponse(data=[])


@app.get("/api/v1/analytics/hot")
async def get_hot_analytics(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get most common query patterns."""
    try:
        hot = database.get_hot_queries(days=days, limit=limit)
        return ApiResponse(data=hot)
    except Exception:
        return ApiResponse(data=[])


# ============================================
# KNOWLEDGE GRAPH VISUALIZATION (CP7)
# ============================================

# Static file route for KG viewer
STATIC_DIR = Path(__file__).parent / "static"

@app.get("/kg-viewer")
async def kg_viewer():
    """Serve the Knowledge Graph visualization page."""
    viewer_path = STATIC_DIR / "kg_viewer.html"
    if viewer_path.exists():
        return FileResponse(viewer_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="KG Viewer not found")


@app.get("/api/v1/graph")
async def get_full_graph():
    """
    Get full Knowledge Graph in vis.js format.

    Returns nodes, edges, and stats for visualization.
    """
    try:
        graph = database.export_kg_to_vis_json()
        return ApiResponse(data=graph)
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "KG_EXPORT_ERROR", "message": str(e)}
        )


@app.get("/api/v1/graph/subgraph/{node_id}")
async def get_subgraph(
    node_id: str,
    depth: int = Query(default=1, ge=0, le=3)
):
    """
    Get subgraph centered on a specific node.

    Useful for focused visualizations.
    - depth=0: Just the center node
    - depth=1: Center + immediate connections
    - depth=2: Two hops out
    - depth=3: Three hops (max)
    """
    try:
        # Handle both integer and string node IDs
        try:
            node_id_int = int(node_id)
            node_id_actual = str(node_id_int)
        except ValueError:
            node_id_actual = node_id

        subgraph = database.export_kg_subgraph(node_id_actual, depth=depth)
        return ApiResponse(data=subgraph)
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "SUBGRAPH_ERROR", "message": str(e)}
        )


@app.get("/api/v1/graph/team/{team_id}")
async def get_team_graph(
    team_id: int,
    depth: int = Query(default=1, ge=0, le=3)
):
    """
    Get subgraph for a team by team ID.

    Convenience endpoint that looks up team's KG node.
    """
    try:
        # Get team name
        team = database.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Find KG node
        node = database.find_kg_node_by_name(team["name"])
        if not node:
            return ApiResponse(data={
                "nodes": [],
                "edges": [],
                "message": f"Team {team['name']} not in Knowledge Graph"
            })

        subgraph = database.export_kg_subgraph(node["node_id"], depth=depth)
        subgraph["team"] = team
        return ApiResponse(data=subgraph)
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "TEAM_GRAPH_ERROR", "message": str(e)}
        )


# ============================================
# PREDICTOR ENDPOINTS (The Analyst)
# ============================================

# Initialize prediction engine (with live data if APIs configured)
prediction_engine = None

def get_prediction_engine():
    """Lazy initialization of prediction engine."""
    global prediction_engine
    if prediction_engine is None:
        try:
            prediction_engine = PredictionEngine(use_live_data=True)
        except Exception as e:
            print(f"Error initializing prediction engine: {e}")
            prediction_engine = PredictionEngine(use_live_data=False)
    return prediction_engine


# Tri-Lens Predictor (xG + Oracle + Upset Detection)
tri_lens_predictor = None

def get_tri_lens_predictor():
    """Lazy initialization of Tri-Lens predictor."""
    global tri_lens_predictor
    if tri_lens_predictor is None:
        try:
            tri_lens_predictor = TriLensPredictor()
            print("Tri-Lens Predictor initialized: 53.2% accuracy, 17.3% draw detection")
        except Exception as e:
            print(f"Error initializing Tri-Lens predictor: {e}")
            tri_lens_predictor = None
    return tri_lens_predictor


# Dixon-Coles + Bookmaker Ensemble (upgraded predictor)
_dixon_coles_model = None

def get_dixon_coles_model():
    """Lazy initialization of Dixon-Coles model. Fits on 3 seasons of PL data."""
    global _dixon_coles_model
    if _dixon_coles_model is None:
        try:
            from predictor.dixon_coles import fit_model
            _dixon_coles_model = fit_model(division="E0", seasons_back=3)
            print(f"Dixon-Coles fitted: {_dixon_coles_model.n_matches} matches, "
                  f"rho={_dixon_coles_model.rho:.4f}, "
                  f"{len(_dixon_coles_model.teams)} teams")
        except Exception as e:
            print(f"Error fitting Dixon-Coles: {e}")
            _dixon_coles_model = None
    return _dixon_coles_model


from pydantic import BaseModel

class TriLensRequest(BaseModel):
    home_team: str
    away_team: str
    home_odds: float = None
    draw_odds: float = None
    away_odds: float = None


@app.post("/api/v1/tri-lens/predict")
async def tri_lens_predict(request: TriLensRequest):
    """
    Generate match prediction using the Tri-Lens Predictor.

    Combines three prediction lenses:
    - Poisson (xG) - 55% weight, best probability calibration
    - Oracle (ELO + patterns) - 45% weight, historical patterns
    - Upset Detector - conditional draw boost when signals align

    Returns: probabilities, xG, likely scores, upset risk, lens agreement
    """
    try:
        predictor = get_tri_lens_predictor()
        if predictor is None:
            raise HTTPException(status_code=500, detail="Predictor not available")

        pred = predictor.predict(
            request.home_team,
            request.away_team,
            request.home_odds,
            request.draw_odds,
            request.away_odds
        )

        return ApiResponse(data={
            "home_team": pred.home_team,
            "away_team": pred.away_team,
            "prediction": pred.prediction,
            "confidence": pred.confidence,
            "probabilities": {
                "home_win": round(pred.final_probs[0], 3),
                "draw": round(pred.final_probs[1], 3),
                "away_win": round(pred.final_probs[2], 3)
            },
            "expected_goals": {
                "home": round(pred.home_xg, 2),
                "away": round(pred.away_xg, 2)
            },
            "likely_scores": [
                {"score": s[0], "probability": round(s[1], 3)}
                for s in pred.likely_scores[:5]
            ],
            "upset_analysis": {
                "risk": round(pred.upset_risk, 2),
                "patterns": pred.upset_patterns,
                "draw_boost_applied": pred.draw_boost_applied
            },
            "lens_agreement": pred.lens_agreement,
            "model": "Tri-Lens v1.0 (53.2% overall, 17.3% draw)"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# ── Dixon-Coles + Bookmaker Ensemble (v2 Predictor) ──

@app.get("/api/v1/predict/v2/{home_team}/{away_team}")
async def predict_v2(home_team: str, away_team: str):
    """
    V2 Match Prediction — Dixon-Coles + Bookmaker Odds ensemble.

    53.9% accuracy, 50% draw precision (backtested on 2024-25 PL).
    No manual favorite/underdog needed — the model determines it from data.
    """
    from predictor.dixon_coles import predict as dc_predict, odds_to_probabilities, get_match_odds

    model = get_dixon_coles_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Dixon-Coles model not available")

    # Resolve team names to match_history format
    db_home = fan_enhancements.CLUB_TO_DB_NAME.get(
        home_team.lower().replace(" ", "_"), home_team
    )
    db_away = fan_enhancements.CLUB_TO_DB_NAME.get(
        away_team.lower().replace(" ", "_"), away_team
    )

    # Dixon-Coles prediction
    dc = dc_predict(model, db_home, db_away)

    # Try to get bookmaker odds
    odds = get_match_odds(db_home, db_away)
    has_odds = odds is not None

    if has_odds:
        bk_h, bk_d, bk_a = odds_to_probabilities(*odds)
        # Ensemble: 40% DC + 60% Bookmaker
        ens_h = 0.40 * dc["home_win"] + 0.60 * bk_h
        ens_d = 0.40 * dc["draw"] + 0.60 * bk_d
        ens_a = 0.40 * dc["away_win"] + 0.60 * bk_a

        # Draw threshold
        max_p = max(ens_h, ens_d, ens_a)
        if ens_d >= 0.245 and ens_d >= max_p * 0.75:
            prediction = "Draw"
            confidence = ens_d
        elif ens_h >= ens_a:
            prediction = f"{home_team} Win"
            confidence = ens_h
        else:
            prediction = f"{away_team} Win"
            confidence = ens_a
    else:
        ens_h, ens_d, ens_a = dc["home_win"], dc["draw"], dc["away_win"]
        bk_h = bk_d = bk_a = None
        max_p = max(ens_h, ens_d, ens_a)
        if dc["home_win"] >= dc["away_win"]:
            prediction = f"{home_team} Win"
            confidence = dc["home_win"]
        else:
            prediction = f"{away_team} Win"
            confidence = dc["away_win"]

    return {
        "success": True,
        "data": {
            "home_team": home_team,
            "away_team": away_team,
            "prediction": prediction,
            "confidence": round(confidence, 3),
            "probabilities": {
                "home_win": round(ens_h, 3),
                "draw": round(ens_d, 3),
                "away_win": round(ens_a, 3),
            },
            "expected_goals": {
                "home": dc["expected_home_goals"],
                "away": dc["expected_away_goals"],
            },
            "most_likely_score": f"{dc['most_likely_score'][0]}-{dc['most_likely_score'][1]}",
            "dixon_coles": {
                "home_win": dc["home_win"],
                "draw": dc["draw"],
                "away_win": dc["away_win"],
                "rho": dc["rho"],
            },
            "bookmaker": {
                "available": has_odds,
                "home_win": round(bk_h, 3) if bk_h else None,
                "draw": round(bk_d, 3) if bk_d else None,
                "away_win": round(bk_a, 3) if bk_a else None,
                "raw_odds": {"home": odds[0], "draw": odds[1], "away": odds[2]} if odds else None,
            },
            "model": "Dixon-Coles + Bookmaker v2 (53.9% accuracy, 50% draw precision)",
        },
    }


@app.get("/api/v1/predict/v2/upcoming")
async def predict_upcoming_v2():
    """
    V2 predictions for all upcoming fixtures using Dixon-Coles + Bookmaker ensemble.
    """
    from predictor.dixon_coles import predict as dc_predict, odds_to_probabilities

    model = get_dixon_coles_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Dixon-Coles model not available")

    # Get upcoming fixtures from database
    import sqlite3 as _sql
    conn = _sql.connect(database.DB_PATH)
    conn.row_factory = _sql.Row
    fixtures = conn.execute("""
        SELECT g.date, h.name AS home, a.name AS away
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.status = 'scheduled' AND g.date >= date('now')
        ORDER BY g.date
        LIMIT 20
    """).fetchall()
    conn.close()

    predictions = []
    for f in fixtures:
        db_home = fan_enhancements.CLUB_TO_DB_NAME.get(
            f["home"].lower().replace(" ", "_"),
            f["home"]
        )
        db_away = fan_enhancements.CLUB_TO_DB_NAME.get(
            f["away"].lower().replace(" ", "_"),
            f["away"]
        )

        # For name resolution, try direct match too
        for club_key, db_name in fan_enhancements.CLUB_TO_DB_NAME.items():
            if db_name.lower() == f["home"].lower() or f["home"].lower() in db_name.lower():
                db_home = db_name
                break
        for club_key, db_name in fan_enhancements.CLUB_TO_DB_NAME.items():
            if db_name.lower() == f["away"].lower() or f["away"].lower() in db_name.lower():
                db_away = db_name
                break

        dc = dc_predict(model, db_home, db_away)

        # Determine prediction
        if dc["home_win"] > dc["away_win"] and dc["home_win"] > dc["draw"]:
            pred_label = f"{f['home']} Win"
        elif dc["away_win"] > dc["home_win"] and dc["away_win"] > dc["draw"]:
            pred_label = f"{f['away']} Win"
        else:
            pred_label = "Draw"

        predictions.append({
            "date": f["date"],
            "home_team": f["home"],
            "away_team": f["away"],
            "prediction": pred_label,
            "probabilities": {
                "home_win": dc["home_win"],
                "draw": dc["draw"],
                "away_win": dc["away_win"],
            },
            "expected_goals": {
                "home": dc["expected_home_goals"],
                "away": dc["expected_away_goals"],
            },
            "most_likely_score": f"{dc['most_likely_score'][0]}-{dc['most_likely_score'][1]}",
        })

    return {
        "success": True,
        "data": {
            "predictions": predictions,
            "count": len(predictions),
            "model": "Dixon-Coles v2",
        },
    }


@app.get("/api/v1/predict/v2/{home_team}/{away_team}/card")
async def predict_card(home_team: str, away_team: str):
    """
    Generate shareable prediction card data with a one-line AI take.
    Returns all data needed to render a visual card for social sharing.
    """
    from predictor.dixon_coles import predict as dc_predict, odds_to_probabilities, get_match_odds

    model = get_dixon_coles_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Predictor not available")

    db_home = fan_enhancements.CLUB_TO_DB_NAME.get(home_team.lower().replace(" ", "_"), home_team)
    db_away = fan_enhancements.CLUB_TO_DB_NAME.get(away_team.lower().replace(" ", "_"), away_team)

    dc = dc_predict(model, db_home, db_away)
    odds = get_match_odds(db_home, db_away)

    if odds:
        bk_h, bk_d, bk_a = odds_to_probabilities(*odds)
        ens_h = 0.40 * dc["home_win"] + 0.60 * bk_h
        ens_d = 0.40 * dc["draw"] + 0.60 * bk_d
        ens_a = 0.40 * dc["away_win"] + 0.60 * bk_a
    else:
        ens_h, ens_d, ens_a = dc["home_win"], dc["draw"], dc["away_win"]

    # Generate a one-line AI take
    max_p = max(ens_h, ens_d, ens_a)
    if ens_d >= 0.245 and ens_d >= max_p * 0.75:
        prediction = "Draw"
    elif ens_h >= ens_a:
        prediction = f"{home_team} Win"
    else:
        prediction = f"{away_team} Win"

    # One-liner based on the data
    xg_home = dc["expected_home_goals"]
    xg_away = dc["expected_away_goals"]
    if prediction == "Draw":
        take = f"Too close to call. Both sides creating ~{xg_home} xG — this has stalemate written all over it."
    elif ens_h > 0.55:
        take = f"Home advantage + {xg_home} xG — {home_team} should control this."
    elif ens_a > 0.55:
        take = f"{away_team} look dangerous. {xg_away} xG away from home spells trouble."
    elif max_p < 0.40:
        take = f"Tight match. Three outcomes, three real possibilities."
    else:
        winner = home_team if ens_h >= ens_a else away_team
        take = f"{winner} edge it, but don't sleep on the underdog."

    # Get next fixture date for these teams
    import sqlite3 as _sql
    conn = _sql.connect(database.DB_PATH)
    conn.row_factory = _sql.Row
    fixture = conn.execute("""
        SELECT g.date, g.time FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE h.name LIKE ? AND a.name LIKE ?
          AND g.status = 'scheduled'
        ORDER BY g.date LIMIT 1
    """, (f"%{db_home}%", f"%{db_away}%")).fetchone()
    conn.close()

    return {
        "success": True,
        "data": {
            "home_team": home_team,
            "away_team": away_team,
            "home_club_id": home_team.lower().replace(" ", "_"),
            "away_club_id": away_team.lower().replace(" ", "_"),
            "prediction": prediction,
            "probabilities": {
                "home_win": round(ens_h, 3),
                "draw": round(ens_d, 3),
                "away_win": round(ens_a, 3),
            },
            "expected_goals": {
                "home": xg_home,
                "away": xg_away,
            },
            "most_likely_score": f"{dc['most_likely_score'][0]}-{dc['most_likely_score'][1]}",
            "ai_take": take,
            "date": fixture["date"] if fixture else None,
            "time": fixture["time"] if fixture else None,
            "model": "Dixon-Coles + Bookmaker v2",
        },
    }


@app.get("/api/v1/predict/v2/backtest")
async def predict_backtest():
    """Run Dixon-Coles backtest and return accuracy metrics."""
    from predictor.dixon_coles import backtest as dc_backtest
    results = dc_backtest(test_season="2024", train_seasons=3)
    return {"success": True, "data": results}


@app.post("/api/v1/predict")
async def predict_match(
    home_team: str,
    away_team: str,
    favorite: str,
    underdog: str,
    match_date: str = None
):
    """
    Generate match prediction using manual data.

    The Analyst combines:
    - Side A: Favorite weakness factors (A01-A15)
    - Side B: Underdog strength factors (B01-B15)
    - Third Knowledge: Hidden interaction patterns

    Returns upset probability with confidence and explanation.
    """
    try:
        engine = get_prediction_engine()

        if not match_date:
            match_date = datetime.now().strftime("%Y-%m-%d")

        # Use empty match_data (will use defaults)
        prediction = engine.analyze_match(
            home_team=home_team,
            away_team=away_team,
            favorite=favorite,
            underdog=underdog,
            match_date=match_date,
            match_data={}
        )

        return ApiResponse(data=engine.to_dict(prediction))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/api/v1/predict/live")
async def predict_match_live(
    home_team: str,
    away_team: str,
    favorite: str,
    underdog: str,
    match_date: str = None
):
    """
    Generate match prediction using LIVE data from external APIs.

    Fetches real-time:
    - Weather at venue (OpenWeatherMap)
    - Current form (Football-Data.org)
    - Betting odds (The Odds API)
    - Travel distance (calculated)

    Falls back to defaults if APIs unavailable.
    """
    try:
        engine = get_prediction_engine()

        if not match_date:
            match_date = datetime.now().strftime("%Y-%m-%d")

        prediction = engine.analyze_match_live(
            home_team=home_team,
            away_team=away_team,
            favorite=favorite,
            underdog=underdog,
            match_date=match_date
        )

        return ApiResponse(data=engine.to_dict(prediction))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live prediction error: {str(e)}")


@app.get("/api/v1/predict/patterns")
async def get_prediction_patterns():
    """
    Get all validated Third Knowledge patterns used by the predictor.

    Patterns combine Side A (weakness) + Side B (strength) factors
    to identify hidden upset indicators.
    """
    try:
        engine = get_prediction_engine()

        patterns = [
            {
                "name": p.pattern_name,
                "description": p.description,
                "factor_a": p.factor_a_code,
                "factor_b": p.factor_b_code,
                "interaction_type": p.interaction_type,
                "multiplier": p.multiplier,
                "confidence": p.confidence
            }
            for p in engine.patterns
        ]

        return ApiResponse(data={
            "patterns": patterns,
            "total": len(patterns)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern retrieval error: {str(e)}")


@app.get("/api/v1/predict/context/{home_team}/{away_team}")
async def get_match_context(home_team: str, away_team: str):
    """
    Get live match context without generating a full prediction.

    Useful for debugging and understanding what data the predictor sees.
    """
    try:
        engine = get_prediction_engine()
        context = engine.get_live_match_context(home_team, away_team)

        if context is None:
            return ApiResponse(
                data=None,
                meta={"message": "No live data available. Check API keys."}
            )

        return ApiResponse(data=context)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval error: {str(e)}")


# ============================================
# BRIDGE ENDPOINTS (Fan <-> Predictor)
# ============================================

# Name mapping for cross-system queries
TEAM_NAME_MAP = {
    "wolves": "wolverhampton",
    "wolverhampton": "wolves",
    "spurs": "tottenham",
    "man_united": "manchester_united",
    "man_utd": "manchester_united",
    "united": "manchester_united",
    "man_city": "manchester_city",
    "city": "manchester_city",
    "villa": "aston_villa",
    "palace": "crystal_palace",
    "forest": "nottingham_forest",
    "hammers": "west_ham",
    "toon": "newcastle",
}


def normalize_team_name(name: str, for_system: str = "fan") -> str:
    """Normalize team name for cross-system queries."""
    name_lower = name.lower().replace(" ", "_").replace("-", "_")
    if for_system == "fan" and name_lower == "wolves":
        return "Wolverhampton"
    if for_system == "predictor" and name_lower == "wolverhampton":
        return "Wolves"
    return name


@app.get("/api/v1/teams/{team_id}/insights")
async def get_team_insights(team_id: int):
    """
    BRIDGE: Get predictor insights for a fan app team.

    Connects predictor analyst_insights to fan-facing content.
    Example: "Did you know? Man United has a 78% Collapse Risk pattern."
    """
    try:
        # Get team from fan DB
        team = database.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Get predictor engine and team insights
        engine = get_prediction_engine()
        team_name = normalize_team_name(team["name"], for_system="predictor")
        insights = engine.get_team_insights(team_name)

        # Format for fan consumption
        fan_insights = []
        for insight in insights:
            fan_insights.append({
                "title": insight["title"],
                "type": insight["type"],
                "confidence": f"{insight['confidence']*100:.0f}%",
                "fan_friendly": f"The Analyst says: {insight['title']} ({insight['confidence']*100:.0f}% confidence)"
            })

        return ApiResponse(data={
            "team": team,
            "insights": fan_insights,
            "source": "The Analyst (predictor_facts.db)"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights error: {str(e)}")


@app.get("/api/v1/match/preview/{home_team_id}/{away_team_id}")
async def get_match_preview(home_team_id: int, away_team_id: int):
    """
    BRIDGE: Combined fan context + predictor analysis for a match.

    Returns:
    - Fan data: team identities, moods, rivalry info
    - Predictor data: patterns, insights, upset probability
    """
    try:
        # Get teams from fan DB
        home_team = database.get_team(home_team_id)
        away_team = database.get_team(away_team_id)

        if not home_team or not away_team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Fan context
        home_identity = database.get_club_identity(home_team_id)
        away_identity = database.get_club_identity(away_team_id)
        home_mood = database.get_club_mood(home_team_id)
        away_mood = database.get_club_mood(away_team_id)

        # Check for rivalry
        rivalries = database.get_club_rivalries(home_team_id)
        is_derby = False
        derby_info = None
        for rivalry in rivalries:
            if rivalry.get("rival_team_id") == away_team_id:
                is_derby = True
                derby_info = rivalry
                break

        # Predictor context
        engine = get_prediction_engine()
        home_name = normalize_team_name(home_team["name"], "predictor")
        away_name = normalize_team_name(away_team["name"], "predictor")

        home_insights = engine.get_team_insights(home_name)
        away_insights = engine.get_team_insights(away_name)

        # Generate prediction (home team as favorite by default)
        prediction = engine.analyze_match(
            home_team=home_team["name"],
            away_team=away_team["name"],
            favorite=home_team["name"],
            underdog=away_team["name"],
            match_date=datetime.now().strftime("%Y-%m-%d"),
            match_data={}
        )

        return ApiResponse(data={
            "match": {
                "home_team": home_team,
                "away_team": away_team,
                "is_derby": is_derby,
                "derby_info": derby_info
            },
            "fan_context": {
                "home": {
                    "identity": home_identity,
                    "mood": home_mood
                },
                "away": {
                    "identity": away_identity,
                    "mood": away_mood
                }
            },
            "predictor_context": {
                "home_insights": home_insights,
                "away_insights": away_insights,
                "prediction": engine.to_dict(prediction),
                "dixon_coles": _get_dc_preview(home_team["name"], away_team["name"]),
            },
            "talking_points": [
                f"Upset probability: {prediction.final_upset_prob:.0%}",
                f"Confidence: {prediction.confidence_level.upper()}",
                prediction.key_insight
            ]
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")


import re as _re

# ─── Fan Memory Detection ──────────────────────────────────────

_MEMORY_PATTERNS = _re.compile(
    r'\b(i\s+was\s+(?:at|there)|my\s+first\s+match|i\s+remember\s+(?:when|the)|'
    r'i\s+(?:saw|watched)\s+(?:the|that|it)|i\s+was\s+(?:in\s+the\s+(?:stands?|crowd|stadium))|'
    r'i\'?ve\s+(?:been\s+(?:a\s+fan|supporting)|followed\s+them)|'
    r'my\s+(?:dad|father|grandad|mum|family)\s+(?:took|brought|used\s+to\s+take))\b',
    _re.IGNORECASE
)


def _maybe_store_fan_memory(message: str, session_id: str, club: str = None):
    """Detect personal fan memories in the user's message and store them."""
    if not _MEMORY_PATTERNS.search(message):
        return
    if not session_id:
        return

    # Classify memory type
    msg_lower = message.lower()
    if "first match" in msg_lower or "first game" in msg_lower:
        memory_type = "first_match"
    elif "was at" in msg_lower or "was there" in msg_lower or "in the stands" in msg_lower:
        memory_type = "attended_match"
    elif "remember when" in msg_lower or "remember the" in msg_lower:
        memory_type = "memory"
    elif "dad" in msg_lower or "father" in msg_lower or "family" in msg_lower or "grandad" in msg_lower:
        memory_type = "family_heritage"
    elif "been a fan" in msg_lower or "following" in msg_lower or "supporting" in msg_lower:
        memory_type = "fan_history"
    else:
        memory_type = "general"

    try:
        database.save_fan_memory(
            session_id=session_id,
            club=club or "unknown",
            memory_text=message,
            memory_type=memory_type,
        )
        print(f"[FAN MEMORY] Stored ({memory_type}): {message[:80]}...")
    except Exception as e:
        print(f"[FAN MEMORY] Failed to store: {e}")


def _maybe_inject_fan_memories(session_id: str, club: str, context: str) -> str:
    """If the user has stored fan memories, inject them into the context."""
    if not session_id:
        return context

    try:
        memories = database.get_fan_memories(session_id, club=club, limit=5)
        if not memories:
            return context

        memory_lines = []
        for m in memories:
            memory_lines.append(f"- [{m['memory_type']}] \"{m['memory_text']}\"")

        memory_context = f"""
=== FAN'S PERSONAL MEMORIES (reference these naturally when relevant — they shared these with you) ===
{chr(10).join(memory_lines)}

You REMEMBER these moments because you're a fellow fan. When relevant, reference them warmly:
"You were there! You know exactly what that felt like..." or "Your dad took you? That's proper football heritage, that is."
Don't force it — only mention if the conversation naturally touches on it."""

        return context + "\n" + memory_context

    except Exception:
        return context

# Keywords that signal the user is asking about a match prediction
_PREDICTION_PATTERNS = _re.compile(
    r'\b(predict|prediction|who.?ll?\s+win|who\s+wins|chances|odds|'
    r'this\s+weekend|upcoming|next\s+match|vs\.?|versus|'
    r'beat|result|score.?line|expect|how\s+will.*do|gonna\s+win|'
    r'reckon|fancy|tip)\b',
    _re.IGNORECASE
)

# Match "TeamA vs TeamB" or "TeamA against TeamB" patterns
_VS_PATTERN = _re.compile(
    r'(\w[\w\s]+?)\s+(?:vs\.?|versus|against|v)\s+(\w[\w\s]+)',
    _re.IGNORECASE
)


def _maybe_inject_prediction(message: str, context: str, club: str = None) -> str:
    """
    Detect prediction intent in the user's message.
    If found, fetch Dixon-Coles prediction and inject as natural context.
    The fan persona will weave this into their emotional response.
    """
    if not _PREDICTION_PATTERNS.search(message):
        return context

    try:
        from predictor.dixon_coles import predict as dc_predict, odds_to_probabilities, get_match_odds

        model = get_dixon_coles_model()
        if model is None:
            return context

        # Try to extract two teams from the message
        vs_match = _VS_PATTERN.search(message)
        home_team = None
        away_team = None

        if vs_match:
            raw_home = vs_match.group(1).strip()
            raw_away = vs_match.group(2).strip()
            # Resolve to DB names
            for club_key, db_name in fan_enhancements.CLUB_TO_DB_NAME.items():
                if raw_home.lower() in db_name.lower() or db_name.lower() in raw_home.lower() or raw_home.lower().replace(" ", "_") == club_key:
                    home_team = db_name
                if raw_away.lower() in db_name.lower() or db_name.lower() in raw_away.lower() or raw_away.lower().replace(" ", "_") == club_key:
                    away_team = db_name

        # If we can't find two teams but have a club context, check upcoming fixtures
        if (not home_team or not away_team) and club and club != "default":
            import sqlite3 as _sql
            conn = _sql.connect(database.DB_PATH)
            conn.row_factory = _sql.Row
            db_club = fan_enhancements.CLUB_TO_DB_NAME.get(club, "")
            # Find next match for this club
            fixture = conn.execute("""
                SELECT h.name AS home, a.name AS away
                FROM games g
                JOIN teams h ON g.home_team_id = h.id
                JOIN teams a ON g.away_team_id = a.id
                WHERE g.status = 'scheduled' AND g.date >= date('now')
                  AND (h.name LIKE ? OR a.name LIKE ?)
                ORDER BY g.date LIMIT 1
            """, (f"%{db_club}%", f"%{db_club}%")).fetchone()
            conn.close()

            if fixture:
                # Resolve fixture team names to match_history names
                for ck, dn in fan_enhancements.CLUB_TO_DB_NAME.items():
                    if dn.lower() in fixture["home"].lower() or fixture["home"].lower() in dn.lower():
                        home_team = dn
                    if dn.lower() in fixture["away"].lower() or fixture["away"].lower() in dn.lower():
                        away_team = dn

        if not home_team or not away_team:
            return context

        # Get prediction
        dc = dc_predict(model, home_team, away_team)

        # Get bookmaker odds if available
        odds = get_match_odds(home_team, away_team)
        if odds:
            bk_h, bk_d, bk_a = odds_to_probabilities(*odds)
            ens_h = 0.40 * dc["home_win"] + 0.60 * bk_h
            ens_d = 0.40 * dc["draw"] + 0.60 * bk_d
            ens_a = 0.40 * dc["away_win"] + 0.60 * bk_a
        else:
            ens_h, ens_d, ens_a = dc["home_win"], dc["draw"], dc["away_win"]

        # Determine prediction outcome
        max_p = max(ens_h, ens_d, ens_a)
        if ens_d >= 0.245 and ens_d >= max_p * 0.75:
            pred_label = "Draw"
        elif ens_h >= ens_a:
            pred_label = f"{home_team} win"
        else:
            pred_label = f"{away_team} win"

        # Format as natural context for the persona
        prediction_context = f"""
=== MATCH PREDICTION DATA (weave this naturally into your response — feel it, don't recite it) ===
Match: {home_team} vs {away_team}
Your gut says: {pred_label}
Probabilities: Home {ens_h:.0%} / Draw {ens_d:.0%} / Away {ens_a:.0%}
Expected goals: {home_team} {dc['expected_home_goals']} - {dc['expected_away_goals']} {away_team}
Most likely score: {dc['most_likely_score'][0]}-{dc['most_likely_score'][1]}
{"Bookmaker odds: " + f"H={odds[0]:.2f} D={odds[1]:.2f} A={odds[2]:.2f}" if odds else "No bookmaker odds available"}

IMPORTANT: Express this as a FAN, not an analyst. Say "I reckon", "my gut says", "the numbers back us".
Reference the xG and probabilities casually, not as a data dump. Feel the prediction."""

        return context + "\n" + prediction_context

    except Exception as e:
        # Graceful fallback — don't break chat if prediction fails
        return context


def _get_dc_preview(home_name: str, away_name: str) -> Optional[Dict]:
    """Get Dixon-Coles prediction for match preview (graceful fallback)."""
    try:
        from predictor.dixon_coles import predict as dc_predict
        model = get_dixon_coles_model()
        if model is None:
            return None
        db_home = fan_enhancements.CLUB_TO_DB_NAME.get(
            home_name.lower().replace(" ", "_"), home_name
        )
        db_away = fan_enhancements.CLUB_TO_DB_NAME.get(
            away_name.lower().replace(" ", "_"), away_name
        )
        dc = dc_predict(model, db_home, db_away)
        return {
            "probabilities": {
                "home_win": dc["home_win"],
                "draw": dc["draw"],
                "away_win": dc["away_win"],
            },
            "expected_goals": {
                "home": dc["expected_home_goals"],
                "away": dc["expected_away_goals"],
            },
            "most_likely_score": f"{dc['most_likely_score'][0]}-{dc['most_likely_score'][1]}",
            "rho": dc["rho"],
            "model": "Dixon-Coles v2",
        }
    except Exception:
        return None


@app.get("/api/v1/derby/check/{team1_id}/{team2_id}")
async def check_derby(team1_id: int, team2_id: int):
    """
    BRIDGE: Check if two teams have a derby rivalry.

    Returns rivalry intensity which feeds into B08 derby_motivation.
    """
    try:
        team1 = database.get_team(team1_id)
        team2 = database.get_team(team2_id)

        if not team1 or not team2:
            raise HTTPException(status_code=404, detail="Team not found")

        rivalries = database.get_club_rivalries(team1_id)
        rivalry = None
        for r in rivalries:
            if r.get("rival_team_id") == team2_id:
                rivalry = r
                break

        if rivalry:
            # Map intensity to B08 factor
            intensity = rivalry.get("intensity", 5)
            b08_active = intensity >= 8  # Derby motivation activates at intensity 8+

            return ApiResponse(data={
                "is_derby": True,
                "rivalry_name": rivalry.get("rivalry_name"),
                "intensity": intensity,
                "b08_derby_motivation": b08_active,
                "predictor_impact": f"B08 factor {'ACTIVE' if b08_active else 'inactive'} (intensity {intensity}/10)"
            })
        else:
            return ApiResponse(data={
                "is_derby": False,
                "rivalry_name": None,
                "intensity": 0,
                "b08_derby_motivation": False,
                "predictor_impact": "B08 factor inactive (no rivalry)"
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Derby check error: {str(e)}")


# ============================================
# IMPLEMENTATION GAP TRACKER (Phase 0)
# ============================================

@app.get("/api/v1/admin/gaps")
async def get_implementation_gaps(
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    """
    Get current implementation gap status.
    The meta-tool that prevents 'forgotten implementation' pattern.
    """
    try:
        gaps = database.get_implementation_gaps(status=status, priority=priority)
        summary = database.get_gap_summary()
        return ApiResponse(data={
            "gaps": gaps,
            "summary": summary
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap retrieval error: {str(e)}")


@app.post("/api/v1/admin/gaps/{gap_id}/status")
async def update_gap_status(
    gap_id: int,
    new_status: str,
    notes: Optional[str] = None
):
    """Update status of an implementation gap."""
    valid_statuses = ["pending", "in_progress", "completed", "deferred"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid_statuses}")

    try:
        database.update_gap_status(gap_id, new_status, notes)
        return ApiResponse(data={"gap_id": gap_id, "new_status": new_status})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SECURITY METRICS (Phase 1)
# ============================================

@app.get("/api/v1/admin/security")
async def get_security_metrics(days: int = Query(default=7, ge=1, le=30)):
    """
    Get security metrics - injection attempts, session states, etc.
    """
    try:
        metrics = database.get_security_metrics(days=days)
        return ApiResponse(data=metrics)
    except Exception as e:
        return ApiResponse(data={"error": str(e), "message": "Security tables may not be initialized"})


# ============================================
# METRICS ENDPOINT (Phase 2)
# ============================================

@app.get("/api/v1/metrics")
async def get_system_metrics():
    """
    Get system metrics - response times, API costs, cache stats.
    """
    try:
        analytics = database.get_analytics_summary(days=7)
        db_stats = database.get_db_stats()
        security = database.get_security_metrics(days=7)

        return ApiResponse(data={
            "analytics": analytics,
            "database": db_stats,
            "security": security,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ON THIS DAY (Phase 2)
# ============================================

@app.get("/api/v1/on-this-day")
async def get_on_this_day(date: Optional[str] = None):
    """
    Get historic moments matching today's MM-DD (or specified date).
    Example: January 5 returns all January 5 moments from history.
    """
    try:
        month_day = None
        if date:
            # Parse provided date
            try:
                parsed = datetime.strptime(date, "%Y-%m-%d")
                month_day = f"{parsed.month:02d}-{parsed.day:02d}"
            except ValueError:
                raise HTTPException(status_code=400, detail="Date format: YYYY-MM-DD")

        moments = database.get_moments_on_this_day(month_day)

        display_date = month_day or datetime.now().strftime("%m-%d")
        return ApiResponse(data={
            "date": display_date,
            "moments": moments,
            "total": len(moments)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TRIVIA SYSTEM (Phase 6)
# ============================================

@app.get("/api/v1/trivia")
async def get_trivia_question(
    team_id: Optional[int] = None,
    category: Optional[str] = None,
    difficulty: str = "medium"
):
    """
    Get a random trivia question.

    Categories: legends, history, transfers, rivalries, stats
    Difficulty: easy, medium, hard, expert
    """
    try:
        question = database.get_trivia_question(
            team_id=team_id,
            category=category,
            difficulty=difficulty
        )

        if not question:
            return ApiResponse(data=None, meta={"message": "No trivia questions found for criteria"})

        return ApiResponse(data=question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/trivia/check")
async def check_trivia_answer(question_id: int, answer: str):
    """
    Check answer for a trivia question.
    Returns correctness and explanation.
    """
    try:
        result = database.check_trivia_answer(question_id, answer)
        return ApiResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trivia/stats")
async def get_trivia_stats(team_id: Optional[int] = None):
    """Get trivia statistics."""
    try:
        stats = database.get_trivia_stats(team_id=team_id)
        return ApiResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# LEGEND STORYTELLING (Phase 2)
# ============================================

@app.post("/api/v1/legends/{legend_id}/tell-story")
async def tell_legend_story(
    legend_id: int,
    angle: str = Query(default="career", description="Story angle: career, moment, legacy")
):
    """
    Generate AI narrative about a legend.

    Angles:
    - career: Full career story
    - moment: Focus on defining moment
    - legacy: What they mean to the club
    """
    try:
        legend = database.get_legend(legend_id)
        if not legend:
            raise HTTPException(status_code=404, detail="Legend not found")

        # Get related context
        team = database.get_team(legend.get("team_id")) if legend.get("team_id") else None
        moments = database.get_club_moments(legend.get("team_id"), limit=3) if legend.get("team_id") else []

        # Build context for AI
        context = f"""
        Legend: {legend.get('name')}
        Team: {team.get('name') if team else 'Unknown'}
        Position: {legend.get('position', 'Unknown')}
        Era: {legend.get('years_active', 'Unknown')}
        Achievements: {legend.get('achievements', 'Unknown')}
        """

        if angle == "moment" and legend.get("defining_moment"):
            context += f"\nDefining Moment: {legend.get('defining_moment')}"

        if angle == "legacy":
            context += f"\nLegacy: {legend.get('legacy_description', 'A true club legend')}"

        # Generate response using AI
        result = ai_response.generate_response(
            query=f"Tell me the {angle} story of {legend.get('name')}",
            context=context,
            sources=[{"type": "legend", "id": legend_id}],
            club=team.get("name", "default").lower().replace(" ", "_") if team else "default"
        )

        return ApiResponse(data={
            "legend": legend,
            "story": result.get("response"),
            "angle": angle,
            "team": team
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/legends/compare")
async def compare_legends(a: int, b: int):
    """
    Compare two legends across eras.
    """
    try:
        legend_a = database.get_legend(a)
        legend_b = database.get_legend(b)

        if not legend_a or not legend_b:
            raise HTTPException(status_code=404, detail="One or both legends not found")

        # Get teams
        team_a = database.get_team(legend_a.get("team_id")) if legend_a.get("team_id") else None
        team_b = database.get_team(legend_b.get("team_id")) if legend_b.get("team_id") else None

        # Build comparison context
        context = f"""
        Legend A: {legend_a.get('name')} ({team_a.get('name') if team_a else 'Unknown'})
        Position: {legend_a.get('position')}, Era: {legend_a.get('years_active')}
        Achievements: {legend_a.get('achievements')}

        Legend B: {legend_b.get('name')} ({team_b.get('name') if team_b else 'Unknown'})
        Position: {legend_b.get('position')}, Era: {legend_b.get('years_active')}
        Achievements: {legend_b.get('achievements')}
        """

        result = ai_response.generate_response(
            query=f"Compare {legend_a.get('name')} and {legend_b.get('name')} as players and legends",
            context=context,
            sources=[
                {"type": "legend", "id": a},
                {"type": "legend", "id": b}
            ],
            club="default"
        )

        return ApiResponse(data={
            "legend_a": legend_a,
            "legend_b": legend_b,
            "comparison": result.get("response"),
            "same_club": legend_a.get("team_id") == legend_b.get("team_id")
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# MOOD AUTO-UPDATE (Phase 3)
# ============================================

@app.post("/api/v1/teams/{team_id}/match-result")
async def record_match_result(
    team_id: int,
    result: str = Query(description="Result: W, D, or L"),
    is_derby: bool = False
):
    """
    Record match result and auto-update team mood.

    Results affect mood:
    - W = +0.2 (derby W = +0.4)
    - D = 0
    - L = -0.2
    - Rival L = +0.1
    """
    if result.upper() not in ["W", "D", "L"]:
        raise HTTPException(status_code=400, detail="Result must be W, D, or L")

    try:
        team = database.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        old_mood = database.get_club_mood(team_id)
        new_mood = database.update_mood_after_match(team_id, result.upper(), is_derby)

        return ApiResponse(data={
            "team": team,
            "result": result.upper(),
            "is_derby": is_derby,
            "mood_before": old_mood.get("intensity") if old_mood else None,
            "mood_after": new_mood.get("intensity") if new_mood else None
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# LIVE MATCH COMPANION
# ============================================

@app.get("/api/v1/live/companion/matches")
async def get_available_simulations():
    """List available simulated matches for demo/testing."""
    from live_companion import SIMULATED_MATCHES
    matches = []
    for key, script in SIMULATED_MATCHES.items():
        matches.append({
            "key": key,
            "home_team": script["home_team"],
            "away_team": script["away_team"],
            "home_id": script["home_id"],
            "away_id": script["away_id"],
            "events_count": len(script["events"]),
        })
    return {"success": True, "data": matches}


# ============================================
# SEASON MOOD TIMELINE
# ============================================

@app.get("/api/v1/fan/{club}/mood-timeline")
async def get_mood_timeline(club: str, season: str = "2024"):
    """
    Compute mood trajectory across a full season for a club.
    Returns per-match mood points with rolling 5-game form window.
    Season param is the starting year (e.g., "2024" for 2024-25 season).
    """
    raw = club.lower().strip().replace(" ", "_").replace("-", "_")
    resolved = TEAM_NAME_MAP.get(raw, raw)
    club = resolved if resolved in VALID_CLUBS else raw
    if club not in VALID_CLUBS or club == "analyst":
        raise HTTPException(status_code=404, detail=f"Unknown club: {club}")

    db_team = fan_enhancements.CLUB_TO_DB_NAME.get(club)
    if not db_team:
        raise HTTPException(status_code=404, detail=f"No DB mapping for: {club}")

    import sqlite3 as _sqlite3
    kg_db = fan_enhancements.DB_PATH
    conn = _sqlite3.connect(kg_db)
    conn.row_factory = _sqlite3.Row

    # Get all matches for this team in the season
    season_start = f"{season}-08-01"
    season_end = f"{int(season) + 1}-06-30"

    matches = conn.execute("""
        SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result
        FROM match_history
        WHERE division = 'E0'
          AND (home_team = ? OR away_team = ?)
          AND match_date >= ? AND match_date <= ?
        ORDER BY match_date
    """, (db_team, db_team, season_start, season_end)).fetchall()
    conn.close()

    if not matches:
        return {"success": True, "data": {"club": club, "season": f"{season}-{int(season)+1}", "points": []}}

    # Compute per-match mood with rolling 5-game window
    results_window: list = []
    points = []

    for i, m in enumerate(matches):
        date = m["match_date"]
        home = m["home_team"]
        away = m["away_team"]
        fh = m["ft_home"] or 0
        fa = m["ft_away"] or 0
        result = m["ft_result"]

        is_home = (home == db_team)
        opponent = away if is_home else home
        my_goals = fh if is_home else fa
        their_goals = fa if is_home else fh

        if is_home:
            match_result = "W" if result == "H" else ("D" if result == "D" else "L")
        else:
            match_result = "W" if result == "A" else ("D" if result == "D" else "L")

        results_window.append(match_result)
        if len(results_window) > 5:
            results_window.pop(0)

        # Compute mood from window: W=3, D=1, L=0
        score = sum({"W": 3, "D": 1, "L": 0}[r] for r in results_window)
        max_score = len(results_window) * 3
        mood_value = round(score / max_score, 3) if max_score > 0 else 0.5

        if mood_value >= 0.8:
            mood_label = "euphoric"
        elif mood_value >= 0.6:
            mood_label = "confident"
        elif mood_value >= 0.4:
            mood_label = "steady"
        elif mood_value >= 0.2:
            mood_label = "anxious"
        else:
            mood_label = "despairing"

        score_str = f"{fh}-{fa}" if is_home else f"{fa}-{fh}"

        points.append({
            "matchweek": i + 1,
            "date": date,
            "opponent": opponent,
            "is_home": is_home,
            "score": f"{home} {fh}-{fa} {away}",
            "result": match_result,
            "my_goals": my_goals,
            "their_goals": their_goals,
            "mood_value": mood_value,
            "mood_label": mood_label,
            "form": "".join(results_window),
        })

    return {
        "success": True,
        "data": {
            "club": club,
            "club_display": db_team,
            "season": f"{season}-{str(int(season)+1)[-2:]}",
            "total_matches": len(points),
            "points": points,
        }
    }


# ============================================
# BUDGET STATUS
# ============================================

@app.get("/api/v1/budget")
async def budget_status():
    """Get current daily AI budget status."""
    return {"success": True, "data": get_budget_status()}


# ============================================
# USER FAN MEMORIES API
# ============================================

@app.get("/api/v1/fan/memories/{session_id}")
async def get_fan_memories(session_id: str, club: str = None):
    """Get stored fan memories for a session."""
    memories = database.get_fan_memories(session_id, club=club)
    return {"success": True, "data": {"memories": memories, "count": len(memories)}}


@app.post("/api/v1/fan/memories")
async def store_fan_memory(
    session_id: str = Body(...),
    club: str = Body(...),
    memory: str = Body(...),
    memory_type: str = Body("general"),
):
    """Manually store a fan memory."""
    database.save_fan_memory(session_id, club, memory, memory_type)
    return {"success": True, "data": {"message": "Memory stored", "session_id": session_id}}


@app.delete("/api/v1/fan/memories/{session_id}")
async def clear_fan_memories(session_id: str):
    """Clear all fan memories for a session."""
    database.delete_fan_memories(session_id)
    return {"success": True, "data": {"message": "Memories cleared"}}


# In-memory store for active simulations
_active_simulations: Dict[str, Dict] = {}


@app.post("/api/v1/live/companion/simulate/{match_key}/{club}")
async def start_simulation(match_key: str, club: str, req: Request = None):
    """
    Start a simulated match. Returns a session_id.
    The simulation runs in a background thread, generating events over time.
    Poll GET /api/v1/live/companion/events/{session_id} to get new events.
    """
    # Rate limit check
    client_ip = req.client.host if req and req.client else "unknown"
    allowed, limit_msg = check_rate_limit(client_ip, "companion")
    if not allowed:
        raise HTTPException(status_code=429, detail=limit_msg)

    from live_companion import (
        SIMULATED_MATCHES, MatchState, detect_changes,
        generate_reaction,
    )
    import threading

    club = TEAM_NAME_MAP.get(club.lower().strip().replace(" ", "_"), club.lower().strip().replace(" ", "_"))

    if match_key not in SIMULATED_MATCHES:
        raise HTTPException(status_code=404, detail=f"Unknown match: {match_key}")
    if club not in VALID_CLUBS and club != "analyst":
        raise HTTPException(status_code=400, detail=f"Unknown club: {club}")

    script = SIMULATED_MATCHES[match_key]
    session_id = f"{match_key}_{club}_{int(time.time())}"

    session = {
        "session_id": session_id,
        "match_key": match_key,
        "club": club,
        "home_team": script["home_team"],
        "away_team": script["away_team"],
        "events": [],
        "finished": False,
        "score_home": 0,
        "score_away": 0,
        "status": "TIMED",
    }
    _active_simulations[session_id] = session

    def run_sim():
        """Run simulation in background thread."""
        home_team = script["home_team"]
        away_team = script["away_team"]
        is_home_fan = (club == script["home_id"])
        state = MatchState(match_id=0, home_team=home_team, away_team=away_team)

        for step in script["events"]:
            if step["delay"] > 0:
                time.sleep(step["delay"])

            current_data = {
                "status": step["status"],
                "home_score": step["home"],
                "away_score": step["away"],
                "minute": step["minute"],
            }

            changes = detect_changes(state, current_data)
            state.home_score = step["home"]
            state.away_score = step["away"]
            state.status = step["status"]
            state.minute = step["minute"]

            session["score_home"] = step["home"]
            session["score_away"] = step["away"]
            session["status"] = step["status"]

            for change in changes:
                try:
                    reaction = generate_reaction(
                        change, club, home_team, away_team, is_home_fan
                    )
                except Exception:
                    reaction = "..."

                session["events"].append({
                    "type": "event",
                    "event_type": change["type"],
                    "minute": change["minute"],
                    "description": change["desc"],
                    "reaction": reaction,
                    "score_home": step["home"],
                    "score_away": step["away"],
                    "home_team": home_team,
                    "away_team": away_team,
                    "timestamp": datetime.utcnow().isoformat(),
                })

        session["finished"] = True

    thread = threading.Thread(target=run_sim, daemon=True)
    thread.start()

    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "home_team": script["home_team"],
            "away_team": script["away_team"],
            "club": club,
            "message": "Simulation started. Poll /api/v1/live/companion/events/{session_id} for updates.",
        }
    }


@app.get("/api/v1/live/companion/events/{session_id}")
async def get_companion_events(session_id: str, after: int = 0):
    """
    Poll for new events from an active simulation.
    Pass `after=N` to get events after index N (for incremental polling).
    """
    session = _active_simulations.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    events = session["events"][after:]

    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "home_team": session["home_team"],
            "away_team": session["away_team"],
            "club": session["club"],
            "score_home": session["score_home"],
            "score_away": session["score_away"],
            "status": session["status"],
            "finished": session["finished"],
            "events": events,
            "total_events": len(session["events"]),
        }
    }


# ============================================
# FAN DEBATE MODE
# ============================================

@app.post("/api/v1/debate")
async def fan_debate(
    req: Request,
    club_a: str = Body(...),
    club_b: str = Body(...),
    topic: str = Body(...),
    rounds: int = Body(3),
):
    """
    Two fan personas debate a topic, taking turns.
    Each sees the other's previous response as context.
    Returns the full exchange.
    """
    # Rate limit check
    client_ip = req.client.host if req.client else "unknown"
    allowed, limit_msg = check_rate_limit(client_ip, "debate")
    if not allowed:
        raise HTTPException(status_code=429, detail=limit_msg)

    # Resolve aliases
    club_a = TEAM_NAME_MAP.get(club_a.lower().strip().replace(" ", "_"), club_a.lower().strip().replace(" ", "_"))
    club_b = TEAM_NAME_MAP.get(club_b.lower().strip().replace(" ", "_"), club_b.lower().strip().replace(" ", "_"))

    if club_a not in VALID_CLUBS or club_a == "analyst":
        raise HTTPException(status_code=400, detail=f"Unknown club: {club_a}")
    if club_b not in VALID_CLUBS or club_b == "analyst":
        raise HTTPException(status_code=400, detail=f"Unknown club: {club_b}")
    if club_a == club_b:
        raise HTTPException(status_code=400, detail="Pick two different clubs!")

    rounds = min(max(rounds, 1), 5)  # Clamp 1-5

    # Load persona data for both clubs
    persona_a = None
    persona_b = None
    if club_a in CLUB_TO_TEAM_ID:
        persona_a = database.load_full_persona(CLUB_TO_TEAM_ID[club_a])
    if club_b in CLUB_TO_TEAM_ID:
        persona_b = database.load_full_persona(CLUB_TO_TEAM_ID[club_b])

    # Get enhanced persona (mood + rivalry + dialect)
    enhanced_a = fan_enhancements.get_enhanced_persona(club_a, f"debate about {club_b}")
    enhanced_b = fan_enhancements.get_enhanced_persona(club_b, f"debate about {club_a}")

    club_a_display = club_a.replace("_", " ").title()
    club_b_display = club_b.replace("_", " ").title()

    def build_debate_system(club_display, enhanced, opponent_display):
        mood = enhanced.get("mood", {})
        dialect = enhanced.get("dialect", {})
        dialect_inject = dialect.get("vocab_inject", "") if dialect else ""
        phrases = ", ".join(f'"{p}"' for p in dialect.get("phrases", [])[:3]) if dialect else ""

        return f"""You are a passionate {club_display} fan in a heated debate against a {opponent_display} fan.

YOUR IDENTITY: You are a {club_display} supporter through and through.
CURRENT MOOD: {mood.get('current_mood', 'steady').upper()} — {mood.get('mood_reason', '')}

DEBATE RULES:
- Keep responses to 2-3 paragraphs MAX. Be punchy, not rambling.
- Lead with EMOTION, then back it up with facts.
- Reference your club's history, legends, and achievements.
- Attack the opponent's weak points — trophies, failures, embarrassments.
- Use your regional dialect naturally. {dialect_inject}
{f'Phrases to weave in: {phrases}' if phrases else ''}
- You're trying to WIN this debate. Don't concede points easily.
- Be passionate but not abusive. Banter, not hatred.
- NEVER break character. You are a real fan, not an AI."""

    system_a = build_debate_system(club_a_display, enhanced_a, club_b_display)
    system_b = build_debate_system(club_b_display, enhanced_b, club_a_display)

    exchanges = []
    context_for_a = f"The debate topic is: {topic}"
    context_for_b = ""

    for round_num in range(rounds):
        # Club A speaks
        prompt_a = context_for_a if round_num == 0 else f"The {club_b_display} fan just said:\n\n\"{context_for_b}\"\n\nRespond to their argument:"
        response_a = ai_response.call_anthropic_api(
            messages=[{"role": "user", "content": prompt_a}],
            system=system_a,
        )
        content_a = response_a.get("content", [])
        text_a = content_a[0]["text"] if isinstance(content_a, list) and content_a else response_a.get("response", "...")
        exchanges.append({"club": club_a, "club_display": club_a_display, "text": text_a, "round": round_num + 1})

        # Club B responds
        prompt_b = f"The {club_a_display} fan opened with:\n\n\"{text_a}\"\n\nRespond to their argument:" if round_num == 0 else f"The {club_a_display} fan just said:\n\n\"{text_a}\"\n\nRespond to their argument:"
        response_b = ai_response.call_anthropic_api(
            messages=[{"role": "user", "content": prompt_b}],
            system=system_b,
        )
        content_b = response_b.get("content", [])
        text_b = content_b[0]["text"] if isinstance(content_b, list) and content_b else response_b.get("response", "...")
        exchanges.append({"club": club_b, "club_display": club_b_display, "text": text_b, "round": round_num + 1})

        context_for_b = text_b  # For next round's context

    return {
        "success": True,
        "data": {
            "club_a": club_a,
            "club_b": club_b,
            "topic": topic,
            "rounds": rounds,
            "exchanges": exchanges,
        }
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc)
            }
        }
    )


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
