"""Value betting calculations and odds conversions."""
import math
from typing import Union


def american_to_decimal(odds_american: Union[str, int, float]) -> float:
    """Convert American odds to decimal odds."""
    if isinstance(odds_american, str):
        # Remove any whitespace and plus signs
        odds_str = odds_american.strip().replace('+', '')
        try:
            odds_value = float(odds_str)
        except ValueError:
            raise ValueError(f"Invalid odds format: {odds_american}")
    else:
        odds_value = float(odds_american)
    
    if odds_value > 0:
        # Positive odds: +150 -> 2.50
        return (odds_value / 100) + 1
    elif odds_value < 0:
        # Negative odds: -120 -> 1.83
        return (100 / abs(odds_value)) + 1
    else:
        raise ValueError("Odds cannot be zero")


def decimal_to_implied_prob(decimal_odds: float, remove_overround: bool = False) -> float:
    """Convert decimal odds to implied probability."""
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    
    implied = 1 / decimal_odds
    
    # Simple overround removal (assumes fair market)
    if remove_overround:
        # This is a simplified approach - in practice, overround removal is more complex
        return implied * 1.05  # Rough adjustment
    
    return implied


def american_to_implied_prob(odds_american: Union[str, int, float], remove_overround: bool = False) -> float:
    """Convert American odds directly to implied probability."""
    decimal_odds = american_to_decimal(odds_american)
    return decimal_to_implied_prob(decimal_odds, remove_overround)


def edge(model_prob: float, implied_prob: float) -> float:
    """Calculate edge: model probability minus implied probability."""
    return model_prob - implied_prob


def expected_value(model_prob: float, decimal_odds: float) -> float:
    """Calculate expected value per unit stake."""
    return (model_prob * (decimal_odds - 1)) - (1 - model_prob)


def kelly_fraction(
    model_prob: float, 
    decimal_odds: float, 
    fraction: float = 1.0
) -> float:
    """Calculate Kelly criterion fraction for optimal bet sizing."""
    if decimal_odds <= 1 or model_prob <= 0 or model_prob >= 1:
        return 0.0
    
    # Kelly formula: f = (bp - q) / b
    # where b = decimal_odds - 1, p = model_prob, q = 1 - model_prob
    b = decimal_odds - 1
    p = model_prob
    q = 1 - model_prob
    
    kelly_f = (b * p - q) / b
    
    # Apply fraction (e.g., 0.5 for half-Kelly)
    kelly_f *= fraction
    
    # Ensure non-negative and reasonable bounds
    return max(0.0, min(kelly_f, 0.25))  # Cap at 25% of bankroll


def suggested_stake(
    model_prob: float, 
    decimal_odds: float, 
    bankroll: float,
    kelly_fraction_mult: float = 1.0,
    max_stake_pct: float = 0.05
) -> float:
    """Calculate suggested stake based on Kelly criterion."""
    kelly_f = kelly_fraction(model_prob, decimal_odds, kelly_fraction_mult)
    
    # Apply maximum stake percentage limit
    stake_fraction = min(kelly_f, max_stake_pct)
    
    return bankroll * stake_fraction


def decimal_to_american(decimal_odds: float) -> str:
    """Convert decimal odds to American odds format."""
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    
    if decimal_odds >= 2.0:
        # Positive American odds: 2.50 -> +150
        american = int((decimal_odds - 1) * 100)
        return f"+{american}"
    else:
        # Negative American odds: 1.83 -> -120
        american = int(-100 / (decimal_odds - 1))
        return str(american)
