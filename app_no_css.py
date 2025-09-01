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

# 🎾 Titolo principale
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")
st.success("🚀 App caricata correttamente!")

# 🔧 Sidebar azioni
st.sidebar.header("🔧 Azioni")
st.sidebar.info("Versione senza CSS personalizzato")

# -------------------------
# 🎾 Partite Tennis Mock Data
# -------------------------
st.subheader("🎾 Tennis Live - Dati Demo")

# Genera dati mock
with st.spinner("Caricamento dati tennis demo..."):
    df_matches = generate_mock_tennis_data()

if not df_matches.empty:
    st.success(f"✅ Caricate {len(df_matches)} partite demo")
    
    # Mostra tabella semplice
    st.dataframe(df_matches[['player1', 'player2', 'tournament', 'player1_odds', 'player2_odds']].head(10))
    
    # Grafico semplice
    fig = px.bar(
        df_matches.head(5),
        x='match',
        y=['player1_odds', 'player2_odds'],
        title="Quote delle prime 5 partite",
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------
# ℹ️ Info progetto
# -------------------------
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Dashboard con integrazione Betfair Italia  
📊 Versione senza CSS personalizzato  
🇮🇹 Configurato specificamente per il mercato italiano  
🚀 Sviluppato con Streamlit + Betfair Exchange API  
""")
