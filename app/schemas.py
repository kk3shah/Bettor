"""Pydantic models for the betting MVP API."""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class LineupEntry(BaseModel):
    match_id: str
    kickoff_utc: datetime
    home_team: str
    away_team: str
    player_name: str
    team: str
    is_starter: bool
    expected_minutes: int


class PlayerStats(BaseModel):
    player_name: str
    team: str
    minutes_per_app: float
    shots_pg: float
    sot_pg: float
    fouls_pg: float
    passes_pg: float
    yc_pg: float
    apps: int


class TeamStats(BaseModel):
    team: str
    goals_for_pg: float
    goals_against_pg: float
    shots_allowed_pg: float
    cards_pg: float


class OddsEntry(BaseModel):
    match_id: str
    market: str
    player_name: str
    team: str
    threshold: int
    odds_american: str
    book: str


class PoissonRequest(BaseModel):
    lambda_value: float
    threshold: int


class PoissonResponse(BaseModel):
    p_geq: float
    p_exact: float


class ValueBetsRequest(BaseModel):
    lineups: List[LineupEntry]
    player_stats: List[PlayerStats]
    team_stats: List[TeamStats]
    odds: List[OddsEntry]


class ValueBet(BaseModel):
    model_config = {'protected_namespaces': ()}
    
    match_id: str
    player: str
    prop: str
    threshold: int
    model_prob: float
    implied_prob: float
    edge: float
    odds: str
    kelly: float
    suggested_stake: float


class ValueBetsResponse(BaseModel):
    signals: List[ValueBet]
