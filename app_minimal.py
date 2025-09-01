import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()
load_dotenv('.env.betfair')

# Configurazione logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

def generate_mock_tennis_data():
    """Genera dati tennis simulati per modalità demo"""
    np.random.seed(42)
    
    tournaments = ["ATP Masters 1000 Roma", "WTA 1000 Roma", "ATP 250 Firenze", "WTA 250 Palermo"]
    players = [
        "Jannik Sinner", "Matteo Berrettini", "Lorenzo Musetti", "Fabio Fognini",
        "Jasmine Paolini", "Martina Trevisan", "Lucia Bronzetti", "Elisabetta Cocciaretto",
        "Novak Djokovic", "Carlos Alcaraz", "Rafael Nadal", "Daniil Medvedev",
        "Iga Swiatek", "Aryna Sabalenka", "Coco Gauff", "Jessica Pegula"
    ]
    
    matches_data = []
    for i in range(15):
        p1, p2 = np.random.choice(players, 2, replace=False)
        p1_odds = np.random.uniform(1.5, 4.0)
        p2_odds = np.random.uniform(1.5, 4.0)
        
        matches_data.append({
            'match': f"{p1} vs {p2}",
            'tournament': np.random.choice(tournaments),
            'player1': p1,
            'player2': p2,
            'player1_odds': round(p1_odds, 2),
            'player2_odds': round(p2_odds, 2),
            'player1_prob': round(1/p1_odds, 3),
            'player2_prob': round(1/p2_odds, 3),
            'market_id': f"mock_{i}",
            'start_time': datetime.now().isoformat(),
            'value_bet': np.random.choice([True, False], p=[0.3, 0.7])
        })
    
    return pd.DataFrame(matches_data)

# ⚙️ Configurazione pagina
st.set_page_config(
    page_title="Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Tema custom con CSS (bianco+viola)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #7B1FA2 !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .stButton>button {
        background-color: #7B1FA2;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #9C27B0;
        color: #fff;
    }
    h1, h2, h3, h4 {
        color: #4A148C;
        font-weight: 700;
    }
    .match-card {
        background:#f6f6f6;
        padding:10px;
        border-radius:8px;
        text-align:center;
    }
    .stDataFrame, .stPlotlyChart, .element-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1.5em;
    }
    .badge {
        display:inline-block;
        padding:2px 8px;
        border-radius:12px;
        font-size:12px;
        font-weight:700;
        color:#fff;
        background:#2e7d32;
        margin-left:6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🎾 Titolo principale
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")
st.success("🚀 App caricata correttamente!")

# 🔧 Sidebar azioni
st.sidebar.header("🔧 Azioni")
st.sidebar.info("Versione semplificata - solo dati mock")

# -------------------------
# 🎾 Partite Tennis Mock Data
# -------------------------
st.subheader("🎾 Tennis Live - Dati Demo")

# Genera dati mock
with st.spinner("Caricamento dati tennis demo..."):
    df_matches = generate_mock_tennis_data()

if not df_matches.empty:
    # Calcola fair odds basate su probabilità implicite
    df_matches["fair_odds_p1"] = (1 / df_matches["player1_prob"]).round(2)
    df_matches["fair_odds_p2"] = (1 / df_matches["player2_prob"]).round(2)

    # Rinomina colonne per compatibilità
    df_matches = df_matches.rename(columns={
        'player1_odds': 'odds_p1',
        'player2_odds': 'odds_p2',
        'player1': 'player1_name',
        'player2': 'player2_name',
        'tournament': 'tournament_name'
    })

    # Aggiungi colonne mancanti
    df_matches["surface"] = "Hard"
    df_matches["round"] = "R1"
    df_matches["match_time"] = pd.to_datetime(df_matches["start_time"]).dt.strftime("%H:%M")

    # Value Bet check
    df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
    df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]

    # Edge come scostamento percentuale vs fair odds
    df_matches["edge_p1"] = ((df_matches["odds_p1"] / df_matches["fair_odds_p1"] - 1)).round(3)
    df_matches["edge_p2"] = ((df_matches["odds_p2"] / df_matches["fair_odds_p2"] - 1)).round(3)

    # Aggiungi Elo fittizi
    df_matches["elo_p1"] = 1800
    df_matches["elo_p2"] = 1800

    st.success(f"✅ Caricate {len(df_matches)} partite demo")

    # Mostra prime 5 partite
    for _, row in df_matches.head(5).iterrows():
        col1, col2, col3 = st.columns([4, 2, 4])

        with col1:
            badge_html = '<span class="badge">VALUE</span>' if row["value_p1"] else ""
            st.markdown(f"""
            <div class="match-card">
                <b>{row['player1_name']}</b> {badge_html}<br>
                Elo: {int(row['elo_p1'])}<br>
                Odds: {row['odds_p1']:.2f}<br>
                Fair: {row['fair_odds_p1']}<br>
                Edge: {(row['edge_p1']*100):.1f}%
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="text-align:center; font-size:22px;">
                <b>VS</b><br>
                <span style="font-size:14px;">{row['tournament_name']} - {row['round']} ({row['surface']})</span><br>
                <span style="font-size:12px;">{row['match_time']}</span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            badge_html2 = '<span class="badge">VALUE</span>' if row["value_p2"] else ""
            st.markdown(f"""
            <div class="match-card">
                <b>{row['player2_name']}</b> {badge_html2}<br>
                Elo: {int(row['elo_p2'])}<br>
                Odds: {row['odds_p2']:.2f}<br>
                Fair: {row['fair_odds_p2']}<br>
                Edge: {(row['edge_p2']*100):.1f}%
            </div>
            """, unsafe_allow_html=True)

        # Grafico quote vs fair
        fig_match = px.bar(
            x=["Odds P1", "Fair P1", "Odds P2", "Fair P2"],
            y=[row['odds_p1'], row['fair_odds_p1'], row['odds_p2'], row['fair_odds_p2']],
            color=["Real", "Fair", "Real", "Fair"],
            title=f"Confronto Quote - {row['player1_name']} vs {row['player2_name']}",
            text=[row['odds_p1'], row['fair_odds_p1'], row['odds_p2'], row['fair_odds_p2']]
        )
        fig_match.update_traces(texttemplate='%{text:.2f}', textposition="outside")
        fig_match.update_layout(yaxis_title="Quota", xaxis_title="", showlegend=False, height=380)
        st.plotly_chart(fig_match, use_container_width=True)

        st.markdown("---")

st.divider()

# -------------------------
# ℹ️ Info progetto
# -------------------------
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Dashboard con integrazione Betfair Italia  
📊 Versione semplificata con dati demo  
🇮🇹 Configurato specificamente per il mercato italiano  
🚀 Sviluppato con Streamlit + Betfair Exchange API  
""")
