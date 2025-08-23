"""Adjustment factors for player prop modeling."""
from typing import Optional


def minutes_scale(lam: float, expected_minutes: int, full_game_minutes: int = 90) -> float:
    """Scale lambda based on expected playing time."""
    if full_game_minutes <= 0:
        return lam
    return lam * (expected_minutes / full_game_minutes)


def opponent_scale(
    lam: float, 
    opp_shots_allowed_pg: float, 
    league_avg_shots_allowed: float
) -> float:
    """Scale lambda based on opponent's defensive strength."""
    if league_avg_shots_allowed <= 0:
        return lam
    return lam * (opp_shots_allowed_pg / league_avg_shots_allowed)


def home_away_scale(
    lam: float, 
    is_home: bool, 
    home_mult: float = 1.05, 
    away_mult: float = 0.95
) -> float:
    """Scale lambda based on home/away advantage."""
    return lam * (home_mult if is_home else away_mult)


def recent_form_blend(
    season_lam: float, 
    recent_lam: Optional[float], 
    weight: float = 0.0
) -> float:
    """Blend season and recent form lambda values."""
    if recent_lam is None or weight <= 0:
        return season_lam
    if weight >= 1:
        return recent_lam
    return weight * recent_lam + (1 - weight) * season_lam


def compound_adjustments(
    base_lam: float,
    expected_minutes: int = 90,
    opponent_shots_allowed: Optional[float] = None,
    league_avg_shots_allowed: float = 10.5,
    is_home: bool = True,
    home_mult: float = 1.05,
    away_mult: float = 0.95,
    recent_lam: Optional[float] = None,
    recent_weight: float = 0.0
) -> float:
    """Apply all adjustments to base lambda."""
    adjusted_lam = base_lam
    
    # Minutes adjustment
    adjusted_lam = minutes_scale(adjusted_lam, expected_minutes)
    
    # Opponent adjustment
    if opponent_shots_allowed is not None:
        adjusted_lam = opponent_scale(adjusted_lam, opponent_shots_allowed, league_avg_shots_allowed)
    
    # Home/away adjustment
    adjusted_lam = home_away_scale(adjusted_lam, is_home, home_mult, away_mult)
    
    # Recent form blend
    adjusted_lam = recent_form_blend(adjusted_lam, recent_lam, recent_weight)
    
    return max(0.0, adjusted_lam)  # Ensure non-negative
