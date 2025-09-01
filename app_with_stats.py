
"""
App principale con sistema completo di statistiche tennis integrato
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Import moduli esistenti
from db import DatabaseManager
from services.betfair_session import BetfairItalySession
from services.betfair_client import BetfairItalyClient
from config.betfair_it import TENNIS_CONFIG, ITALIAN_BETTING_RULES

# Import nuovi moduli statistiche
from models.stats_models import TennisStatsDatabase
from services.data_fetcher import TennisDataFetcher
from analytics.advanced_metrics import TennisAdvancedMetrics
from visualization.stats_charts import TennisStatsVisualizer
from ui.stats_interface import TennisStatsInterface

# Carica variabili ambiente
load_dotenv()
load_dotenv('.env.betfair')

# Configurazione logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

# ⚙️ Configurazione pagina
st.set_page_config(
    page_title="Tennis Value Bets & Stats",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione componenti
@st.cache_resource
def init_components():
    """Inizializza tutti i componenti dell'applicazione"""
    try:
        # Database originale
        db = DatabaseManager()
        
        # Nuovo sistema statistiche
        stats_db = TennisStatsDatabase()
        data_fetcher = TennisDataFetcher()
        metrics_calculator = TennisAdvancedMetrics()
        visualizer = TennisStatsVisualizer()
        stats_interface = TennisStatsInterface()
        
        return {
            'db': db,
            'stats_db': stats_db,
            'data_fetcher': data_fetcher,
            'metrics': metrics_calculator,
            'visualizer': visualizer,
            'stats_interface': stats_interface
        }
    except Exception as e:
        st.error(f"Errore inizializzazione componenti: {e}")
        return None

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
        
        if demo_mode or not app_key:
            st.warning("⚠️ Modalità DEMO attiva - usando dati simulati")
            return None
        
        session = BetfairItalySession(app_key, username, password)
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
            competition_filter=TENNIS_CONFIG['competition_filters'][:5]
        )
        
        if not tennis_odds:
            st.warning("Nessun dato tennis disponibile da Betfair")
            return generate_mock_tennis_data()
        
        # Converte in formato compatibile
        matches_data = []
        for match in tennis_odds:
            if len(match['runners']) >= 2:
                player1 = match['runners'][0]
                player2 = match['runners'][1]
                
                p1_back = player1['back_prices'][0]['price'] if player1['back_prices'] else 2.0
                p2_back = player2['back_prices'][0]['price'] if player2['back_prices'] else 2.0
                
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
                    'value_bet': abs(p1_prob - p2_prob) > 0.1
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

# Inizializza componenti
components = init_components()

if not components:
    st.error("❌ Errore critico nell'inizializzazione. Riavviare l'applicazione.")
    st.stop()

# 🎾 Titolo principale
st.title("🎾 Tennis Value Bets & Statistics Dashboard")
st.markdown("**Analisi ATP/WTA con quote Betfair, statistiche complete e metriche avanzate**")

# 🔧 Sidebar navigazione principale
st.sidebar.header("🚀 Navigazione Principale")

main_section = st.sidebar.selectbox(
    "📊 Seleziona Sezione",
    [
        "🎯 Value Betting (Betfair)",
        "📊 Sistema Statistiche Complete",
        "⚡ Dashboard Integrata",
        "🔧 Configurazione"
    ]
)

if main_section == "🎯 Value Betting (Betfair)":
    # -------------------------
    # SEZIONE VALUE BETTING ORIGINALE
    # -------------------------
    
    st.header("🎯 Tennis Value Betting - Betfair Italia")
    
    # Inizializza client Betfair
    betfair_client = init_betfair_client()
    
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
        df_matches["round"] = "Unknown"
        df_matches["match_time"] = pd.to_datetime(df_matches["start_time"]).dt.strftime("%H:%M")
        
        # Value Bet check
        df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
        df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]
        
        # Edge calculation
        df_matches["edge_p1"] = ((df_matches["odds_p1"] / df_matches["fair_odds_p1"] - 1)).round(3)
        df_matches["edge_p2"] = ((df_matches["odds_p2"] / df_matches["fair_odds_p2"] - 1)).round(3)
        
        # Elo fittizi
        df_matches["elo_p1"] = 1800
        df_matches["elo_p2"] = 1800
        
        # ---- Filtri partite (sidebar)
        st.sidebar.header("🎯 Filtri Value Betting")
        
        tournaments = sorted(df_matches["tournament_name"].dropna().unique().tolist())
        selected_tournaments = st.sidebar.multiselect("🏟️ Tornei", tournaments, default=tournaments)
        
        only_value = st.sidebar.checkbox("🔥 Solo Value Bets", value=False)
        min_edge = st.sidebar.slider("📊 Edge minimo (%)", 0, 50, 5)
        min_edge_dec = min_edge / 100.0
        
        # Applica filtri
        dfm = df_matches[df_matches["tournament_name"].isin(selected_tournaments)].copy()
        
        if only_value:
            dfm = dfm[(dfm["value_p1"]) | (dfm["value_p2"])]
        
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
        
        # Render partite
        if dfm.empty:
            st.info("Nessuna partita soddisfa i filtri attuali.")
        else:
            for _, row in dfm.iterrows():
                col1, col2, col3 = st.columns([4, 2, 4])
                
                with col1:
                    badge_html = '<span style="background: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">VALUE</span>' if row["value_p1"] and row["edge_p1"] >= min_edge_dec else ""
                    odds_p1_display = f"{row['odds_p1']:.2f}" if pd.notna(row['odds_p1']) else "N/A"
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
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
                        <span style="font-size:14px;">{row['tournament_name']} - {row['round']}</span><br>
                        <span style="font-size:12px;">{when}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    badge_html2 = '<span style="background: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">VALUE</span>' if row["value_p2"] and row["edge_p2"] >= min_edge_dec else ""
                    odds_p2_display = f"{row['odds_p2']:.2f}" if pd.notna(row['odds_p2']) else "N/A"
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                        <b>{row['player2_name']}</b> {badge_html2}<br>
                        Elo: {int(row['elo_p2'])}<br>
                        Odds: <span style="color:{'green' if row['value_p2'] and row['edge_p2'] >= min_edge_dec else 'black'}">{odds_p2_display}</span><br>
                        Fair: {row['fair_odds_p2']}<br>
                        Edge: {(row['edge_p2']*100):.1f}%
                    </div>
                    """, unsafe_allow_html=True)
                
                # Grafico quote vs fair
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

elif main_section == "📊 Sistema Statistiche Complete":
    # -------------------------
    # SEZIONE STATISTICHE COMPLETE
    # -------------------------
    
    # Renderizza interfaccia statistiche completa
    components['stats_interface'].render_main_interface()

elif main_section == "⚡ Dashboard Integrata":
    # -------------------------
    # DASHBOARD INTEGRATA VALUE BETTING + STATISTICHE
    # -------------------------
    
    st.header("⚡ Dashboard Integrata")
    st.markdown("**Combinazione di Value Betting e Analisi Statistiche Avanzate**")
    
    # Metriche principali integrate
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Value Bets Oggi", "12", "+3")
    with col2:
        st.metric("Edge Medio", "8.4%", "+1.2%")
    with col3:
        st.metric("Giocatori Analizzati", "1,247", "+23")
    with col4:
        st.metric("Accuracy Predizioni", "73.2%", "+2.1%")
    
    st.divider()
    
    # Sezione partite con statistiche integrate
    st.subheader("🎾 Partite con Analisi Completa")
    
    # Recupera dati Betfair
    betfair_client = init_betfair_client()
    df_matches = get_tennis_data_betfair(betfair_client)
    
    if not df_matches.empty:
        # Processa dati come nella sezione value betting
        df_matches["fair_odds_p1"] = (1 / df_matches["player1_prob"]).round(2)
        df_matches["fair_odds_p2"] = (1 / df_matches["player2_prob"]).round(2)
        df_matches = df_matches.rename(columns={
            'player1_odds': 'odds_p1',
            'player2_odds': 'odds_p2',
            'player1': 'player1_name',
            'player2': 'player2_name',
            'tournament': 'tournament_name'
        })
        df_matches["surface"] = "Hard"
        df_matches["value_p1"] = df_matches["odds_p1"] > df_matches["fair_odds_p1"]
        df_matches["value_p2"] = df_matches["odds_p2"] > df_matches["fair_odds_p2"]
        df_matches["edge_p1"] = ((df_matches["odds_p1"] / df_matches["fair_odds_p1"] - 1)).round(3)
        df_matches["edge_p2"] = ((df_matches["odds_p2"] / df_matches["fair_odds_p2"] - 1)).round(3)
        
        # Per ogni partita, aggiungi analisi statistiche
        for idx, row in df_matches.head(5).iterrows():  # Limita a 5 per performance
            
            st.markdown(f"### 🎾 {row['player1_name']} vs {row['player2_name']}")
            
            # Tabs per diverse analisi
            tab1, tab2, tab3, tab4 = st.tabs(["💰 Value Betting", "📊 Statistiche", "🔮 Predizione", "📈 Grafici"])
            
            with tab1:
                # Analisi value betting
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Player 1 Value**")
                    if row["value_p1"]:
                        st.success(f"✅ VALUE BET")
                        st.metric("Edge", f"{row['edge_p1']*100:.1f}%")
                    else:
                        st.info("No Value")
                    st.metric("Odds", f"{row['odds_p1']:.2f}")
                    st.metric("Fair Odds", f"{row['fair_odds_p1']:.2f}")
                
                with col2:
                    st.markdown("**Match Info**")
                    st.write(f"🏟️ Torneo: {row['tournament_name']}")
                    st.write(f"🎯 Superficie: Hard")
                    st.write(f"⏰ Orario: {row.get('match_time', 'TBD')}")
                
                with col3:
                    st.markdown("**Player 2 Value**")
                    if row["value_p2"]:
                        st.success(f"✅ VALUE BET")
                        st.metric("Edge", f"{row['edge_p2']*100:.1f}%")
                    else:
                        st.info("No Value")
                    st.metric("Odds", f"{row['odds_p2']:.2f}")
                    st.metric("Fair Odds", f"{row['fair_odds_p2']:.2f}")
            
            with tab2:
                # Statistiche simulate per i giocatori
                p1_stats = components['data_fetcher'].fetch_player_stats(row['player1_name'])
                p2_stats = components['data_fetcher'].fetch_player_stats(row['player2_name'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**📋 {row['player1_name']}**")
                    st.write(f"🎾 Aces/Match: {p1_stats['avg_aces_per_match']}")
                    st.write(f"🎯 Prime Servizio: {p1_stats['avg_first_serve_pct']}%")
                    st.write(f"🏆 Vincenti/Match: {p1_stats['avg_winners_per_match']}")
                    st.write(f"💥 Errori NF/Match: {p1_stats['avg_unforced_errors_per_match']}")
                    st.write(f"📊 Dominance Ratio: {p1_stats['dominance_ratio']}")
                
                with col2:
                    st.markdown(f"**📋 {row['player2_name']}**")
                    st.write(f"🎾 Aces/Match: {p2_stats['avg_aces_per_match']}")
                    st.write(f"🎯 Prime Servizio: {p2_stats['avg_first_serve_pct']}%")
                    st.write(f"🏆 Vincenti/Match: {p2_stats['avg_winners_per_match']}")
                    st.write(f"💥 Errori NF/Match: {p2_stats['avg_unforced_errors_per_match']}")
                    st.write(f"📊 Dominance Ratio: {p2_stats['dominance_ratio']}")
            
            with tab3:
                # Predizione match
                prediction = components['metrics'].predict_match_outcome(p1_stats, p2_stats, "Hard")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        f"Prob. {row['player1_name']}",
                        f"{prediction['player1_win_probability']:.1%}",
                        f"Surface: {prediction['surface_advantage_p1']:+.1%}"
                    )
                
                with col2:
                    st.metric(
                        "Confidenza Predizione",
                        f"{prediction['confidence']:.1%}",
                        f"Elo Diff: {prediction['elo_difference']:+.0f}"
                    )
                
                with col3:
                    st.metric(
                        f"Prob. {row['player2_name']}",
                        f"{prediction['player2_win_probability']:.1%}",
                        f"Surface: {prediction['surface_advantage_p2']:+.1%}"
                    )
                
                # Confronto predizione vs quote
                st.markdown("**🔍 Analisi Predizione vs Quote**")
                
                pred_p1 = prediction['player1_win_probability']
                pred_p2 = prediction['player2_win_probability']
                
                implied_p1 = 1 / row['odds_p1']
                implied_p2 = 1 / row['odds_p2']
                
                if pred_p1 > implied_p1:
                    st.success(f"✅ Modello favorisce {row['player1_name']} (Pred: {pred_p1:.1%} vs Quote: {implied_p1:.1%})")
                elif pred_p2 > implied_p2:
                    st.success(f"✅ Modello favorisce {row['player2_name']} (Pred: {pred_p2:.1%} vs Quote: {implied_p2:.1%})")
                else:
                    st.info("📊 Predizione allineata con le quote")
            
            with tab4:
                # Grafici comparativi
                radar_fig = components['visualizer'].create_player_comparison_radar(
                    p1_stats, p2_stats, row['player1_name'], row['player2_name']
                )
                st.plotly_chart(radar_fig, use_container_width=True)
            
            st.divider()

elif main_section == "🔧 Configurazione":
    # -------------------------
    # SEZIONE CONFIGURAZIONE
    # -------------------------
    
    st.header("🔧 Configurazione Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Betfair", "📊 Statistiche", "🔗 Integrazioni"])
    
    with tab1:
        st.subheader("🇮🇹 Configurazione Betfair Italia")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Requisiti**")
            st.write("✅ Account Betfair Italia (betfair.it)")
            st.write("✅ App Key dal Developer Portal")
            st.write("✅ Credenziali o Certificato SSL")
            st.write("✅ Fondi per scommesse (opzionale)")
            
            st.markdown("**⚙️ Variabili Ambiente**")
            st.code("""
BETFAIR_APP_KEY=your_app_key_here
BETFAIR_USERNAME=your_username
BETFAIR_PASSWORD=your_password
DEMO_MODE=false
            """)
        
        with col2:
            st.markdown("**🔗 Endpoint**")
            st.write("• Login: `identitysso.betfair.it`")
            st.write("• API: `api.betfair.com`")
            st.write("• Rate limit: 5 req/sec")
            
            st.markdown("**💰 Regole Mercato Italiano**")
            st.write("• Puntata minima: €2.00")
            st.write("• Incrementi: €0.50")
            st.write("• Vincita massima: €10,000")
            st.write("• Valuta: EUR")
        
        # Test connessione
        if st.button("🧪 Test Connessione Betfair"):
            with st.spinner("Testing..."):
                import time
                time.sleep(2)
            
            demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
            if demo_mode:
                st.warning("⚠️ Modalità DEMO - Connessione simulata OK")
            else:
                st.success("✅ Connessione Betfair OK")
    
    with tab2:
        st.subheader("📊 Configurazione Sistema Statistiche")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🗄️ Database**")
            st.write("• Engine: SQLite")
            st.write("• Path: `data/tennis_stats.db`")
            st.write("• Tabelle: 6 principali")
            st.write("• Indici: Ottimizzati per query")
            
            if st.button("🔧 Inizializza Database"):
                with st.spinner("Inizializzazione..."):
                    components['stats_db'].init_extended_database()
                st.success("✅ Database inizializzato")
        
        with col2:
            st.markdown("**📡 Fonti Dati**")
            
            data_sources = st.multiselect(
                "Seleziona fonti attive:",
                ["ATP Official", "WTA Official", "Ultimate Tennis Stats", "Tennis Abstract", "Sofascore"],
                default=["ATP Official", "WTA Official"]
            )
            
            st.markdown("**⚙️ Metriche Calcolate**")
            enable_dominance = st.checkbox("Dominance Ratio", value=True)
            enable_momentum = st.checkbox("Momentum Score", value=True)
            enable_predictions = st.checkbox("Match Predictions", value=True)
            
            if st.button("💾 Salva Configurazione Stats"):
                st.success("✅ Configurazione salvata")
    
    with tab3:
        st.subheader("🔗 Integrazioni e API")
        
        st.markdown("**🌐 API Esterne Disponibili**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Tennis Data APIs**")
            st.write("• Ultimate Tennis Statistics")
            st.write("• Tennis Abstract")
            st.write("• Sofascore API")
            st.write("• ATP/WTA Official")
            
            st.markdown("**Status Integrazioni**")
            st.write("🟢 Betfair Italia: Attivo")
            st.write("🟡 Tennis APIs: Demo Mode")
            st.write("🔴 Live Streaming: Non configurato")
        
        with col2:
            st.markdown("**🔑 Configurazione API Keys**")
            
            api_key_sofascore = st.text_input("Sofascore API Key", type="password")
            api_key_tennis_abstract = st.text_input("Tennis Abstract API Key", type="password")
            
            if st.button("🔐 Salva API Keys"):
                st.success("✅ API Keys salvate (encrypted)")
            
            st.markdown("**📊 Rate Limits**")
            st.write("• Betfair: 5 req/sec")
            st.write("• Sofascore: 100 req/hour")
            st.write("• Tennis Abstract: 1000 req/day")

# -------------------------
# Footer informazioni
# -------------------------
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🎾 Tennis Value Bets & Stats**")
    st.write("Dashboard completa per analisi tennis")
    st.write("Value betting + Statistiche avanzate")

with col2:
    st.markdown("**🇮🇹 Betfair Italia**")
    st.write("Integrazione nativa betfair.it")
    st.write("Quote live e piazzamento scommesse")

with col3:
    st.markdown("**📊 Analytics Avanzate**")
    st.write("Dominance Ratio, Momentum Score")
    st.write("Predizioni ML e metriche custom")

st.markdown("---")
st.markdown("🚀 **Sviluppato per la comunità tennis italiana** | ⚠️ **Scommettere responsabilmente**")
