"""
Tennis Value Bets - Home Page Pulita
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
from dotenv import load_dotenv
import asyncio
import time

# Import moduli esistenti
from db import DatabaseManager
from etl_today import run_etl_today
from services.betfair_session import BetfairItalySession
from services.betfair_client import BetfairItalyClient

# Import componenti custom
from components.auto_refresh import auto_refresh_component, show_refresh_status, update_timestamp
from utils.data_loader import TennisDataLoader

# Carica variabili ambiente
load_dotenv()
load_dotenv('.env.betfair')

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
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79, #2d5aa0);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .match-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .match-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .player-section {
        text-align: center;
        padding: 1rem;
    }
    
    .player-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    
    .odds-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2d5aa0;
        margin: 0.5rem 0;
    }
    
    .value-badge {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .tournament-info {
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
        padding: 0.8rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
    }
    
    .stat-value {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f4e79;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.2rem;
    }
    
    .refresh-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #2d5aa0;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        z-index: 1000;
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #2d5aa0;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .summary-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .summary-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .summary-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2d5aa0;
    }
    
    .summary-label {
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione componenti cached
@st.cache_resource
def init_data_loader():
    """Inizializza data loader ottimizzato"""
    return TennisDataLoader()

@st.cache_data(ttl=300)  # Cache per 5 minuti
def load_today_matches(force_refresh: bool = False):
    """Carica automaticamente le partite del giorno"""
    data_loader = init_data_loader()
    return data_loader.load_matches_today(force_refresh=force_refresh)



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
            flag = f"🇮🇹" if match_data.get('player1_country') == 'ITA' else "🌍"
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
            st.markdown("""
            <div style="text-align: center; padding-top: 2rem;">
                <div style="font-size: 1.5rem; font-weight: bold; color: #666;">VS</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="player-section">', unsafe_allow_html=True)
            
            # Nome e paese
            flag = f"🇮🇹" if match_data.get('player2_country') == 'ITA' else "🌍"
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
                
                # Superficie
                surf_wins = match_data.get('p1_surface_wins', 10)
                surf_losses = match_data.get('p1_surface_losses', 5)
                surf_pct = surf_wins / (surf_wins + surf_losses) * 100 if (surf_wins + surf_losses) > 0 else 50
                st.metric(f"Su {match_data.get('surface', 'Hard')}", f"{surf_pct:.0f}%", 
                         delta=f"{surf_pct-50:.0f}%")
            
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
                
                # Superficie
                surf_wins = match_data.get('p2_surface_wins', 10)
                surf_losses = match_data.get('p2_surface_losses', 5)
                surf_pct = surf_wins / (surf_wins + surf_losses) * 100 if (surf_wins + surf_losses) > 0 else 50
                st.metric(f"Su {match_data.get('surface', 'Hard')}", f"{surf_pct:.0f}%", 
                         delta=f"{surf_pct-50:.0f}%")
            
            # Grafico confronto probabilità
            if match_data.get('player1_prob') and match_data.get('player2_prob'):
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Probabilità Implicita',
                    x=[match_data.get('player1', 'P1'), match_data.get('player2', 'P2')],
                    y=[match_data.get('player1_prob', 0.5) * 100, match_data.get('player2_prob', 0.5) * 100],
                    marker_color=['#2d5aa0', '#1f4e79']
                ))
                
                fig.update_layout(
                    title="Probabilità di Vittoria (%)",
                    yaxis_title="Probabilità %",
                    height=300,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Funzione principale dell'applicazione"""
    
    # Componente auto-refresh
    auto_refresh_component(refresh_interval_minutes=5)
    
    # Header principale
    st.markdown("""
    <div class="main-header">
        <h1>🎾 Tennis Value Bets Dashboard</h1>
        <p>Partite del giorno con statistiche complete e analisi value betting</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carica dati automaticamente
    with st.spinner("🔄 Caricamento partite del giorno..."):
        df_matches, summary = load_today_matches()
    
    # Summary cards
    if not df_matches.empty:
        total_matches = len(df_matches)
        value_bets = len(df_matches[(df_matches.get('value_p1', False)) | (df_matches.get('value_p2', False))])
        tournaments = df_matches['tournament'].nunique() if 'tournament' in df_matches.columns else 0
        avg_edge = df_matches[['edge_p1', 'edge_p2']].max(axis=1).mean() * 100 if 'edge_p1' in df_matches.columns else 0
        
        st.markdown("""
        <div class="summary-cards">
            <div class="summary-card">
                <div class="summary-number">{}</div>
                <div class="summary-label">Partite Oggi</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{}</div>
                <div class="summary-label">Value Bets</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{}</div>
                <div class="summary-label">Tornei</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{:.1f}%</div>
                <div class="summary-label">Edge Medio</div>
            </div>
        </div>
        """.format(total_matches, value_bets, tournaments, avg_edge), unsafe_allow_html=True)
    
    # Filtri rapidi nella sidebar
    with st.sidebar:
        st.header("🔧 Filtri Rapidi")
        
        if not df_matches.empty:
            # Filtro tornei
            tournaments = sorted(df_matches['tournament'].unique()) if 'tournament' in df_matches.columns else []
            selected_tournaments = st.multiselect("🏆 Tornei", tournaments, default=tournaments)
            
            # Filtro solo value bets
            only_value = st.checkbox("🔥 Solo Value Bets", value=False)
            
            # Filtro edge minimo
            min_edge = st.slider("📊 Edge Minimo (%)", 0, 20, 5)
            
            # Filtro superficie
            surfaces = sorted(df_matches['surface'].unique()) if 'surface' in df_matches.columns else []
            selected_surfaces = st.multiselect("🟦 Superficie", surfaces, default=surfaces)
            
            # Applica filtri
            df_filtered = df_matches.copy()
            
            if 'tournament' in df_matches.columns:
                df_filtered = df_filtered[df_filtered['tournament'].isin(selected_tournaments)]
            
            if 'surface' in df_matches.columns:
                df_filtered = df_filtered[df_filtered['surface'].isin(selected_surfaces)]
            
            if only_value:
                df_filtered = df_filtered[
                    (df_filtered.get('value_p1', False)) | (df_filtered.get('value_p2', False))
                ]
            
            if 'edge_p1' in df_matches.columns and 'edge_p2' in df_matches.columns:
                min_edge_dec = min_edge / 100
                df_filtered = df_filtered[
                    (df_filtered['edge_p1'] >= min_edge_dec) | (df_filtered['edge_p2'] >= min_edge_dec)
                ]
        else:
            df_filtered = df_matches
        
        # Info caricamento
        st.markdown("---")
        st.subheader("ℹ️ Info Caricamento")
        
        if summary.get('mock'):
            st.info("🎲 Dati simulati")
        else:
            st.success(f"✅ {summary.get('events', 0)} eventi caricati")
        
        # Componente status refresh
        show_refresh_status()
    
    # Visualizza partite
    if df_filtered.empty:
        st.warning("⚠️ Nessuna partita trovata con i filtri attuali.")
        st.info("💡 Prova a modificare i filtri nella sidebar o attendi il prossimo aggiornamento automatico.")
    else:
        st.subheader(f"🎾 Partite del Giorno ({len(df_filtered)} trovate)")
        
        # Ordina per orario e value bets
        if 'start_time' in df_filtered.columns:
            df_filtered = df_filtered.sort_values('start_time')
        
        # Mostra ogni partita
        for idx, match in df_filtered.iterrows():
            display_match_card(match)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        🎾 <strong>Tennis Value Bets</strong> • Aggiornamento automatico ogni 5 minuti<br>
        Dati in tempo reale • Analisi statistiche avanzate • Value betting intelligente
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
