"""FastAPI application for football betting MVP."""
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from app.schemas import (
    PoissonRequest, PoissonResponse, ValueBetsRequest, ValueBetsResponse, ValueBet,
    LineupEntry, PlayerStats, TeamStats, OddsEntry
)
from app.services.poisson import p_geq, p_exact
from app.services.value import american_to_decimal, american_to_implied_prob, edge, suggested_stake
from app.services.adjust import compound_adjustments
from app.data.adapters.manual_csv import ManualCSVAdapter

app = FastAPI(
    title="Football Betting MVP",
    description="API for calculating player prop probabilities and value bets",
    version="1.0.0"
)

# Global adapter instance
stats_adapter = ManualCSVAdapter()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/prob/shots", response_model=PoissonResponse)
def calculate_poisson_probability(request: PoissonRequest):
    """Calculate Poisson probabilities for shots."""
    try:
        p_geq_value = p_geq(request.threshold, request.lambda_value)
        p_exact_value = p_exact(request.threshold, request.lambda_value)
        
        return PoissonResponse(
            p_geq=p_geq_value,
            p_exact=p_exact_value
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating probabilities: {str(e)}")


@app.post("/signals/value-bets", response_model=ValueBetsResponse)
def calculate_value_bets(request: ValueBetsRequest, bankroll: float = 1000.0):
    """Calculate value betting signals."""
    try:
        # Load data into adapter
        player_df = pd.DataFrame([p.dict() for p in request.player_stats])
        team_df = pd.DataFrame([t.dict() for t in request.team_stats])
        stats_adapter.load_from_dataframes(player_df, team_df)
        
        # Create lookup dictionaries
        lineups_dict = {}
        for lineup in request.lineups:
            key = (lineup.match_id, lineup.player_name, lineup.team)
            lineups_dict[key] = lineup
        
        signals = []
        
        for odds_entry in request.odds:
            # Find corresponding lineup entry
            lineup_key = (odds_entry.match_id, odds_entry.player_name, odds_entry.team)
            if lineup_key not in lineups_dict:
                continue
            
            lineup = lineups_dict[lineup_key]
            
            # Get player and opponent stats
            player_stats = stats_adapter.get_player_stats(odds_entry.player_name, odds_entry.team)
            if not player_stats:
                continue
            
            # Determine opponent team
            opponent_team = lineup.away_team if lineup.team == lineup.home_team else lineup.home_team
            opponent_stats = stats_adapter.get_team_stats(opponent_team)
            
            # Calculate adjusted lambda
            is_home = lineup.team == lineup.home_team
            opponent_shots_allowed = opponent_stats.shots_allowed_pg if opponent_stats else None
            
            adjusted_lambda = compound_adjustments(
                base_lam=player_stats.shots_pg,
                expected_minutes=lineup.expected_minutes,
                opponent_shots_allowed=opponent_shots_allowed,
                league_avg_shots_allowed=10.5,  # Default league average
                is_home=is_home,
                home_mult=1.05,
                away_mult=0.95
            )
            
            # Calculate model probability
            model_prob = p_geq(odds_entry.threshold, adjusted_lambda)
            
            # Calculate implied probability from odds
            implied_prob = american_to_implied_prob(odds_entry.odds_american)
            
            # Calculate edge and value metrics
            prob_edge = edge(model_prob, implied_prob)
            decimal_odds = american_to_decimal(odds_entry.odds_american)
            
            # Kelly fraction calculation
            stake = suggested_stake(model_prob, decimal_odds, bankroll, kelly_fraction_mult=1.0)
            kelly_fraction = stake / bankroll if bankroll > 0 else 0
            
            # Only include positive expected value bets
            if prob_edge > 0:
                signals.append(ValueBet(
                    match_id=odds_entry.match_id,
                    player=odds_entry.player_name,
                    prop=f"{odds_entry.market} ≥ {odds_entry.threshold}",
                    threshold=odds_entry.threshold,
                    model_prob=round(model_prob, 4),
                    implied_prob=round(implied_prob, 4),
                    edge=round(prob_edge, 4),
                    odds=odds_entry.odds_american,
                    kelly=round(kelly_fraction, 4),
                    suggested_stake=round(stake, 2)
                ))
        
        # Sort signals by edge (highest first)
        signals.sort(key=lambda x: x.edge, reverse=True)
        
        return ValueBetsResponse(signals=signals)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating value bets: {str(e)}")


@app.get("/stats/players")
def get_all_players():
    """Get all available player stats."""
    try:
        players = stats_adapter.get_all_players()
        return {"players": [p.dict() for p in players]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching players: {str(e)}")


@app.get("/stats/teams")
def get_all_teams():
    """Get all available team stats."""
    try:
        teams = stats_adapter.get_all_teams()
        return {"teams": [t.dict() for t in teams]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
