"""
Soccer-AI Pydantic Models
Request/Response models for FastAPI
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


# ============================================
# REQUEST MODELS
# ============================================

class ChatRequest(BaseModel):
    """Chat endpoint request."""
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None
    club: Optional[str] = Field(default=None, description="Fan persona club (arsenal, chelsea, manchester_united)")


class SearchRequest(BaseModel):
    """Search endpoint request."""
    query: str = Field(..., min_length=1, max_length=200)
    type: Optional[str] = Field(default="all", pattern="^(players|teams|games|news|all)$")
    limit: int = Field(default=10, ge=1, le=50)


# ============================================
# RESPONSE MODELS
# ============================================

class TeamBase(BaseModel):
    """Team base model."""
    id: int
    name: str
    short_name: Optional[str] = None
    league: str
    country: str
    stadium: Optional[str] = None
    founded: Optional[int] = None
    logo_url: Optional[str] = None


class TeamDetail(TeamBase):
    """Team detail model with additional info."""
    standing: Optional[Dict[str, Any]] = None
    next_game: Optional[Dict[str, Any]] = None


class PlayerBase(BaseModel):
    """Player base model."""
    id: int
    name: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    position: Optional[str] = None
    nationality: Optional[str] = None
    jersey_number: Optional[int] = None


class PlayerDetail(PlayerBase):
    """Player detail model with additional info."""
    birth_date: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    market_value_eur: Optional[int] = None
    photo_url: Optional[str] = None
    stats_summary: Optional[Dict[str, Any]] = None
    current_injury: Optional[Dict[str, Any]] = None


class PlayerStats(BaseModel):
    """Player statistics model."""
    player_id: int
    games: int = 0
    total_goals: int = 0
    total_assists: int = 0
    avg_rating: Optional[float] = None
    total_minutes: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class GameEvent(BaseModel):
    """Game event model."""
    id: int
    event_type: str
    minute: Optional[int] = None
    extra_time_minute: Optional[int] = None
    player_name: Optional[str] = None
    details: Optional[str] = None


class GameBase(BaseModel):
    """Game base model."""
    id: int
    date: date
    time: Optional[str] = None
    status: str
    home_team_id: int
    home_team_name: str
    home_team_short: Optional[str] = None
    away_team_id: int
    away_team_name: str
    away_team_short: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    competition: Optional[str] = None
    venue: Optional[str] = None


class GameDetail(GameBase):
    """Game detail model with events."""
    matchday: Optional[int] = None
    attendance: Optional[int] = None
    referee: Optional[str] = None
    events: List[GameEvent] = []
    stats: Optional[Dict[str, Any]] = None


class InjuryBase(BaseModel):
    """Injury base model."""
    id: int
    player_id: int
    player_name: str
    team_name: Optional[str] = None
    injury_type: str
    severity: Optional[str] = None
    occurred_date: Optional[date] = None
    expected_return: Optional[date] = None
    status: str


class TransferBase(BaseModel):
    """Transfer base model."""
    id: int
    player_id: int
    player_name: str
    from_team_id: Optional[int] = None
    from_team_name: Optional[str] = None
    to_team_id: Optional[int] = None
    to_team_name: Optional[str] = None
    transfer_type: Optional[str] = None
    fee_eur: Optional[int] = None
    announced_date: Optional[date] = None
    status: str


class StandingEntry(BaseModel):
    """League standing entry."""
    position: int
    team_id: int
    team_name: str
    short_name: Optional[str] = None
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    form: Optional[str] = None


class NewsArticle(BaseModel):
    """News article model."""
    id: int
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None


# ============================================
# CHAT RESPONSE MODELS
# ============================================

class ChatSource(BaseModel):
    """Source reference in chat response."""
    type: str
    id: Optional[int] = None
    ids: Optional[List[int]] = None


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    response: str
    conversation_id: Optional[str] = None
    sources: List[ChatSource] = []
    confidence: float = Field(default=0.5, ge=0, le=1)
    usage: Optional[Dict[str, int]] = None


# ============================================
# API RESPONSE WRAPPERS
# ============================================

class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None


class PaginatedMeta(BaseModel):
    """Pagination metadata."""
    total: int
    limit: int
    offset: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SearchResults(BaseModel):
    """Search results model."""
    query: str
    results: Dict[str, List[Any]]
    total: int


class DbStats(BaseModel):
    """Database statistics."""
    teams: int = 0
    players: int = 0
    games: int = 0
    player_stats: int = 0
    injuries: int = 0
    transfers: int = 0
    standings: int = 0
    news: int = 0
    game_events: int = 0


# ============================================
# ERROR MODELS
# ============================================

class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    data: None = None
    meta: None = None
    error: ErrorDetail
