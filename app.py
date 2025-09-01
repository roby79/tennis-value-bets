import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

from db import DatabaseManager
from services.betfair_session import BetfairItalySession
from services.betfair_client import BetfairItalyClient
from config.betfair_it import TENNIS_CONFIG, ITALIAN_BETTING_RULES

# Carica variabili ambiente
load_dotenv()
load_dotenv('.env.betfair')

# Configurazione logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

# Inizializzazione client Betfair (cached per performance)
@st.cache_resource
def init_betfair_client():
    """Inizializza il client Betfair Italia con caching"""
    try:
        st.info("🔄 Inizializzazione client Betfair...")
        app_key = os.getenv('BETFAIR_APP_KEY')
        username = os.getenv('BETFAIR_USERNAME')
        password = os.getenv('BETFAIR_PASSWORD')
        demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
        
        st.info(f"📋 Demo mode: {demo_mode}, App key presente: {bool(app_key)}")
        
        if demo_mode or not app_key:
            st.warning("⚠️ Modalità DEMO attiva - usando dati simulati")
            return None
        
        st.info("🔗 Creazione sessione Betfair...")
        session = BetfairItalySession(app_key, username, password)
        st.info("🔗 Creazione client Betfair...")
        client = BetfairItalyClient(session)
        st.success("✅ Client Betfair inizializzato")
        return client
    except Exception as e:
        st.error(f"❌ Errore inizializzazione Betfair: {e}")
        return None

def get_tennis_data_betfair(client):
    """Recupera dati tennis reali da Betfair Italia"""
    if not client:
        return generate_mock_tennis_data()
    
    try:
        # Login se necessario
        if not client.session.is_logged_in():
            cert_path = os.getenv('BETFAIR_CERT_PATH')
            key_path = os.getenv('BETFAIR_KEY_PATH')
            
            if cert_path and key_path:
                success = client.session.login_certificate(cert_path, key_path)
            else:
                success = client.session.login_interactive()
            
            if not success:
                st.error("❌ Login Betfair fallito")
                return generate_mock_tennis_data()
        
        # Recupera dati tennis
        tennis_odds = client.get_tennis_odds_realtime(
            competition_filter=TENNIS_CONFIG['competition_filters'][:5]  # Limita per performance
        )
        
        if not tennis_odds:
            st.warning("Nessun dato tennis disponibile da Betfair")
            return generate_mock_tennis_data()
        
        # Converte in formato compatibile con l'app
        matches_data = []
        for match in tennis_odds:
            if len(match['runners']) >= 2:
                player1 = match['runners'][0]
                player2 = match['runners'][1]
                
                # Estrae migliori quote back
                p1_back = player1['back_prices'][0]['price'] if player1['back_prices'] else 2.0
                p2_back = player2['back_prices'][0]['price'] if player2['back_prices'] else 2.0
                
                # Calcola probabilità implicite
                p1_prob = 1 / p1_back if p1_back > 1 else 0.5
                p2_prob = 1 / p2_back if p2_back > 1 else 0.5
                
                matches_data.append({
                    'match': match['event_name'],
                    'tournament': match['competition'],
                    'player1': player1['runner_name'],
                    'player2': player2['runner_name'],
                    'player1_odds': p1_back,
                    'player2_odds': p2_back,
                    'player1_prob': p1_prob,
                    'player2_prob': p2_prob,
                    'market_id': match['market_id'],
                    'start_time': match['market_start_time'],
                    'value_bet': abs(p1_prob - p2_prob) > 0.1  # Semplice calcolo value bet
                })
        
        return pd.DataFrame(matches_data)
        
    except Exception as e:
        st.error(f"Errore recupero dati Betfair: {e}")
        return generate_mock_tennis_data()

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

# CSS rimosso temporaneamente per risolvere problemi di rendering

# Inizializza DB - temporaneamente commentato per debug
# db = DatabaseManager()
db = None

# 🎾 Titolo principale
st.title("🎾 Tennis Value Bets Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair e detection value bets**")
st.info("🚀 App caricata correttamente!")

# 🔧 Sidebar azioni
st.sidebar.header("🔧 Azioni")

# Azioni DB temporaneamente commentate per debug
st.sidebar.info("Azioni DB temporaneamente disabilitate per debug")

# if st.sidebar.button("Popola DB giocatori 👥"):
#     db.populate_mock_data()
#     st.success("DB popolato con giocatori demo ✅")

# if st.sidebar.button("Genera partite mock 🎲"):
#     try:
#         db.populate_mock_matches()
#         st.success("Partite mock generate ✅")
#     except Exception as e:
#         st.error(f"Errore nel generare partite mock: {e}")

# Fetch dati reali (Sofascore)
if st.sidebar.button("Fetch dati reali (Sofascore) 🌍"):
    try:
        from etl_today import run_etl_today
        with st.spinner("Scaricando dati reali da Sofascore..."):
            summary = run_etl_today(verbose=False)
        st.success(f"ETL ok: eventi={summary['events']} | aggiornati={summary['updated']} | con quote={summary['with_odds']} | skip={summary['skipped']}")
    except Exception as e:
        st.error(f"Errore ETL Sofascore: {e}")

# -------------------------
# 👥 Filtri Giocatori - temporaneamente commentato per debug
# -------------------------
st.sidebar.header("Filtri giocatori")
st.sidebar.info("Sezione giocatori temporaneamente disabilitata per debug")

# players = db.get_all_players_with_stats()
players = None
if False:
    df_players = pd.DataFrame(players)
    df_players = df_players.sort_values("elo_rating", ascending=False)

    nations = sorted(df_players["country"].dropna().unique())
    selected_nations = st.sidebar.multiselect("🌍 Seleziona Paesi", nations, default=nations)

    min_elo = int(df_players["elo_rating"].min())
    max_elo = int(df_players["elo_rating"].max())
    elo_min = st.sidebar.slider("📈 Elo minimo", min_elo, max_elo, min_elo)

    min_rank = int(df_players["ranking"].min())
    max_rank = int(df_players["ranking"].max())
    rank_max = st.sidebar.slider("🏅 Ranking massimo", min_rank, max_rank, max_rank)

    df_filtered = df_players[
        (df_players["country"].isin(selected_nations)) &
        (df_players["elo_rating"] >= elo_min) &
        (df_players["ranking"] <= rank_max)
    ]

    st.subheader(f"📊 Giocatori trovati: {len(df_filtered)}")

    if not df_filtered.empty:
        st.dataframe(df_filtered[["name", "country", "elo_rating", "ranking", "wins", "losses"]].head(15))

        top10 = df_filtered.head(10)
        fig = px.bar(
            top10,
            x="name",
            y="elo_rating",
            color="country",
            title="🏆 Top 10 Giocatori per Elo Rating (filtrati)",
            text="elo_rating"
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition="outside")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # 👤 Scheda giocatore
        player_names = df_filtered["name"].tolist()
        selected_player = st.selectbox("👤 Vedi scheda giocatore", ["—"] + player_names)

        if selected_player != "—":
            player_data = df_filtered[df_filtered["name"] == selected_player].iloc[0]
            st.markdown(f"### 👤 {player_data['name']} ({player_data['country']})")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Elo Rating", f"{player_data['elo_rating']}")
                st.metric("Ranking", f"{player_data['ranking']}")
            with col2:
                st.metric("Vittorie", f"{player_data['wins']}")
                st.metric("Sconfitte", f"{player_data['losses']}")

            fig_trend = px.line(
                x=list(range(10)),
                y=np.random.randint(1600, 2000, 10),
                title=f"Andamento Elo di {player_data['name']}"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    else:
        st.warning("⚠️ Nessun giocatore trovato con i filtri attuali.")
else:
    st.info("ℹ️ Nessun giocatore presente nel database. Popola il DB dal menu a sinistra.")

st.divider()

# -------------------------
# 🎾 Partite Tennis Betfair Italia (dati reali + value bets)
# -------------------------
st.subheader("🎾 Tennis Live - Betfair Italia")

# Inizializza client Betfair - temporaneamente commentato per debug
# betfair_client = init_betfair_client()
betfair_client = None

# Pulsante refresh dati
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("🔄 Aggiorna Dati Betfair"):
        st.cache_resource.clear()
        st.rerun()

with col2:
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    if demo_mode:
        st.info("🔧 Modalità DEMO")
    else:
        st.success("🟢 Dati REALI")

# Recupera dati tennis
with st.spinner("Caricamento dati tennis da Betfair Italia..."):
    df_matches = get_tennis_data_betfair(betfair_client)

if not df_matches.empty:
    # Calcola fair odds basate su probabilità implicite Betfair
    df_matches["fair_odds_p1"] = (1 / df_matches["player1_prob"]).round(2)
    df_matches["fair_odds_p2"] = (1 / df_matches["player2_prob"]).round(2)

    # Rinomina colonne per compatibilità con il resto dell'app
    df_matches = df_matches.rename(columns={
        'player1_odds': 'odds_p1',
        'player2_odds': 'odds_p2',
        'player1': 'player1_name',
        'player2': 'player2_name',
        'tournament': 'tournament_name'
    })

    # Aggiungi colonne mancanti per compatibilità
    df_matches["surface"] = "Hard"  # Default, Betfair non fornisce superficie
    df_matches["round"] = "Unknown"
    df_matches["match_time"] = pd.to_datetime(df_matches["start_time"]).dt.strftime("%H:%M")

    # Value Bet check basato su probabilità Betfair vs quote
    df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
    df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]

    # Edge come scostamento percentuale vs fair odds
    df_matches["edge_p1"] = ((df_matches["odds_p1"] / df_matches["fair_odds_p1"] - 1)).round(3)
    df_matches["edge_p2"] = ((df_matches["odds_p2"] / df_matches["fair_odds_p2"] - 1)).round(3)

    # Aggiungi Elo fittizi per compatibilità (se disponibili dal DB)
    if players:
        elo_map = {p["name"]: p["elo_rating"] for p in players}
        df_matches["elo_p1"] = df_matches["player1_name"].map(elo_map).fillna(1800)
        df_matches["elo_p2"] = df_matches["player2_name"].map(elo_map).fillna(1800)
    else:
        df_matches["elo_p1"] = 1800
        df_matches["elo_p2"] = 1800

    # ---- Filtri partite (sidebar)
    st.sidebar.header("Filtri partite")

    tournaments = sorted(df_matches["tournament_name"].dropna().unique().tolist())
    selected_tournaments = st.sidebar.multiselect("🏟️ Tornei", tournaments, default=tournaments)

    surfaces = sorted(df_matches["surface"].dropna().unique().tolist())
    selected_surfaces = st.sidebar.multiselect("🟦 Superfici", surfaces, default=surfaces)

    only_value = st.sidebar.checkbox("🔥 Solo Value Bets", value=False)
    min_edge = st.sidebar.slider("📊 Edge minimo (%)", 0, 50, 5)  # percento
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

    # Download CSV value bets
    vb = dfm[
        (dfm["edge_p1"] >= min_edge_dec) | (dfm["edge_p2"] >= min_edge_dec)
    ][[
        "tournament_name","round","surface",
        "player1_name","odds_p1","fair_odds_p1","edge_p1",
        "player2_name","odds_p2","fair_odds_p2","edge_p2",
        "match_time"
    ]].copy()
    if not vb.empty:
        vb_sorted = vb.sort_values(by=["edge_p1","edge_p2"], ascending=False)
        csv = vb_sorted.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Scarica Value Bets (CSV)", data=csv, file_name="value_bets.csv", mime="text/csv")

    # Render card + grafico per ciascun match
    if dfm.empty:
        st.info("Nessuna partita soddisfa i filtri attuali.")
    else:
        for _, row in dfm.iterrows():
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                badge_html = '<span class="badge">VALUE</span>' if row["value_p1"] and row["edge_p1"] >= min_edge_dec else ""
                odds_p1_display = f"{row['odds_p1']:.2f}" if pd.notna(row['odds_p1']) else "N/A"
                st.markdown(f"""
                <div class="match-card">
                    <b>{row['player1_name']}</b> {badge_html}<br>
                    Elo: {int(row['elo_p1'])}<br>
                    Odds: <span style="color:{'green' if row['value_p1'] and row['edge_p1'] >= min_edge_dec else 'black'}">{odds_p1_display}</span><br>
                    Fair: {row['fair_odds_p1']}<br>
                    Edge: {(row['edge_p1']*100):.1f}%
                </div>
                """, unsafe_allow_html=True)

            with col2:
                when = ""
                try:
                    when = pd.to_datetime(row["match_time"]).strftime("%H:%M")
                except Exception:
                    when = str(row["match_time"]) if pd.notna(row["match_time"]) else "TBD"
                st.markdown(f"""
                <div style="text-align:center; font-size:22px;">
                    <b>VS</b><br>
                    <span style="font-size:14px;">{row['tournament_name']} - {row['round']} ({row['surface']})</span><br>
                    <span style="font-size:12px;">{when}</span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                badge_html2 = '<span class="badge">VALUE</span>' if row["value_p2"] and row["edge_p2"] >= min_edge_dec else ""
                odds_p2_display = f"{row['odds_p2']:.2f}" if pd.notna(row['odds_p2']) else "N/A"
                st.markdown(f"""
                <div class="match-card">
                    <b>{row['player2_name']}</b> {badge_html2}<br>
                    Elo: {int(row['elo_p2'])}<br>
                    Odds: <span style="color:{'green' if row['value_p2'] and row['edge_p2'] >= min_edge_dec else 'black'}">{odds_p2_display}</span><br>
                    Fair: {row['fair_odds_p2']}<br>
                    Edge: {(row['edge_p2']*100):.1f}%
                </div>
                """, unsafe_allow_html=True)

            # 🔹 Grafico quote vs fair (solo se abbiamo almeno una quota reale)
            if pd.notna(row['odds_p1']) or pd.notna(row['odds_p2']):
                o1 = row['odds_p1'] if pd.notna(row['odds_p1']) else 0
                o2 = row['odds_p2'] if pd.notna(row['odds_p2']) else 0
                fig_match = px.bar(
                    x=["Odds P1", "Fair P1", "Odds P2", "Fair P2"],
                    y=[o1, row['fair_odds_p1'], o2, row['fair_odds_p2']],
                    color=["Real", "Fair", "Real", "Fair"],
                    title=f"Confronto Quote - {row['player1_name']} vs {row['player2_name']}",
                    text=[o1, row['fair_odds_p1'], o2, row['fair_odds_p2']]
                )
                fig_match.update_traces(texttemplate='%{text:.2f}', textposition="outside")
                fig_match.update_layout(yaxis_title="Quota", xaxis_title="", showlegend=False, height=380)
                st.plotly_chart(fig_match, use_container_width=True)

            st.markdown("---")

else:
    st.info("Nessun dato tennis disponibile. Verifica la configurazione Betfair o attiva la modalità DEMO.")

# -------------------------
# 🎯 Sezione Betfair Italia - Informazioni e Configurazione
# -------------------------
st.divider()
st.subheader("🇮🇹 Configurazione Betfair Italia")

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

# Informazioni stato connessione
if betfair_client:
    if betfair_client.session.is_logged_in():
        st.success("✅ Connesso a Betfair Italia")
        
        # Mostra informazioni account se disponibili
        try:
            funds = betfair_client.get_account_funds()
            if funds:
                st.info(f"💰 Saldo disponibile: €{funds.get('availableToBetBalance', 'N/A')}")
        except:
            pass
    else:
        st.warning("⚠️ Non connesso a Betfair Italia")
else:
    st.info("🔧 Modalità DEMO attiva - nessuna connessione reale")

# Sezione piazzamento scommesse (solo se connesso e non in demo)
if betfair_client and betfair_client.session.is_logged_in() and not df_matches.empty:
    st.divider()
    st.subheader("🎯 Piazza Scommessa (ATTENZIONE: USA FONDI REALI!)")
    
    st.warning("⚠️ **ATTENZIONE**: Questa funzione piazza scommesse reali con fondi veri!")
    
    # Selezione partita
    match_options = [f"{row['player1_name']} vs {row['player2_name']}" for _, row in df_matches.iterrows()]
    selected_match_idx = st.selectbox("Seleziona partita", range(len(match_options)), 
                                     format_func=lambda x: match_options[x])
    
    if selected_match_idx is not None:
        selected_match = df_matches.iloc[selected_match_idx]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bet_side = st.selectbox("Scommetti su", [
                f"{selected_match['player1_name']} (€{selected_match['odds_p1']:.2f})",
                f"{selected_match['player2_name']} (€{selected_match['odds_p2']:.2f})"
            ])
        
        with col2:
            bet_amount = st.number_input("Importo (€)", min_value=2.0, max_value=1000.0, 
                                       value=10.0, step=0.5)
        
        with col3:
            if st.button("🎯 PIAZZA SCOMMESSA", type="primary"):
                try:
                    # Determina selezione
                    if selected_match['player1_name'] in bet_side:
                        selection_id = 0  # Placeholder - dovrebbe essere il vero selection_id
                        odds = selected_match['odds_p1']
                    else:
                        selection_id = 1  # Placeholder
                        odds = selected_match['odds_p2']
                    
                    # Piazza scommessa (commentato per sicurezza)
                    st.error("🚫 Funzione scommesse disabilitata per sicurezza. Implementare con cautela!")
                    
                    # result = betfair_client.place_bet(
                    #     market_id=selected_match['market_id'],
                    #     selection_id=selection_id,
                    #     side='B',  # Back bet
                    #     size=bet_amount,
                    #     price=odds
                    # )
                    # st.success(f"✅ Scommessa piazzata: {result}")
                    
                except Exception as e:
                    st.error(f"❌ Errore piazzamento scommessa: {e}")

st.divider()

# -------------------------
# ℹ️ Info progetto
# -------------------------
st.subheader("💰 Info Progetto")
st.markdown("""
🎾 **Tennis Value Bets** - Dashboard con integrazione Betfair Italia  
📊 Dati reali da betfair.it, analisi value bets e piazzamento scommesse  
🇮🇹 Configurato specificamente per il mercato italiano  
🚀 Sviluppato con Streamlit + Betfair Exchange API  
""")
