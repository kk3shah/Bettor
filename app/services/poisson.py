"""Poisson distribution calculations for player prop modeling."""
import math
from scipy.stats import poisson


def p_exact(k: int, lam: float) -> float:
    """Calculate P(X = k) for Poisson distribution with parameter lambda."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return poisson.pmf(k, lam)


def p_geq(k: int, lam: float) -> float:
    """Calculate P(X >= k) for Poisson distribution with parameter lambda."""
    if lam <= 0:
        return 1.0 if k <= 0 else 0.0
    if k <= 0:
        return 1.0
    return 1 - poisson.cdf(k - 1, lam)


def p_leq(k: int, lam: float) -> float:
    """Calculate P(X <= k) for Poisson distribution with parameter lambda."""
    if lam <= 0:
        return 1.0
    return poisson.cdf(k, lam)


def expected_value(lam: float) -> float:
    """Calculate expected value (mean) of Poisson distribution."""
    return lam


def variance(lam: float) -> float:
    """Calculate variance of Poisson distribution."""
    return lam
