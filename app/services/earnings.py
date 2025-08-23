"""Expected earnings calculations for betting opportunities."""
from typing import List, Dict, Tuple
import pandas as pd
from .value import american_to_decimal, expected_value
from .poisson import p_geq


def calculate_expected_earnings(signals: List[Dict], bankroll: float = 1000.0) -> Dict:
    """Calculate expected earnings from a list of betting signals."""
    
    if not signals:
        return {
            'total_stakes': 0,
            'expected_profit': 0,
            'expected_roi': 0,
            'win_probability': 0,
            'scenarios': []
        }
    
    total_stakes = sum(signal['suggested_stake'] for signal in signals)
    
    # Calculate expected value for each bet
    expected_values = []
    for signal in signals:
        decimal_odds = american_to_decimal(signal['odds'])
        ev = expected_value(signal['model_prob'], decimal_odds)
        expected_values.append(ev * signal['suggested_stake'])
    
    total_expected_profit = sum(expected_values)
    expected_roi = (total_expected_profit / total_stakes * 100) if total_stakes > 0 else 0
    
    # Calculate overall win probability (simplified)
    avg_win_prob = sum(signal['model_prob'] for signal in signals) / len(signals)
    
    # Generate scenarios
    scenarios = generate_profit_scenarios(signals, bankroll)
    
    return {
        'total_stakes': round(total_stakes, 2),
        'expected_profit': round(total_expected_profit, 2),
        'expected_roi': round(expected_roi, 1),
        'win_probability': round(avg_win_prob, 3),
        'scenarios': scenarios,
        'num_bets': len(signals),
        'bankroll_utilization': round(total_stakes / bankroll * 100, 1)
    }


def generate_profit_scenarios(signals: List[Dict], bankroll: float) -> List[Dict]:
    """Generate different profit scenarios based on win rates."""
    
    scenarios = []
    
    # Scenario 1: All bets lose
    total_loss = sum(signal['suggested_stake'] for signal in signals)
    scenarios.append({
        'name': 'Worst Case (All Lose)',
        'probability': calculate_all_lose_prob(signals),
        'profit': -total_loss,
        'roi': -total_loss / bankroll * 100
    })
    
    # Scenario 2: Expected outcome (based on model probabilities)
    expected_profit = 0
    for signal in signals:
        decimal_odds = american_to_decimal(signal['odds'])
        stake = signal['suggested_stake']
        win_prob = signal['model_prob']
        
        # Expected value = (win_prob * profit) - (lose_prob * stake)
        profit_if_win = stake * (decimal_odds - 1)
        expected_profit += win_prob * profit_if_win - (1 - win_prob) * stake
    
    scenarios.append({
        'name': 'Expected Outcome',
        'probability': 'Model-based',
        'profit': round(expected_profit, 2),
        'roi': round(expected_profit / bankroll * 100, 1)
    })
    
    # Scenario 3: 50% win rate
    profit_50pct = calculate_scenario_profit(signals, 0.5)
    scenarios.append({
        'name': '50% Win Rate',
        'probability': 0.5,
        'profit': round(profit_50pct, 2),
        'roi': round(profit_50pct / bankroll * 100, 1)
    })
    
    # Scenario 4: High win rate (80%)
    profit_80pct = calculate_scenario_profit(signals, 0.8)
    scenarios.append({
        'name': '80% Win Rate',
        'probability': 0.8,
        'profit': round(profit_80pct, 2),
        'roi': round(profit_80pct / bankroll * 100, 1)
    })
    
    # Scenario 5: Best case (all win)
    total_profit_all_win = 0
    for signal in signals:
        decimal_odds = american_to_decimal(signal['odds'])
        stake = signal['suggested_stake']
        profit_if_win = stake * (decimal_odds - 1)
        total_profit_all_win += profit_if_win
    
    scenarios.append({
        'name': 'Best Case (All Win)',
        'probability': calculate_all_win_prob(signals),
        'profit': round(total_profit_all_win, 2),
        'roi': round(total_profit_all_win / bankroll * 100, 1)
    })
    
    return scenarios


def calculate_all_lose_prob(signals: List[Dict]) -> float:
    """Calculate probability that all bets lose."""
    prob = 1.0
    for signal in signals:
        prob *= (1 - signal['model_prob'])
    return round(prob, 4)


def calculate_all_win_prob(signals: List[Dict]) -> float:
    """Calculate probability that all bets win."""
    prob = 1.0
    for signal in signals:
        prob *= signal['model_prob']
    return round(prob, 4)


def calculate_scenario_profit(signals: List[Dict], win_rate: float) -> float:
    """Calculate profit assuming a fixed win rate."""
    total_profit = 0
    
    for signal in signals:
        decimal_odds = american_to_decimal(signal['odds'])
        stake = signal['suggested_stake']
        
        # Profit if win vs loss if lose
        profit_if_win = stake * (decimal_odds - 1)
        loss_if_lose = -stake
        
        expected_profit = win_rate * profit_if_win + (1 - win_rate) * loss_if_lose
        total_profit += expected_profit
    
    return total_profit


def format_earnings_report(earnings: Dict, signals: List[Dict]) -> str:
    """Format a comprehensive earnings report."""
    
    report = []
    report.append("💰 EXPECTED EARNINGS ANALYSIS")
    report.append("=" * 50)
    report.append(f"📊 Total Bets: {earnings['num_bets']}")
    report.append(f"💵 Total Stakes: ${earnings['total_stakes']}")
    report.append(f"🎯 Expected Profit: ${earnings['expected_profit']}")
    report.append(f"📈 Expected ROI: {earnings['expected_roi']}%")
    report.append(f"🏦 Bankroll Used: {earnings['bankroll_utilization']}%")
    report.append("")
    
    report.append("🎲 PROFIT SCENARIOS:")
    report.append("-" * 30)
    for scenario in earnings['scenarios']:
        prob_str = f"{scenario['probability']:.1%}" if isinstance(scenario['probability'], float) else scenario['probability']
        report.append(f"{scenario['name']}: ${scenario['profit']} ({scenario['roi']:+.1f}% ROI) [{prob_str}]")
    
    report.append("")
    report.append("🏆 TOP VALUE BETS:")
    report.append("-" * 30)
    
    # Sort signals by edge
    top_signals = sorted(signals, key=lambda x: x['edge'], reverse=True)[:5]
    for i, signal in enumerate(top_signals, 1):
        decimal_odds = american_to_decimal(signal['odds'])
        potential_profit = signal['suggested_stake'] * (decimal_odds - 1)
        report.append(f"{i}. {signal['player']} - {signal['prop']}")
        report.append(f"   Stake: ${signal['suggested_stake']} → Potential: ${potential_profit:.2f} ({signal['model_prob']:.1%} chance)")
    
    return "\n".join(report)
