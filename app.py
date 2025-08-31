import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime

from db import DatabaseManager   # import della classe

# ⚙️ Configurazione pagina
st.set_page_config(
    page_title="Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Tema custom con CSS (bianco+viola stile mobile UI)
st.markdown(
    """
    <style>
    /* Sidebar viola */
    [data-testid="stSidebar"] {
        background-color: #7B1FA2 !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Bottoni */
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

    /* Titoli */
    h1, h2, h3, h4 {
        color: #4A148C;
        font-weight: 700;
    }

    /* Blocchi card */
    .stDataFrame, .stPlotlyChart, .element-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1.5em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inizializza DB
db = DatabaseManager()
    fig.update_traces(texttemplate='%{text:.0f}', textposition="outside")
fig.update_layout(xaxis_tickangle=-45)# Page config
st.set_page_config(
    page_title="Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_db():
    return DatabaseManager()

db = init_db()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .value-bet {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")

# Sidebar
st.sidebar.header("🔧 Filtri")
show_value_only = st.sidebar.checkbox("Mostra solo Value Bets", False)

# Refresh data
if st.sidebar.button("🔄 Aggiorna Dati"):
    st.cache_resource.clear()
    st.rerun()

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📅 Partite Oggi", "📊 Statistiche Giocatori", "💰 Info Progetto"])

with tab1:
    st.header("Partite di Oggi")
    
    matches_today = db.get_today_matches()
    
    if matches_today:
        match_data = []
        
        for m in matches_today:
            # Ottieni gli ID partendo dai nomi
            p1_id = db.get_player_by_name(m['player1_name'])
            p2_id = db.get_player_by_name(m['player2_name'])

            p1_stats = db.get_player_stats(p1_id) if p1_id else None
            p2_stats = db.get_player_stats(p2_id) if p2_id else None
            
            # Calcola probabilità basata su ELO
            if p1_stats and p2_stats:
                p1_elo = p1_stats.get('elo_rating', 1500)
                p2_elo = p2_stats.get('elo_rating', 1500)
                prob_p1 = 1 / (1 + 10 ** ((p2_elo - p1_elo) / 400))
                prob_p2 = 1 - prob_p1
            else:
                prob_p1 = prob_p2 = 0.5
            
            # Recupera quote mercato (MATCH ODDS)
            conn = db._connect()
            cur = conn.execute("""
                SELECT r.runner_name, p.back_price
                FROM runners r
                JOIN markets mkt ON r.market_id = mkt.id
                JOIN prices p ON r.id = p.runner_id
                WHERE mkt.match_id = ?
                ORDER BY p.timestamp DESC
                LIMIT 2
            """, (m['id'],))
            odds = cur.fetchall()
            conn.close()
            
            if len(odds) == 2:
                odds_p1 = odds[0][1]
                odds_p2 = odds[1][1]
            else:
                odds_p1 = odds_p2 = None
            
            # Calcola EV (expected value)
            ev_p1 = (prob_p1 * odds_p1 - 1) if odds_p1 else None
            ev_p2 = (prob_p2 * odds_p2 - 1) if odds_p2 else None
            
            match_data.append({
                "Ora": m['match_time'],
                "Torneo": m['tournament_name'],
                "Giocatore 1": m['player1_name'],
                "Giocatore 2": m['player2_name'],
                "Quota 1": odds_p1,
                "Quota 2": odds_p2,
                "Prob 1": round(prob_p1*100, 1),
                "Prob 2": round(prob_p2*100, 1),
                "EV 1": round(ev_p1*100, 1) if ev_p1 else None,
                "EV 2": round(ev_p2*100, 1) if ev_p2 else None,
            })
        
        st.dataframe(match_data, use_container_width=True)
    else:
        st.warning("Nessuna partita trovata per oggi.")

with tab3:
    st.header("💰 Info Progetto")
    
    st.markdown("""
    ### 🎾 Tennis Value Bets Dashboard
    
    Questa è una **demo funzionante** del progetto completo per l'analisi di value bets nel tennis.
    
    #### ✅ Cosa funziona già:
    - **Database SQLite** popolato con giocatori ATP/WTA reali
    - **Sistema ELO** per rating giocatori
    - **Partite mock** generate per oggi
    - **Dashboard interattiva** con filtri e grafici
    - **Struttura completa** pronta per integrazioni API
    
    #### 🚀 Prossimi passi per la versione completa:
    1. **Integrazione Betfair API** (credenziali in `.env`)
    2. **ETL automatico** per import partite reali
    3. **Modelli ML** avanzati per predizioni
    4. **Deploy su Streamlit Cloud** o Heroku
    
    #### 📁 File del progetto:
    - `app.py` - Questa dashboard Streamlit
    - `db.py` - Gestione database SQLite
    - `bootstrap.py` - Script di setup iniziale
    - `data/tennis.db` - Database con dati mock
    
    #### 🔧 Comandi utili:
    ```bash
    # Avvia l'app
    streamlit run app.py
    
    # Rigenera dati mock
    python3 bootstrap.py
    ```
    """)
    
    # Database stats
    st.subheader("📊 Statistiche Database")
    
    with sqlite3.connect("data/tennis.db") as conn:
        players_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        matches_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        tournaments_count = conn.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Giocatori", players_count)
    with col2:
        st.metric("Partite", matches_count)
    with col3:
        st.metric("Tornei", tournaments_count)

# Footer
st.markdown("---")
st.markdown("🎾 **Tennis Value Bets** - Demo Dashboard con dati mock")
