"""Streamlit UI for Football Betting MVP."""
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.components import (
    upload_csv_component, config_panel, lineup_editor, 
    value_bets_table, metrics_overview, filter_panel
)

# Page configuration
st.set_page_config(
    page_title="Football Betting MVP",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("⚽ Football Betting MVP")
st.markdown("---")
st.write("Calculate player prop probabilities and find value betting opportunities")

# Configuration panel
config = config_panel()

# Initialize session state
if 'lineups_df' not in st.session_state:
    st.session_state.lineups_df = None
if 'player_stats_df' not in st.session_state:
    st.session_state.player_stats_df = None
if 'team_stats_df' not in st.session_state:
    st.session_state.team_stats_df = None
if 'odds_df' not in st.session_state:
    st.session_state.odds_df = None

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Lineups", "📊 Player Stats", "🏟️ Team Stats", "💰 Odds", "🎯 Signals"])

# Tab 1: Lineups
with tab1:
    st.header("📋 Confirmed Lineups")
    
    lineups_df = upload_csv_component(
        "Lineups Data",
        "Upload confirmed starting lineups with expected playing time",
        ["match_id", "kickoff_utc", "home_team", "away_team", "player_name", "team", "is_starter", "expected_minutes"]
    )
    
    if lineups_df is not None:
        st.session_state.lineups_df = lineup_editor(lineups_df)
        
        # Show summary
        st.subheader("📈 Lineup Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Players", len(lineups_df))
        with col2:
            st.metric("Matches", lineups_df['match_id'].nunique())
        with col3:
            st.metric("Teams", lineups_df['team'].nunique())

# Tab 2: Player Stats
with tab2:
    st.header("📊 Player Statistics")
    
    player_stats_df = upload_csv_component(
        "Player Stats Data",
        "Upload player performance statistics (season averages)",
        ["player_name", "team", "minutes_per_app", "shots_pg", "sot_pg", "fouls_pg", "passes_pg", "yc_pg", "apps"]
    )
    
    if player_stats_df is not None:
        st.session_state.player_stats_df = player_stats_df
        
        # Show top performers
        st.subheader("🏆 Top Shot-Takers")
        top_shooters = player_stats_df.nlargest(10, 'shots_pg')[['player_name', 'team', 'shots_pg', 'sot_pg']]
        st.dataframe(top_shooters, use_container_width=True)

# Tab 3: Team Stats
with tab3:
    st.header("🏟️ Team Statistics")
    
    team_stats_df = upload_csv_component(
        "Team Stats Data",
        "Upload team defensive and offensive statistics",
        ["team", "goals_for_pg", "goals_against_pg", "shots_allowed_pg", "cards_pg"]
    )
    
    if team_stats_df is not None:
        st.session_state.team_stats_df = team_stats_df
        
        # Show team comparison
        st.subheader("⚔️ Defensive Comparison")
        defense_stats = team_stats_df[['team', 'goals_against_pg', 'shots_allowed_pg']].copy()
        defense_stats = defense_stats.sort_values('shots_allowed_pg')
        st.dataframe(defense_stats, use_container_width=True)

# Tab 4: Odds
with tab4:
    st.header("💰 Betting Odds")
    
    odds_df = upload_csv_component(
        "Odds Data",
        "Upload current betting odds from sportsbooks",
        ["match_id", "market", "player_name", "team", "threshold", "odds_american", "book"]
    )
    
    if odds_df is not None:
        st.session_state.odds_df = odds_df
        
        # Show odds summary
        st.subheader("📊 Odds Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Markets", len(odds_df))
        with col2:
            st.metric("Unique Players", odds_df['player_name'].nunique())
        with col3:
            st.metric("Sportsbooks", odds_df['book'].nunique())

# Tab 5: Signals
with tab5:
    st.header("🎯 Value Betting Signals")
    
    # Check if all data is loaded
    all_data_loaded = all([
        st.session_state.lineups_df is not None,
        st.session_state.player_stats_df is not None,
        st.session_state.team_stats_df is not None,
        st.session_state.odds_df is not None
    ])
    
    if not all_data_loaded:
        st.warning("⚠️ Please load all required data in the previous tabs before calculating signals.")
        missing = []
        if st.session_state.lineups_df is None:
            missing.append("Lineups")
        if st.session_state.player_stats_df is None:
            missing.append("Player Stats")
        if st.session_state.team_stats_df is None:
            missing.append("Team Stats")
        if st.session_state.odds_df is None:
            missing.append("Odds")
        st.write(f"Missing: {', '.join(missing)}")
    else:
        # Calculate signals button
        if st.button("🚀 Calculate Value Signals", type="primary", use_container_width=True):
            with st.spinner("Calculating value betting signals..."):
                try:
                    # Prepare data for API call
                    payload = {
                        "lineups": st.session_state.lineups_df.to_dict('records'),
                        "player_stats": st.session_state.player_stats_df.to_dict('records'),
                        "team_stats": st.session_state.team_stats_df.to_dict('records'),
                        "odds": st.session_state.odds_df.to_dict('records')
                    }
                    
                    # Try to call the API (if running), otherwise calculate locally
                    try:
                        response = requests.post(
                            f"http://localhost:8000/signals/value-bets?bankroll={config['bankroll']}", 
                            json=payload,
                            timeout=30
                        )
                        if response.status_code == 200:
                            signals = response.json()['signals']
                        else:
                            st.error(f"API Error: {response.status_code} - {response.text}")
                            signals = []
                    except requests.exceptions.ConnectionError:
                        st.warning("⚠️ API not available, calculating locally...")
                        
                        # Local calculation fallback
                        from app.services.poisson import p_geq
                        from app.services.value import american_to_decimal, american_to_implied_prob, edge, suggested_stake
                        from app.services.adjust import compound_adjustments
                        
                        signals = []
                        
                        # Create lookups
                        lineups_dict = {}
                        for _, lineup in st.session_state.lineups_df.iterrows():
                            key = (lineup['match_id'], lineup['player_name'], lineup['team'])
                            lineups_dict[key] = lineup
                        
                        player_stats_dict = {}
                        for _, player in st.session_state.player_stats_df.iterrows():
                            key = (player['player_name'], player['team'])
                            player_stats_dict[key] = player
                        
                        team_stats_dict = {}
                        for _, team in st.session_state.team_stats_df.iterrows():
                            team_stats_dict[team['team']] = team
                        
                        # Calculate signals
                        for _, odds_row in st.session_state.odds_df.iterrows():
                            lineup_key = (odds_row['match_id'], odds_row['player_name'], odds_row['team'])
                            player_key = (odds_row['player_name'], odds_row['team'])
                            
                            if lineup_key not in lineups_dict or player_key not in player_stats_dict:
                                continue
                            
                            lineup = lineups_dict[lineup_key]
                            player_stats = player_stats_dict[player_key]
                            
                            # Determine opponent
                            opponent_team = lineup['away_team'] if lineup['team'] == lineup['home_team'] else lineup['home_team']
                            opponent_stats = team_stats_dict.get(opponent_team)
                            
                            # Calculate adjusted lambda
                            is_home = lineup['team'] == lineup['home_team']
                            opponent_shots_allowed = opponent_stats['shots_allowed_pg'] if opponent_stats is not None else config['league_avg_shots']
                            
                            adjusted_lambda = compound_adjustments(
                                base_lam=player_stats['shots_pg'],
                                expected_minutes=lineup['expected_minutes'],
                                opponent_shots_allowed=opponent_shots_allowed,
                                league_avg_shots_allowed=config['league_avg_shots'],
                                is_home=is_home,
                                home_mult=config['home_mult'],
                                away_mult=config['away_mult']
                            )
                            
                            # Calculate probabilities and value
                            model_prob = p_geq(odds_row['threshold'], adjusted_lambda)
                            implied_prob = american_to_implied_prob(odds_row['odds_american'])
                            prob_edge = edge(model_prob, implied_prob)
                            
                            if prob_edge > 0:
                                decimal_odds = american_to_decimal(odds_row['odds_american'])
                                stake = suggested_stake(model_prob, decimal_odds, config['bankroll'], config['kelly_fraction'])
                                kelly_fraction = stake / config['bankroll'] if config['bankroll'] > 0 else 0
                                
                                signals.append({
                                    'match_id': odds_row['match_id'],
                                    'player': odds_row['player_name'],
                                    'prop': f"{odds_row['market']} ≥ {odds_row['threshold']}",
                                    'threshold': odds_row['threshold'],
                                    'model_prob': model_prob,
                                    'implied_prob': implied_prob,
                                    'edge': prob_edge,
                                    'odds': odds_row['odds_american'],
                                    'kelly': kelly_fraction,
                                    'suggested_stake': stake
                                })
                        
                        # Sort by edge
                        signals.sort(key=lambda x: x['edge'], reverse=True)
                    
                    # Store in session state
                    st.session_state.signals = signals
                    
                    st.success(f"✅ Found {len(signals)} value betting opportunities!")
                    
                except Exception as e:
                    st.error(f"Error calculating signals: {str(e)}")
                    st.session_state.signals = []
        
        # Display signals if available
        if 'signals' in st.session_state and st.session_state.signals:
            # Metrics overview
            metrics_overview(st.session_state.signals)
            st.markdown("---")
            
            # Filter panel
            filtered_signals = filter_panel(st.session_state.signals)
            
            # Display results
            if filtered_signals:
                st.subheader("📈 Value Betting Opportunities")
                value_bets_table(filtered_signals)
            else:
                st.warning("No signals match the current filters.")

# Footer
st.markdown("---")
st.markdown(
    "⚠️ **Disclaimer**: This tool is for educational purposes only. "
    "Sports betting involves risk. Please bet responsibly and within your means."
)
