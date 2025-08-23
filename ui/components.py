"""Streamlit UI components and helpers."""
import streamlit as st
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import io


def upload_csv_component(label: str, help_text: str, sample_columns: list) -> Optional[pd.DataFrame]:
    """Component for CSV upload with textarea fallback."""
    st.subheader(label)
    st.write(help_text)
    
    # Show expected columns
    with st.expander("Expected CSV format"):
        st.code(", ".join(sample_columns))
    
    # Upload method selection
    upload_method = st.radio(f"How would you like to provide {label}?", 
                           ["Upload CSV file", "Paste CSV data"], 
                           key=f"method_{label}")
    
    df = None
    
    if upload_method == "Upload CSV file":
        uploaded_file = st.file_uploader(
            f"Choose {label} CSV file", 
            type="csv", 
            key=f"upload_{label}"
        )
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows")
                with st.expander("Preview data"):
                    st.dataframe(df.head())
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
    
    else:  # Paste CSV data
        csv_text = st.text_area(
            f"Paste {label} CSV data", 
            height=200, 
            key=f"paste_{label}",
            help="Paste your CSV data here, including headers"
        )
        if csv_text.strip():
            try:
                df = pd.read_csv(io.StringIO(csv_text))
                st.success(f"✅ Parsed {len(df)} rows")
                with st.expander("Preview data"):
                    st.dataframe(df.head())
            except Exception as e:
                st.error(f"Error parsing CSV: {str(e)}")
    
    return df


def config_panel() -> Dict[str, Any]:
    """Configuration panel for model parameters."""
    st.sidebar.header("⚙️ Model Configuration")
    
    config = {}
    
    # Home/Away multipliers
    st.sidebar.subheader("Home/Away Advantage")
    config['home_mult'] = st.sidebar.slider("Home multiplier", 0.95, 1.15, 1.05, 0.01)
    config['away_mult'] = st.sidebar.slider("Away multiplier", 0.85, 1.05, 0.95, 0.01)
    
    # League averages
    st.sidebar.subheader("League Averages")
    config['league_avg_shots'] = st.sidebar.number_input("Average shots allowed per game", 5.0, 20.0, 10.5, 0.5)
    
    # Recent form
    st.sidebar.subheader("Recent Form")
    config['recent_weight'] = st.sidebar.slider("Recent form weight", 0.0, 1.0, 0.0, 0.1)
    
    # Kelly criterion
    st.sidebar.subheader("Betting Strategy")
    config['kelly_fraction'] = st.sidebar.slider("Kelly fraction", 0.1, 1.0, 1.0, 0.1)
    config['bankroll'] = st.sidebar.number_input("Bankroll ($)", 100, 50000, 1000, 100)
    config['max_stake_pct'] = st.sidebar.slider("Max stake %", 0.01, 0.25, 0.05, 0.01)
    
    return config


def lineup_editor(df: pd.DataFrame) -> pd.DataFrame:
    """Interactive lineup editor for expected minutes."""
    if df is None or df.empty:
        return df
    
    st.subheader("📝 Edit Expected Minutes")
    
    # Create editable dataframe
    edited_df = df.copy()
    
    # Group by match for easier editing
    matches = edited_df['match_id'].unique()
    
    for match in matches:
        match_data = edited_df[edited_df['match_id'] == match]
        
        with st.expander(f"📅 {match}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("🏠 **Home Team**")
                home_team = match_data['home_team'].iloc[0]
                home_players = match_data[match_data['team'] == home_team]
                
                for idx, row in home_players.iterrows():
                    new_mins = st.number_input(
                        f"{row['player_name']}", 
                        min_value=0, 
                        max_value=90, 
                        value=int(row['expected_minutes']),
                        key=f"home_{idx}"
                    )
                    edited_df.loc[idx, 'expected_minutes'] = new_mins
            
            with col2:
                st.write("✈️ **Away Team**")
                away_team = match_data['away_team'].iloc[0]
                away_players = match_data[match_data['team'] == away_team]
                
                for idx, row in away_players.iterrows():
                    new_mins = st.number_input(
                        f"{row['player_name']}", 
                        min_value=0, 
                        max_value=90, 
                        value=int(row['expected_minutes']),
                        key=f"away_{idx}"
                    )
                    edited_df.loc[idx, 'expected_minutes'] = new_mins
    
    return edited_df


def value_bets_table(signals: list) -> None:
    """Display value bets in a formatted table."""
    if not signals:
        st.warning("No value bets found with current parameters.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame([{
        'Match': signal['match_id'],
        'Player': signal['player'],
        'Prop': signal['prop'],
        'Model Prob': f"{signal['model_prob']:.1%}",
        'Implied Prob': f"{signal['implied_prob']:.1%}",
        'Edge': f"{signal['edge']:.1%}",
        'Odds': signal['odds'],
        'Kelly %': f"{signal['kelly']:.1%}",
        'Suggested Stake': f"${signal['suggested_stake']:.2f}"
    } for signal in signals])
    
    # Color coding for edges
    def highlight_edge(val):
        if 'Edge' not in val.name:
            return ''
        edge_val = float(val.replace('%', ''))
        if edge_val >= 10:
            return 'background-color: #d4edda'  # Green
        elif edge_val >= 5:
            return 'background-color: #fff3cd'  # Yellow
        return ''
    
    st.dataframe(
        df.style.applymap(highlight_edge),
        use_container_width=True
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="value_bets.csv",
        mime="text/csv"
    )


def metrics_overview(signals: list) -> None:
    """Display key metrics overview."""
    if not signals:
        return
    
    total_bets = len(signals)
    avg_edge = sum(s['edge'] for s in signals) / total_bets if total_bets > 0 else 0
    total_stake = sum(s['suggested_stake'] for s in signals)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bets", total_bets)
    
    with col2:
        st.metric("Avg Edge", f"{avg_edge:.1%}")
    
    with col3:
        st.metric("Total Stake", f"${total_stake:.2f}")
    
    with col4:
        best_bet = max(signals, key=lambda x: x['edge'])
        st.metric("Best Edge", f"{best_bet['edge']:.1%}")


def filter_panel(signals: list) -> list:
    """Filter panel for value bets."""
    if not signals:
        return signals
    
    st.subheader("🔍 Filter Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_edge = st.slider("Minimum Edge %", 0.0, 50.0, 0.0, 0.5) / 100
    
    with col2:
        min_prob = st.slider("Minimum Model Prob %", 0.0, 100.0, 0.0, 1.0) / 100
    
    with col3:
        matches = list(set(s['match_id'] for s in signals))
        selected_matches = st.multiselect("Matches", matches, default=matches)
    
    # Apply filters
    filtered = [
        s for s in signals
        if s['edge'] >= min_edge
        and s['model_prob'] >= min_prob
        and s['match_id'] in selected_matches
    ]
    
    return filtered
