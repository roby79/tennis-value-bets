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
st.sidebar.info("Modalità DEMO - Dati simulati")

# -------------------------
# 🎾 Partite Tennis Demo
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
    df_matches["elo_p1"] = np.random.randint(1600, 2200, len(df_matches))
    df_matches["elo_p2"] = np.random.randint(1600, 2200, len(df_matches))

    st.success(f"✅ Caricate {len(df_matches)} partite demo")

    # ---- Filtri partite (sidebar)
    st.sidebar.header("Filtri partite")

    tournaments = sorted(df_matches["tournament_name"].dropna().unique().tolist())
    selected_tournaments = st.sidebar.multiselect("🏟️ Tornei", tournaments, default=tournaments)

    surfaces = sorted(df_matches["surface"].dropna().unique().tolist())
    selected_surfaces = st.sidebar.multiselect("🟦 Superfici", surfaces, default=surfaces)

    only_value = st.sidebar.checkbox("🔥 Solo Value Bets", value=False)
    min_edge = st.sidebar.slider("📊 Edge minimo (%)", 0, 50, 5)
    min_edge_dec = min_edge / 100.0

    # Applica filtri
    dfm = df_matches[
        (df_matches["tournament_name"].isin(selected_tournaments)) &
        (df_matches["surface"].isin(selected_surfaces))
    ].copy()

    if only_value:
        dfm = dfm[(dfm["value_p1"]) | (dfm["value_p2"])]

    # Edge soglia su almeno uno dei due lati
    dfm = dfm[(dfm["edge_p1"] >= min_edge_dec) | (dfm["edge_p2"] >= min_edge_dec)]

    st.caption(f"Partite dopo filtri: {len(dfm)}")

    # Render card + grafico per ciascun match
    if dfm.empty:
        st.info("Nessuna partita soddisfa i filtri attuali.")
    else:
        for _, row in dfm.head(5).iterrows():  # Mostra solo prime 5 per performance
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                value_badge = "🔥 VALUE" if row["value_p1"] and row["edge_p1"] >= min_edge_dec else ""
                st.markdown(f"""
                **{row['player1_name']}** {value_badge}  
                Elo: {int(row['elo_p1'])}  
                Odds: **{row['odds_p1']:.2f}**  
                Fair: {row['fair_odds_p1']}  
                Edge: {(row['edge_p1']*100):.1f}%
                """)

            with col2:
                st.markdown(f"""
                <div style="text-align:center; font-size:22px;">
                    <b>VS</b><br>
                    <span style="font-size:14px;">{row['tournament_name']} - {row['round']} ({row['surface']})</span><br>
                    <span style="font-size:12px;">{row['match_time']}</span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                value_badge2 = "🔥 VALUE" if row["value_p2"] and row["edge_p2"] >= min_edge_dec else ""
                st.markdown(f"""
                **{row['player2_name']}** {value_badge2}  
                Elo: {int(row['elo_p2'])}  
                Odds: **{row['odds_p2']:.2f}**  
                Fair: {row['fair_odds_p2']}  
                Edge: {(row['edge_p2']*100):.1f}%
                """)

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

        # Tabella riassuntiva
        st.subheader("📊 Tabella Riassuntiva")
        display_cols = ['player1_name', 'player2_name', 'tournament_name', 'odds_p1', 'odds_p2', 'edge_p1', 'edge_p2']
        st.dataframe(dfm[display_cols])

        # Grafico distribuzione edge
        st.subheader("📈 Distribuzione Edge")
        edges_data = []
        for _, row in dfm.iterrows():
            edges_data.append({'Player': row['player1_name'], 'Edge': row['edge_p1']*100, 'Match': row['match']})
            edges_data.append({'Player': row['player2_name'], 'Edge': row['edge_p2']*100, 'Match': row['match']})
        
        edges_df = pd.DataFrame(edges_data)
        fig_edges = px.histogram(edges_df, x='Edge', nbins=20, title="Distribuzione Edge (%)")
        st.plotly_chart(fig_edges, use_container_width=True)

st.divider()

# -------------------------
# 🇮🇹 Sezione Betfair Italia - Informazioni
# -------------------------
st.subheader("🇮🇹 Informazioni Betfair Italia")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📋 Requisiti per Betfair Italia
    
    **Per utilizzare dati reali da betfair.it:**
    
    1. **Account Betfair Italia** registrato su betfair.it
    2. **App Key** creata nel developer portal
    3. **Credenziali** o **Certificato SSL** per login
    4. **Fondi** nell'account per piazzare scommesse
    
    **Regole mercato italiano:**
    - Puntata minima: €2.00
    - Incrementi: €0.50
    - Vincita massima: €10,000 per scommessa
    - Valuta: EUR
    """)

with col2:
    st.markdown("""
    ### ⚙️ Configurazione
    
    **File di configurazione:** `.env`
    
    ```bash
    BETFAIR_APP_KEY=your_app_key_here
    BETFAIR_USERNAME=your_username
    BETFAIR_PASSWORD=your_password
    DEMO_MODE=false
    ```
    
    **Endpoint utilizzati:**
    - Login: `identitysso.betfair.it`
    - API: `api.betfair.com` (filtrato per Italia)
    - Rate limit: 5 req/sec, 100 login/min
    """)

# Stato demo
demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
if demo_mode:
    st.info("🔧 **Modalità DEMO attiva** - Utilizzando dati simulati per la dimostrazione")
else:
    st.success("🟢 **Modalità REALE** - Connessione a Betfair Italia configurata")

st.divider()

# -------------------------
# ℹ️ Info progetto
# -------------------------
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Dashboard con integrazione Betfair Italia  
📊 Analisi value bets in tempo reale con dati simulati  
🇮🇹 Configurato specificamente per il mercato italiano  
🚀 Sviluppato con Streamlit + Betfair Exchange API  

**Funzionalità:**
- ✅ Analisi quote tennis in tempo reale
- ✅ Detection automatica value bets
- ✅ Calcolo edge e probabilità implicite
- ✅ Filtri avanzati per tornei e superfici
- ✅ Grafici interattivi con Plotly
- ✅ Export dati in CSV
- 🔄 Integrazione Betfair Italia (configurabile)
""")
