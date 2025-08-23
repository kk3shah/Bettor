"""Tests for Poisson distribution calculations."""
import pytest
import math
from app.services.poisson import p_geq, p_exact, expected_value, variance


def test_p_exact():
    """Test exact probability calculations."""
    # P(X = 0) when lambda = 2 should be e^(-2) ≈ 0.1353
    assert abs(p_exact(0, 2.0) - math.exp(-2)) < 0.0001
    
    # P(X = 2) when lambda = 2 should be 2^2 * e^(-2) / 2! ≈ 0.2707
    expected = (2**2 * math.exp(-2)) / math.factorial(2)
    assert abs(p_exact(2, 2.0) - expected) < 0.0001
    
    # Edge case: lambda = 0
    assert p_exact(0, 0.0) == 1.0
    assert p_exact(1, 0.0) == 0.0


def test_p_geq():
    """Test greater-than-or-equal probability calculations."""
    # P(X >= 0) should always be 1
    assert p_geq(0, 2.0) == 1.0
    
    # P(X >= k) should decrease as k increases
    assert p_geq(1, 2.0) > p_geq(2, 2.0)
    assert p_geq(2, 2.0) > p_geq(3, 2.0)
    
    # Edge cases
    assert p_geq(0, 0.0) == 1.0
    assert p_geq(1, 0.0) == 0.0


def test_complementary_probabilities():
    """Test that P(X >= k) + P(X < k) = 1."""
    lam = 3.5
    k = 4
    
    # P(X >= k) + P(X < k) should equal 1
    # P(X < k) = P(X <= k-1) = sum of P(X = i) for i = 0 to k-1
    p_geq_k = p_geq(k, lam)
    p_less_k = sum(p_exact(i, lam) for i in range(k))
    
    assert abs(p_geq_k + p_less_k - 1.0) < 0.0001


def test_expected_value_and_variance():
    """Test expected value and variance calculations."""
    lam = 2.5
    assert expected_value(lam) == lam
    assert variance(lam) == lam


def test_boundary_conditions():
    """Test boundary conditions and edge cases."""
    # Very small lambda
    small_lam = 0.001
    assert p_geq(0, small_lam) == 1.0
    assert p_geq(1, small_lam) < 0.01
    
    # Large lambda
    large_lam = 100.0
    assert p_geq(50, large_lam) > 0.5  # Should be roughly around the mean
