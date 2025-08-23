#!/usr/bin/env python
"""Launch Streamlit UI with live data pre-loaded."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime

from app.data.adapters.live_scraper import LiveDataScraper


def main():
    """Launch Streamlit with live data."""
    st.set_page_config(
        page_title="🔥 LIVE: Man City vs Tottenham",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔥 LIVE BETTING ANALYSIS")
    st.markdown("### Manchester City vs Tottenham Hotspur")
    
    # Get live data
    with st.spinner("🚀 Loading live match data..."):
        scraper = LiveDataScraper()
        live_data = scraper.get_live_match_data("Manchester City", "Tottenham")
    
    # Display match info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏠 Home Team", live_data['match_info']['home_team'])
    with col2:
        st.metric("✈️ Away Team", live_data['match_info']['away_team'])
    with col3:
        kickoff_time = datetime.fromisoformat(live_data['match_info']['kickoff_utc'].replace('Z', '+00:00'))
        st.metric("🕐 Kickoff", kickoff_time.strftime("%H:%M"))
    
    st.markdown("---")
    
    # Store data in session state
    st.session_state.lineups_df = pd.DataFrame(live_data['lineups'])
    st.session_state.player_stats_df = pd.DataFrame(live_data['player_stats'])
    st.session_state.team_stats_df = pd.DataFrame(live_data['team_stats'])
    st.session_state.odds_df = pd.DataFrame(live_data['odds'])
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⚽ Players", len(live_data['lineups']))
    with col2:
        st.metric("📊 Markets", len(live_data['odds']))
    with col3:
        home_players = len([p for p in live_data['lineups'] if p['team'] == live_data['match_info']['home_team']])
        st.metric("🏠 City XI", home_players)
    with col4:
        away_players = len([p for p in live_data['lineups'] if p['team'] == live_data['match_info']['away_team']])
        st.metric("✈️ Spurs XI", away_players)
    
    st.success("✅ Live data loaded! Go to the **Signals** tab to calculate value bets, or review the data in other tabs.")
    
    # Show key players
    st.markdown("### 🔥 Key Players to Watch")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏠 Manchester City**")
        city_stats = [p for p in live_data['player_stats'] if p['team'] == 'Manchester City' and p['shots_pg'] > 2]
        city_df = pd.DataFrame(city_stats)[['player_name', 'shots_pg', 'sot_pg', 'expected_minutes']]
        city_df.columns = ['Player', 'Shots/Game', 'SOT/Game', 'Exp. Minutes']
        city_df = city_df.sort_values('Shots/Game', ascending=False)
        st.dataframe(city_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**✈️ Tottenham**")
        spurs_stats = [p for p in live_data['player_stats'] if p['team'] == 'Tottenham' and p['shots_pg'] > 1.5]
        spurs_df = pd.DataFrame(spurs_stats)[['player_name', 'shots_pg', 'sot_pg', 'expected_minutes']]
        spurs_df.columns = ['Player', 'Shots/Game', 'SOT/Game', 'Exp. Minutes']
        spurs_df = spurs_df.sort_values('Shots/Game', ascending=False)
        st.dataframe(spurs_df, use_container_width=True, hide_index=True)
    
    # Show available odds
    st.markdown("### 💰 Available Betting Markets")
    odds_display = pd.DataFrame(live_data['odds'])
    odds_display = odds_display[['player_name', 'team', 'market', 'threshold', 'odds_american', 'book']]
    odds_display.columns = ['Player', 'Team', 'Market', 'Threshold', 'Odds', 'Book']
    st.dataframe(odds_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.info("🎯 **Next Step:** Click the **Signals** tab above to calculate value betting opportunities!")


if __name__ == "__main__":
    main()
