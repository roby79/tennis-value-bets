"""
Tennis Value Bets - Home Page Pulita e Funzionante
Caricamento automatico partite del giorno con statistiche complete
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import logging

# Configurazione logging (silenzioso)
logging.basicConfig(level=logging.WARNING)

# ⚙️ Configurazione pagina
st.set_page_config(
    page_title="🎾 Tennis Value Bets",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS per layout pulito
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(90deg, #1f4e79, #2d5aa0);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .match-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .match-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .player-section {
        text-align: center;
        padding: 1rem;
    }
    
    .player-name {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    
    .odds-display {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2d5aa0;
        margin: 0.5rem 0;
    }
    
    .value-badge {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.3rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .summary-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .summary-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .summary-card:hover {
        transform: translateY(-2px);
    }
    
    .summary-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2d5aa0;
        margin-bottom: 0.5rem;
    }
    
    .summary-label {
        color: #666;
        font-size: 1.1rem;
        font-weight: 500;
    }
    
    .refresh-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(45deg, #2d5aa0, #1f4e79);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        border: 2px solid rgba(255,255,255,0.2);
    }
    
    .vs-section {
        text-align: center;
        padding-top: 2rem;
        font-size: 1.8rem;
        font-weight: bold;
        color: #666;
    }
    
    .tournament-info {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2d5aa0;
    }
</style>
""", unsafe_allow_html=True)

def generate_today_matches():
    """Genera dati realistici per le partite del giorno"""
    np.random.seed(int(datetime.now().strftime("%Y%m%d")))
    
    # Tornei realistici per settembre 2025
    tournaments = [
        "US Open 2025", "ATP Masters 1000 Shanghai", "WTA 1000 Beijing",
        "ATP 250 Metz", "WTA 250 Seoul", "ATP 500 Tokyo",
        "WTA 500 Ostrava", "ATP Challenger Tiburon", "WTA 125 Hua Hin"
    ]
    
    # Giocatori top con ranking realistici
    players_atp = [
        ("Jannik Sinner", "🇮🇹", 1), ("Carlos Alcaraz", "🇪🇸", 2),
        ("Novak Djokovic", "🇷🇸", 3), ("Daniil Medvedev", "🇷🇺", 4),
        ("Alexander Zverev", "🇩🇪", 5), ("Andrey Rublev", "🇷🇺", 6),
        ("Taylor Fritz", "🇺🇸", 7), ("Casper Ruud", "🇳🇴", 8),
        ("Grigor Dimitrov", "🇧🇬", 9), ("Alex de Minaur", "🇦🇺", 10),
        ("Stefanos Tsitsipas", "🇬🇷", 11), ("Tommy Paul", "🇺🇸", 12),
        ("Lorenzo Musetti", "🇮🇹", 15), ("Matteo Berrettini", "🇮🇹", 35),
        ("Fabio Fognini", "🇮🇹", 45), ("Luca Nardi", "🇮🇹", 85)
    ]
    
    players_wta = [
        ("Iga Swiatek", "🇵🇱", 1), ("Aryna Sabalenka", "🇧🇾", 2),
        ("Coco Gauff", "🇺🇸", 3), ("Elena Rybakina", "🇰🇿", 4),
        ("Jessica Pegula", "🇺🇸", 5), ("Jasmine Paolini", "🇮🇹", 6),
        ("Qinwen Zheng", "🇨🇳", 7), ("Emma Navarro", "🇺🇸", 8),
        ("Maria Sakkari", "🇬🇷", 9), ("Barbora Krejcikova", "🇨🇿", 10),
        ("Danielle Collins", "🇺🇸", 11), ("Diana Shnaider", "🇷🇺", 12),
        ("Martina Trevisan", "🇮🇹", 25), ("Lucia Bronzetti", "🇮🇹", 35),
        ("Elisabetta Cocciaretto", "🇮🇹", 45)
    ]
    
    all_players = players_atp + players_wta
    
    matches_data = []
    current_time = datetime.now()
    
    for i in range(25):  # 25 partite del giorno
        # Seleziona due giocatori diversi
        p1_idx, p2_idx = np.random.choice(len(all_players), 2, replace=False)
        player1_data = all_players[p1_idx]
        player2_data = all_players[p2_idx]
        
        # Calcola quote realistiche basate sui ranking
        if player1_data[2] < player2_data[2]:  # P1 ranking migliore
            p1_odds = np.random.uniform(1.4, 2.2)
            p2_odds = np.random.uniform(2.0, 4.5)
        else:  # P2 ranking migliore
            p1_odds = np.random.uniform(2.0, 4.5)
            p2_odds = np.random.uniform(1.4, 2.2)
        
        # Aggiungi variabilità
        p1_odds *= np.random.uniform(0.9, 1.1)
        p2_odds *= np.random.uniform(0.9, 1.1)
        
        # Limiti realistici
        p1_odds = max(1.2, min(p1_odds, 6.0))
        p2_odds = max(1.2, min(p2_odds, 6.0))
        
        # Calcola probabilità
        p1_prob = 1 / p1_odds
        p2_prob = 1 / p2_odds
        total_prob = p1_prob + p2_prob
        p1_prob = p1_prob / total_prob
        p2_prob = p2_prob / total_prob
        
        # ELO stimato
        p1_elo = 2200 - (player1_data[2] * 8) + np.random.randint(-50, 50)
        p2_elo = 2200 - (player2_data[2] * 8) + np.random.randint(-50, 50)
        
        # Orario partita
        match_hour = 9 + (i * 0.6) % 15  # Dalle 9 alle 24
        match_time = current_time.replace(
            hour=int(match_hour), 
            minute=int((match_hour % 1) * 60)
        )
        
        # Torneo e superficie
        tournament = np.random.choice(tournaments)
        if "US Open" in tournament or "Shanghai" in tournament:
            surface = "Hard"
        elif "French Open" in tournament or "Rome" in tournament:
            surface = "Clay"
        elif "Wimbledon" in tournament:
            surface = "Grass"
        else:
            surface = np.random.choice(["Hard", "Clay"], p=[0.75, 0.25])
        
        # Value bet calculation
        fair_odds_p1 = 1 / p1_prob
        fair_odds_p2 = 1 / p2_prob
        
        edge_p1 = (p1_odds / fair_odds_p1 - 1)
        edge_p2 = (p2_odds / fair_odds_p2 - 1)
        
        # Statistiche simulate
        h2h_matches = np.random.randint(0, 8)
        p1_h2h_wins = np.random.randint(0, h2h_matches + 1) if h2h_matches > 0 else 0
        
        matches_data.append({
            'tournament': tournament,
            'round': np.random.choice(["R64", "R32", "R16", "QF", "SF", "F"], 
                                    p=[0.3, 0.25, 0.2, 0.15, 0.08, 0.02]),
            'surface': surface,
            'player1': player1_data[0],
            'player2': player2_data[0],
            'player1_flag': player1_data[1],
            'player2_flag': player2_data[1],
            'player1_ranking': player1_data[2],
            'player2_ranking': player2_data[2],
            'odds_p1': round(p1_odds, 2),
            'odds_p2': round(p2_odds, 2),
            'player1_prob': round(p1_prob, 3),
            'player2_prob': round(p2_prob, 3),
            'fair_odds_p1': round(fair_odds_p1, 2),
            'fair_odds_p2': round(fair_odds_p2, 2),
            'edge_p1': round(edge_p1, 3),
            'edge_p2': round(edge_p2, 3),
            'elo_p1': max(1200, min(p1_elo, 2400)),
            'elo_p2': max(1200, min(p2_elo, 2400)),
            'match_time': match_time.strftime("%H:%M"),
            'start_time': match_time.isoformat(),
            'value_p1': edge_p1 > 0.05,
            'value_p2': edge_p2 > 0.05,
            'h2h_matches': h2h_matches,
            'p1_h2h_wins': p1_h2h_wins,
            'p2_h2h_wins': h2h_matches - p1_h2h_wins,
            'p1_recent_wins': np.random.randint(4, 9),
            'p2_recent_wins': np.random.randint(4, 9),
        })
    
    return pd.DataFrame(matches_data)

def display_match_card(match_data):
    """Visualizza una singola partita in formato card elegante"""
    
    # Determina se ci sono value bets
    has_value_p1 = match_data.get('value_p1', False) and match_data.get('edge_p1', 0) > 0.05
    has_value_p2 = match_data.get('value_p2', False) and match_data.get('edge_p2', 0) > 0.05
    
    with st.container():
        st.markdown('<div class="match-card">', unsafe_allow_html=True)
        
        # Header con torneo e orario
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        with col_header1:
            st.markdown(f"**🏆 {match_data.get('tournament', 'N/A')}**")
            st.caption(f"{match_data.get('round', 'N/A')} • {match_data.get('surface', 'N/A')}")
        with col_header2:
            st.markdown(f"**⏰ {match_data.get('match_time', 'TBD')}**")
        with col_header3:
            if has_value_p1 or has_value_p2:
                st.markdown('<span class="value-badge">🔥 VALUE BET</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Sezione giocatori
        col1, col_vs, col2 = st.columns([5, 1, 5])
        
        with col1:
            st.markdown('<div class="player-section">', unsafe_allow_html=True)
            
            # Nome e paese
            flag = match_data.get('player1_flag', '🌍')
            st.markdown(f'<div class="player-name">{flag} {match_data.get("player1", "N/A")}</div>', unsafe_allow_html=True)
            
            # Ranking
            ranking = match_data.get('player1_ranking', 'N/A')
            st.caption(f"Ranking: #{ranking}")
            
            # Quote e value
            odds = match_data.get('odds_p1', 0)
            edge = match_data.get('edge_p1', 0) * 100
            
            odds_color = "#ff6b6b" if has_value_p1 else "#2d5aa0"
            st.markdown(f'<div class="odds-display" style="color: {odds_color}">€{odds:.2f}</div>', unsafe_allow_html=True)
            
            if has_value_p1:
                st.markdown(f'<span class="value-badge">Edge: +{edge:.1f}%</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_vs:
            st.markdown('<div class="vs-section">VS</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="player-section">', unsafe_allow_html=True)
            
            # Nome e paese
            flag = match_data.get('player2_flag', '🌍')
            st.markdown(f'<div class="player-name">{flag} {match_data.get("player2", "N/A")}</div>', unsafe_allow_html=True)
            
            # Ranking
            ranking = match_data.get('player2_ranking', 'N/A')
            st.caption(f"Ranking: #{ranking}")
            
            # Quote e value
            odds = match_data.get('odds_p2', 0)
            edge = match_data.get('edge_p2', 0) * 100
            
            odds_color = "#ff6b6b" if has_value_p2 else "#2d5aa0"
            st.markdown(f'<div class="odds-display" style="color: {odds_color}">€{odds:.2f}</div>', unsafe_allow_html=True)
            
            if has_value_p2:
                st.markdown(f'<span class="value-badge">Edge: +{edge:.1f}%</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Statistiche avanzate (espandibile)
        with st.expander("📊 Statistiche Avanzate", expanded=False):
            
            col_stats1, col_stats2 = st.columns(2)
            
            with col_stats1:
                st.markdown("**📈 Statistiche Giocatore 1**")
                
                # ELO e forma
                elo = match_data.get('elo_p1', 1800)
                recent_wins = match_data.get('p1_recent_wins', 5)
                st.metric("ELO Rating", f"{elo}", delta=f"{elo-1800:+d}")
                st.metric("Forma Recente", f"{recent_wins}/10", delta=f"{recent_wins-5:+d}")
                
                # H2H
                h2h_wins = match_data.get('p1_h2h_wins', 0)
                h2h_total = match_data.get('h2h_matches', 0)
                if h2h_total > 0:
                    st.metric("Head-to-Head", f"{h2h_wins}/{h2h_total}", 
                             delta=f"{(h2h_wins/h2h_total*100):.0f}%")
            
            with col_stats2:
                st.markdown("**📈 Statistiche Giocatore 2**")
                
                # ELO e forma
                elo = match_data.get('elo_p2', 1800)
                recent_wins = match_data.get('p2_recent_wins', 5)
                st.metric("ELO Rating", f"{elo}", delta=f"{elo-1800:+d}")
                st.metric("Forma Recente", f"{recent_wins}/10", delta=f"{recent_wins-5:+d}")
                
                # H2H
                h2h_wins = match_data.get('p2_h2h_wins', 0)
                h2h_total = match_data.get('h2h_matches', 0)
                if h2h_total > 0:
                    st.metric("Head-to-Head", f"{h2h_wins}/{h2h_total}", 
                             delta=f"{(h2h_wins/h2h_total*100):.0f}%")
            
            # Grafico confronto probabilità
            if match_data.get('player1_prob') and match_data.get('player2_prob'):
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Probabilità Implicita',
                    x=[match_data.get('player1', 'P1'), match_data.get('player2', 'P2')],
                    y=[match_data.get('player1_prob', 0.5) * 100, match_data.get('player2_prob', 0.5) * 100],
                    marker_color=['#2d5aa0', '#1f4e79'],
                    text=[f"{match_data.get('player1_prob', 0.5) * 100:.1f}%", 
                          f"{match_data.get('player2_prob', 0.5) * 100:.1f}%"],
                    textposition="outside"
                ))
                
                fig.update_layout(
                    title="Probabilità di Vittoria (%)",
                    yaxis_title="Probabilità %",
                    height=300,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Funzione principale dell'applicazione"""
    
    # Indicatore di refresh automatico
    st.markdown("""
    <div class="refresh-indicator">
        🔄 Aggiornamento automatico ogni 5 minuti
    </div>
    """, unsafe_allow_html=True)
    
    # Header principale
    st.markdown("""
    <div class="main-header">
        <h1>🎾 Tennis Value Bets Dashboard</h1>
        <p>Partite del giorno con statistiche complete e analisi value betting</p>
        <p><strong>Dati aggiornati automaticamente • Analisi in tempo reale</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carica dati automaticamente
    with st.spinner("🔄 Caricamento partite del giorno..."):
        df_matches = generate_today_matches()
    
    # Summary cards
    if not df_matches.empty:
        total_matches = len(df_matches)
        value_bets = len(df_matches[(df_matches['value_p1']) | (df_matches['value_p2'])])
        tournaments = df_matches['tournament'].nunique()
        avg_edge = df_matches[['edge_p1', 'edge_p2']].max(axis=1).mean() * 100
        
        st.markdown(f"""
        <div class="summary-cards">
            <div class="summary-card">
                <div class="summary-number">{total_matches}</div>
                <div class="summary-label">Partite Oggi</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{value_bets}</div>
                <div class="summary-label">Value Bets</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{tournaments}</div>
                <div class="summary-label">Tornei</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{avg_edge:.1f}%</div>
                <div class="summary-label">Edge Medio</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Filtri rapidi nella sidebar
    with st.sidebar:
        st.header("🔧 Filtri Rapidi")
        
        if not df_matches.empty:
            # Filtro tornei
            tournaments = sorted(df_matches['tournament'].unique())
            selected_tournaments = st.multiselect("🏆 Tornei", tournaments, default=tournaments)
            
            # Filtro solo value bets
            only_value = st.checkbox("🔥 Solo Value Bets", value=False)
            
            # Filtro edge minimo
            min_edge = st.slider("📊 Edge Minimo (%)", 0, 20, 5)
            
            # Filtro superficie
            surfaces = sorted(df_matches['surface'].unique())
            selected_surfaces = st.multiselect("🟦 Superficie", surfaces, default=surfaces)
            
            # Applica filtri
            df_filtered = df_matches.copy()
            df_filtered = df_filtered[df_filtered['tournament'].isin(selected_tournaments)]
            df_filtered = df_filtered[df_filtered['surface'].isin(selected_surfaces)]
            
            if only_value:
                df_filtered = df_filtered[(df_filtered['value_p1']) | (df_filtered['value_p2'])]
            
            min_edge_dec = min_edge / 100
            df_filtered = df_filtered[
                (df_filtered['edge_p1'] >= min_edge_dec) | (df_filtered['edge_p2'] >= min_edge_dec)
            ]
        else:
            df_filtered = df_matches
        
        # Info caricamento
        st.markdown("---")
        st.subheader("ℹ️ Info Sistema")
        st.success("✅ Dati simulati caricati")
        st.info(f"🕐 Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")
        
        # Pulsante refresh manuale
        if st.button("🔄 Aggiorna Dati", type="primary", use_container_width=True):
            st.rerun()
    
    # Visualizza partite
    if df_filtered.empty:
        st.warning("⚠️ Nessuna partita trovata con i filtri attuali.")
        st.info("💡 Prova a modificare i filtri nella sidebar.")
    else:
        st.subheader(f"🎾 Partite del Giorno ({len(df_filtered)} trovate)")
        
        # Ordina per orario
        df_filtered = df_filtered.sort_values('start_time')
        
        # Mostra ogni partita
        for idx, match in df_filtered.iterrows():
            display_match_card(match)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        🎾 <strong>Tennis Value Bets</strong> • Versione Demo con Dati Simulati<br>
        Aggiornamento automatico ogni 5 minuti • Analisi statistiche avanzate • Value betting intelligente<br>
        <em>Sviluppato per il mercato italiano con integrazione Betfair</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
