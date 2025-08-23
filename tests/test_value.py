"""Tests for value betting calculations."""
import pytest
from app.services.value import (
    american_to_decimal, decimal_to_implied_prob, american_to_implied_prob,
    edge, expected_value, kelly_fraction, suggested_stake
)


def test_american_to_decimal():
    """Test American odds to decimal odds conversion."""
    # Positive odds
    assert abs(american_to_decimal("+100") - 2.0) < 0.001
    assert abs(american_to_decimal("+150") - 2.5) < 0.001
    assert abs(american_to_decimal(150) - 2.5) < 0.001
    
    # Negative odds
    assert abs(american_to_decimal("-100") - 2.0) < 0.001
    assert abs(american_to_decimal("-200") - 1.5) < 0.001
    assert abs(american_to_decimal(-200) - 1.5) < 0.001
    
    # Edge cases
    with pytest.raises(ValueError):
        american_to_decimal("0")
    with pytest.raises(ValueError):
        american_to_decimal("invalid")


def test_decimal_to_implied_prob():
    """Test decimal odds to implied probability conversion."""
    # Even odds (2.0) should be 50%
    assert abs(decimal_to_implied_prob(2.0) - 0.5) < 0.001
    
    # 1.5 decimal odds should be 66.67%
    assert abs(decimal_to_implied_prob(1.5) - (2/3)) < 0.001
    
    # 3.0 decimal odds should be 33.33%
    assert abs(decimal_to_implied_prob(3.0) - (1/3)) < 0.001
    
    # Edge case
    with pytest.raises(ValueError):
        decimal_to_implied_prob(1.0)


def test_american_to_implied_prob():
    """Test direct American to implied probability conversion."""
    # +100 should be 50%
    assert abs(american_to_implied_prob("+100") - 0.5) < 0.001
    
    # -200 should be 66.67%
    assert abs(american_to_implied_prob("-200") - (2/3)) < 0.001


def test_edge_calculation():
    """Test edge calculation."""
    # Model thinks 60% chance, market implies 50% -> 10% edge
    assert abs(edge(0.6, 0.5) - 0.1) < 0.001
    
    # Model thinks 40% chance, market implies 50% -> -10% edge
    assert abs(edge(0.4, 0.5) - (-0.1)) < 0.001


def test_expected_value():
    """Test expected value calculation."""
    # 60% chance to win, 2.0 decimal odds
    # EV = 0.6 * (2.0 - 1) - 0.4 * 1 = 0.6 - 0.4 = 0.2
    assert abs(expected_value(0.6, 2.0) - 0.2) < 0.001
    
    # Losing bet: 40% chance to win, 2.0 decimal odds
    # EV = 0.4 * 1.0 - 0.6 * 1 = -0.2
    assert abs(expected_value(0.4, 2.0) - (-0.2)) < 0.001


def test_kelly_fraction():
    """Test Kelly criterion calculation."""
    # Perfect scenario: 60% chance, 2.0 decimal odds
    # Kelly = (0.6 * 1.0 - 0.4) / 1.0 = 0.2
    kelly = kelly_fraction(0.6, 2.0)
    assert abs(kelly - 0.2) < 0.001
    
    # No edge scenario
    kelly_no_edge = kelly_fraction(0.5, 2.0)
    assert kelly_no_edge == 0.0
    
    # Negative edge should return 0
    kelly_negative = kelly_fraction(0.4, 2.0)
    assert kelly_negative == 0.0
    
    # Half Kelly
    kelly_half = kelly_fraction(0.6, 2.0, 0.5)
    assert abs(kelly_half - 0.1) < 0.001


def test_suggested_stake():
    """Test suggested stake calculation."""
    bankroll = 1000.0
    
    # 60% chance, 2.0 odds, Kelly suggests 20% but capped at default 5%
    stake = suggested_stake(0.6, 2.0, bankroll)
    assert abs(stake - 50.0) < 0.001  # Capped at 5% = $50
    
    # Test with higher max stake limit
    stake_uncapped = suggested_stake(0.6, 2.0, bankroll, max_stake_pct=0.25)
    assert abs(stake_uncapped - 200.0) < 0.001  # Now shows full 20% Kelly
    
    # No edge should suggest $0
    stake_no_edge = suggested_stake(0.5, 2.0, bankroll)
    assert stake_no_edge == 0.0
    
    # Test max stake limit
    stake_limited = suggested_stake(0.8, 2.0, bankroll, max_stake_pct=0.01)
    assert stake_limited <= 10.0  # Should be capped at 1%


def test_round_trip_conversions():
    """Test round-trip conversions between odds formats."""
    test_odds = ["+100", "+150", "-120", "-200", "+250"]
    
    for odds in test_odds:
        decimal = american_to_decimal(odds)
        implied = decimal_to_implied_prob(decimal)
        
        # Basic sanity checks
        assert decimal > 1.0
        assert 0 < implied < 1.0
        
        # Implied prob should be consistent
        implied_direct = american_to_implied_prob(odds)
        assert abs(implied - implied_direct) < 0.001
