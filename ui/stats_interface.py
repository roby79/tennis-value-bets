
"""
Interfaccia Streamlit per statistiche tennis
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go

from models.stats_models import TennisStatsDatabase
from services.data_fetcher import TennisDataFetcher
from analytics.advanced_metrics import TennisAdvancedMetrics
from visualization.stats_charts import TennisStatsVisualizer

class TennisStatsInterface:
    """Interfaccia principale per statistiche tennis"""
    
    def __init__(self):
        self.db = TennisStatsDatabase()
        self.fetcher = TennisDataFetcher()
        self.metrics = TennisAdvancedMetrics()
        self.visualizer = TennisStatsVisualizer()
    
    def render_main_interface(self):
        """Renderizza interfaccia principale"""
        st.title("🎾 Sistema Completo Statistiche Tennis")
        
        # Sidebar per navigazione
        page = st.sidebar.selectbox(
            "📊 Sezione Statistiche",
            [
                "🏠 Dashboard Generale",
                "👥 Confronto Giocatori", 
                "📈 Analisi Partite",
                "🏆 Performance Tornei",
                "📊 Metriche Avanzate",
                "⚡ Statistiche Live",
                "📋 Gestione Dati"
            ]
        )
        
        if page == "🏠 Dashboard Generale":
            self.render_general_dashboard()
        elif page == "👥 Confronto Giocatori":
            self.render_player_comparison()
        elif page == "📈 Analisi Partite":
            self.render_match_analysis()
        elif page == "🏆 Performance Tornei":
            self.render_tournament_performance()
        elif page == "📊 Metriche Avanzate":
            self.render_advanced_metrics()
        elif page == "⚡ Statistiche Live":
            self.render_live_stats()
        elif page == "📋 Gestione Dati":
            self.render_data_management()
    
    def render_general_dashboard(self):
        """Dashboard generale con overview statistiche"""
        st.header("🏠 Dashboard Generale")
        
        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Giocatori nel DB", "1,247", "+23")
        with col2:
            st.metric("Partite Analizzate", "15,892", "+156")
        with col3:
            st.metric("Tornei Coperti", "89", "+2")
        with col4:
            st.metric("Aggiornamento", "2 min fa", "🟢")
        
        st.divider()
        
        # Grafici overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Top 10 Giocatori per Elo Rating")
            
            # Simula dati top players
            top_players_data = {
                'Giocatore': ['Djokovic', 'Alcaraz', 'Medvedev', 'Sinner', 'Tsitsipas', 
                             'Zverev', 'Nadal', 'Ruud', 'Rublev', 'Fritz'],
                'Elo': [2150, 2089, 2045, 2012, 1987, 1965, 1943, 1921, 1898, 1876],
                'Ranking': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
            
            df_top = pd.DataFrame(top_players_data)
            
            fig_top = go.Figure(data=[
                go.Bar(x=df_top['Giocatore'], y=df_top['Elo'], 
                      text=df_top['Elo'], textposition='auto',
                      marker_color='lightblue')
            ])
            fig_top.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_top, use_container_width=True)
        
        with col2:
            st.subheader("🌍 Distribuzione per Paese")
            
            countries_data = {
                'Paese': ['USA', 'ESP', 'ITA', 'FRA', 'GER', 'RUS', 'Altri'],
                'Giocatori': [156, 89, 67, 54, 48, 43, 790]
            }
            
            df_countries = pd.DataFrame(countries_data)
            
            fig_countries = go.Figure(data=[
                go.Pie(labels=df_countries['Paese'], values=df_countries['Giocatori'],
                      hole=0.3)
            ])
            fig_countries.update_layout(height=400)
            st.plotly_chart(fig_countries, use_container_width=True)
        
        st.divider()
        
        # Statistiche recenti
        st.subheader("📈 Attività Recente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔥 Giocatori in Forma**")
            form_data = [
                {"Giocatore": "Carlos Alcaraz", "Forma": 87, "Trend": "📈"},
                {"Giocatore": "Jannik Sinner", "Forma": 84, "Trend": "📈"},
                {"Giocatore": "Daniil Medvedev", "Forma": 79, "Trend": "📊"},
                {"Giocatore": "Alexander Zverev", "Forma": 76, "Trend": "📉"},
                {"Giocatore": "Stefanos Tsitsipas", "Forma": 73, "Trend": "📊"}
            ]
            
            for player in form_data:
                st.write(f"{player['Trend']} **{player['Giocatore']}** - Forma: {player['Forma']}/100")
        
        with col2:
            st.markdown("**⚡ Partite Recenti Analizzate**")
            recent_matches = [
                "Sinner vs Medvedev (US Open)",
                "Alcaraz vs Djokovic (Wimbledon)", 
                "Swiatek vs Gauff (WTA Finals)",
                "Zverev vs Tsitsipas (ATP Masters)",
                "Rybakina vs Sabalenka (Miami Open)"
            ]
            
            for match in recent_matches:
                st.write(f"🎾 {match}")
    
    def render_player_comparison(self):
        """Interfaccia confronto giocatori"""
        st.header("👥 Confronto Giocatori")
        
        # Selezione giocatori
        col1, col2 = st.columns(2)
        
        with col1:
            player1 = st.selectbox(
                "🎾 Seleziona Giocatore 1",
                ["Novak Djokovic", "Carlos Alcaraz", "Daniil Medvedev", "Jannik Sinner", 
                 "Stefanos Tsitsipas", "Alexander Zverev", "Rafael Nadal"]
            )
        
        with col2:
            player2 = st.selectbox(
                "🎾 Seleziona Giocatore 2", 
                ["Carlos Alcaraz", "Daniil Medvedev", "Jannik Sinner", "Stefanos Tsitsipas",
                 "Alexander Zverev", "Rafael Nadal", "Novak Djokovic"]
            )
        
        if player1 and player2 and player1 != player2:
            
            # Fetch statistiche (simulate)
            p1_stats = self.fetcher.fetch_player_stats(player1)
            p2_stats = self.fetcher.fetch_player_stats(player2)
            
            # Radar chart confronto
            st.subheader("📊 Confronto Radar")
            radar_fig = self.visualizer.create_player_comparison_radar(
                p1_stats, p2_stats, player1, player2
            )
            st.plotly_chart(radar_fig, use_container_width=True)
            
            # Statistiche dettagliate
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📋 {player1}")
                self._display_player_stats_card(p1_stats)
            
            with col2:
                st.subheader(f"📋 {player2}")
                self._display_player_stats_card(p2_stats)
            
            # Head-to-Head
            st.divider()
            st.subheader("🥊 Head-to-Head")
            
            h2h_data = self.fetcher.fetch_head_to_head(player1, player2)
            h2h_fig = self.visualizer.create_head_to_head_history(h2h_data, player1, player2)
            st.plotly_chart(h2h_fig, use_container_width=True)
            
            # Predizione match
            st.divider()
            st.subheader("🔮 Predizione Match")
            
            surface = st.selectbox("Superficie", ["Hard", "Clay", "Grass"])
            tournament_level = st.selectbox("Livello Torneo", ["ATP250", "ATP500", "ATP1000", "Grand Slam"])
            
            if st.button("🎯 Calcola Predizione"):
                prediction = self.metrics.predict_match_outcome(p1_stats, p2_stats, surface, tournament_level)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        f"Probabilità {player1}",
                        f"{prediction['player1_win_probability']:.1%}",
                        f"{prediction['surface_advantage_p1']:+.1%}"
                    )
                
                with col2:
                    st.metric(
                        f"Probabilità {player2}",
                        f"{prediction['player2_win_probability']:.1%}",
                        f"{prediction['surface_advantage_p2']:+.1%}"
                    )
                
                with col3:
                    st.metric(
                        "Confidenza",
                        f"{prediction['confidence']:.1%}",
                        f"Elo Diff: {prediction['elo_difference']:+.0f}"
                    )
    
    def render_match_analysis(self):
        """Interfaccia analisi partite"""
        st.header("📈 Analisi Partite")
        
        # Selezione partita
        match_options = [
            "Sinner vs Medvedev - US Open 2024",
            "Alcaraz vs Djokovic - Wimbledon 2024",
            "Swiatek vs Gauff - WTA Finals 2024",
            "Zverev vs Tsitsipas - ATP Masters 2024"
        ]
        
        selected_match = st.selectbox("🎾 Seleziona Partita", match_options)
        
        if selected_match:
            # Simula statistiche partita
            match_stats = self.fetcher.fetch_match_stats("match_123")
            
            # Overview partita
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Durata", f"{match_stats['match_duration_minutes']} min")
            with col2:
                st.metric("Set Giocati", match_stats['sets_played'])
            with col3:
                st.metric("Giochi Totali", match_stats['total_games'])
            with col4:
                st.metric("Qualità Match", f"{match_stats['match_quality_score']}/10")
            
            # Confronto statistiche
            st.subheader("📊 Statistiche Dettagliate")
            
            player1_name = selected_match.split(" vs ")[0]
            player2_name = selected_match.split(" vs ")[1].split(" - ")[0]
            
            stats_fig = self.visualizer.create_match_stats_comparison(
                match_stats, player1_name, player2_name
            )
            st.plotly_chart(stats_fig, use_container_width=True)
            
            # Metriche avanzate
            st.subheader("🔬 Metriche Avanzate")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Player 1 - Metriche**")
                
                # Calcola dominance ratio
                p1_return_won = match_stats.get('p1_first_return_won_pct', 35)
                p1_service_lost = 100 - match_stats.get('p1_first_serve_won_pct', 70)
                p1_dr = self.metrics.calculate_dominance_ratio(p1_return_won, p1_service_lost)
                
                st.metric("Dominance Ratio", f"{p1_dr:.2f}")
                st.metric("Pressure Points", f"{match_stats.get('p1_break_points_converted', 3)}/{match_stats.get('p1_break_points_opportunities', 8)}")
                st.metric("Winners/UE Ratio", f"{match_stats.get('p1_winners', 25)}/{match_stats.get('p1_unforced_errors', 18)}")
            
            with col2:
                st.markdown("**Player 2 - Metriche**")
                
                p2_return_won = match_stats.get('p2_first_return_won_pct', 35)
                p2_service_lost = 100 - match_stats.get('p2_first_serve_won_pct', 70)
                p2_dr = self.metrics.calculate_dominance_ratio(p2_return_won, p2_service_lost)
                
                st.metric("Dominance Ratio", f"{p2_dr:.2f}")
                st.metric("Pressure Points", f"{match_stats.get('p2_break_points_converted', 2)}/{match_stats.get('p2_break_points_opportunities', 5)}")
                st.metric("Winners/UE Ratio", f"{match_stats.get('p2_winners', 22)}/{match_stats.get('p2_unforced_errors', 24)}")
            
            # Export statistiche
            st.divider()
            
            if st.button("📥 Esporta Statistiche CSV"):
                # Crea DataFrame per export
                export_data = {
                    'Statistica': ['Aces', 'Doppi Falli', 'Prime Servizio %', 'Vincenti', 'Errori Non Forzati'],
                    player1_name: [
                        match_stats.get('p1_aces', 0),
                        match_stats.get('p1_double_faults', 0),
                        match_stats.get('p1_first_serve_pct', 0),
                        match_stats.get('p1_winners', 0),
                        match_stats.get('p1_unforced_errors', 0)
                    ],
                    player2_name: [
                        match_stats.get('p2_aces', 0),
                        match_stats.get('p2_double_faults', 0),
                        match_stats.get('p2_first_serve_pct', 0),
                        match_stats.get('p2_winners', 0),
                        match_stats.get('p2_unforced_errors', 0)
                    ]
                }
                
                df_export = pd.DataFrame(export_data)
                csv = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="⬇️ Scarica CSV",
                    data=csv,
                    file_name=f"match_stats_{selected_match.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
    
    def render_tournament_performance(self):
        """Interfaccia performance tornei"""
        st.header("🏆 Performance nei Tornei")
        
        # Selezione giocatore
        player = st.selectbox(
            "👤 Seleziona Giocatore",
            ["Novak Djokovic", "Carlos Alcaraz", "Jannik Sinner", "Rafael Nadal", "Daniil Medvedev"]
        )
        
        if player:
            # Fetch dati tornei
            tournament_data = self.fetcher.fetch_tournament_history(player, "US Open", 5)
            
            # Heatmap performance
            st.subheader("🗓️ Performance Storica")
            heatmap_fig = self.visualizer.create_tournament_performance_heatmap(tournament_data, player)
            st.plotly_chart(heatmap_fig, use_container_width=True)
            
            # Statistiche per superficie
            st.subheader("🏟️ Performance per Superficie")
            player_stats = self.fetcher.fetch_player_stats(player)
            surface_fig = self.visualizer.create_surface_performance_chart(player_stats, player)
            st.plotly_chart(surface_fig, use_container_width=True)
            
            # Tabella dettagliata
            st.subheader("📋 Dettaglio Performance")
            
            if tournament_data:
                df_tournaments = pd.DataFrame(tournament_data)
                df_tournaments['Win %'] = (df_tournaments['wins'] / (df_tournaments['wins'] + df_tournaments['losses']) * 100).round(1)
                
                st.dataframe(
                    df_tournaments[['year', 'matches_played', 'wins', 'losses', 'Win %', 'best_result', 'prize_money']],
                    use_container_width=True
                )
                
                # Statistiche aggregate
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_matches = df_tournaments['matches_played'].sum()
                    st.metric("Partite Totali", total_matches)
                
                with col2:
                    total_wins = df_tournaments['wins'].sum()
                    st.metric("Vittorie", total_wins)
                
                with col3:
                    win_pct = (total_wins / total_matches * 100) if total_matches > 0 else 0
                    st.metric("Win %", f"{win_pct:.1f}%")
                
                with col4:
                    total_prize = df_tournaments['prize_money'].sum()
                    st.metric("Prize Money", f"${total_prize:,.0f}")
    
    def render_advanced_metrics(self):
        """Interfaccia metriche avanzate"""
        st.header("📊 Metriche Avanzate")
        
        # Calcolatori metriche
        st.subheader("🧮 Calcolatori")
        
        tab1, tab2, tab3 = st.tabs(["Dominance Ratio", "Momentum Score", "Match Prediction"])
        
        with tab1:
            st.markdown("**Calcola Dominance Ratio**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                return_won = st.slider("% Punti Vinti in Risposta", 0.0, 50.0, 35.0, 0.1)
            
            with col2:
                service_lost = st.slider("% Punti Persi al Servizio", 0.0, 50.0, 25.0, 0.1)
            
            if service_lost > 0:
                dr = self.metrics.calculate_dominance_ratio(return_won, service_lost)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Dominance Ratio", f"{dr:.3f}")
                
                with col2:
                    if dr > 1.0:
                        st.success("🟢 Giocatore Dominante")
                    else:
                        st.error("🔴 Giocatore Non Dominante")
                
                with col3:
                    dominance_level = "Alta" if dr > 1.2 else "Media" if dr > 0.8 else "Bassa"
                    st.info(f"Dominanza: {dominance_level}")
        
        with tab2:
            st.markdown("**Calcola Momentum Score**")
            
            st.write("Inserisci risultati ultimi punti (1 = vinto, 0 = perso):")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            recent_points = []
            with col1:
                p1 = st.selectbox("Punto -4", [0, 1], key="p1")
                recent_points.append(bool(p1))
            with col2:
                p2 = st.selectbox("Punto -3", [0, 1], key="p2")
                recent_points.append(bool(p2))
            with col3:
                p3 = st.selectbox("Punto -2", [0, 1], key="p3")
                recent_points.append(bool(p3))
            with col4:
                p4 = st.selectbox("Punto -1", [0, 1], key="p4")
                recent_points.append(bool(p4))
            with col5:
                p5 = st.selectbox("Punto Attuale", [0, 1], key="p5")
                recent_points.append(bool(p5))
            
            momentum = self.metrics.calculate_momentum_score(recent_points)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Momentum Score", f"{momentum:.3f}")
            
            with col2:
                if momentum > 0.6:
                    st.success("🟢 Momentum Positivo")
                elif momentum > 0.4:
                    st.warning("🟡 Momentum Neutro")
                else:
                    st.error("🔴 Momentum Negativo")
            
            with col3:
                momentum_pct = momentum * 100
                st.info(f"Probabilità: {momentum_pct:.1f}%")
        
        with tab3:
            st.markdown("**Predizione Match**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Giocatore 1**")
                p1_elo = st.number_input("Elo Rating", 1200, 2500, 1900, key="p1_elo")
                p1_form = st.slider("Forma (0-100)", 0, 100, 60, key="p1_form")
                p1_surface_wins = st.number_input("Vittorie Superficie", 0, 100, 25, key="p1_surf")
                p1_surface_losses = st.number_input("Sconfitte Superficie", 0, 100, 15, key="p1_surf_l")
            
            with col2:
                st.markdown("**Giocatore 2**")
                p2_elo = st.number_input("Elo Rating", 1200, 2500, 1850, key="p2_elo")
                p2_form = st.slider("Forma (0-100)", 0, 100, 55, key="p2_form")
                p2_surface_wins = st.number_input("Vittorie Superficie", 0, 100, 20, key="p2_surf")
                p2_surface_losses = st.number_input("Sconfitte Superficie", 0, 100, 18, key="p2_surf_l")
            
            surface = st.selectbox("Superficie", ["Hard", "Clay", "Grass"])
            
            if st.button("🎯 Calcola Predizione"):
                # Simula statistiche per predizione
                p1_stats = {
                    "elo_rating": p1_elo,
                    "recent_form_rating": p1_form,
                    "hard_wins": p1_surface_wins if surface == "Hard" else 0,
                    "hard_losses": p1_surface_losses if surface == "Hard" else 0,
                    "clay_wins": p1_surface_wins if surface == "Clay" else 0,
                    "clay_losses": p1_surface_losses if surface == "Clay" else 0,
                    "grass_wins": p1_surface_wins if surface == "Grass" else 0,
                    "grass_losses": p1_surface_losses if surface == "Grass" else 0,
                    "dominance_ratio": 1.0
                }
                
                p2_stats = {
                    "elo_rating": p2_elo,
                    "recent_form_rating": p2_form,
                    "hard_wins": p2_surface_wins if surface == "Hard" else 0,
                    "hard_losses": p2_surface_losses if surface == "Hard" else 0,
                    "clay_wins": p2_surface_wins if surface == "Clay" else 0,
                    "clay_losses": p2_surface_losses if surface == "Clay" else 0,
                    "grass_wins": p2_surface_wins if surface == "Grass" else 0,
                    "grass_losses": p2_surface_losses if surface == "Grass" else 0,
                    "dominance_ratio": 1.0
                }
                
                prediction = self.metrics.predict_match_outcome(p1_stats, p2_stats, surface)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Probabilità P1", f"{prediction['player1_win_probability']:.1%}")
                
                with col2:
                    st.metric("Probabilità P2", f"{prediction['player2_win_probability']:.1%}")
                
                with col3:
                    st.metric("Confidenza", f"{prediction['confidence']:.1%}")
    
    def render_live_stats(self):
        """Interfaccia statistiche live"""
        st.header("⚡ Statistiche Live")
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)")
        
        if auto_refresh:
            st.rerun()
        
        # Fetch partite live
        live_matches = self.fetcher.get_live_matches()
        
        if live_matches:
            st.subheader(f"🎾 Partite Live ({len(live_matches)})")
            
            for match in live_matches:
                with st.expander(f"{match['player1']} vs {match['player2']} - {match['tournament']}"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Info Partita**")
                        st.write(f"🏟️ Superficie: {match['surface']}")
                        st.write(f"📊 Set: {match['current_set']}")
                        st.write(f"🎯 Score: {match['score']}")
                    
                    with col2:
                        st.markdown(f"**{match['player1']}**")
                        st.write(f"🎾 Aces: {match['p1_aces']}")
                        st.write(f"❌ Doppi Falli: {match['p1_double_faults']}")
                        st.write(f"📈 Prime Servizio: {match['p1_first_serve_pct']}%")
                        st.write(f"🏆 Vincenti: {match['p1_winners']}")
                        st.write(f"💥 Errori NF: {match['p1_unforced_errors']}")
                    
                    with col3:
                        st.markdown(f"**{match['player2']}**")
                        st.write(f"🎾 Aces: {match['p2_aces']}")
                        st.write(f"❌ Doppi Falli: {match['p2_double_faults']}")
                        st.write(f"📈 Prime Servizio: {match['p2_first_serve_pct']}%")
                        st.write(f"🏆 Vincenti: {match['p2_winners']}")
                        st.write(f"💥 Errori NF: {match['p2_unforced_errors']}")
        else:
            st.info("Nessuna partita live al momento")
        
        # Refresh manuale
        if st.button("🔄 Aggiorna Dati"):
            st.rerun()
    
    def render_data_management(self):
        """Interfaccia gestione dati"""
        st.header("📋 Gestione Dati")
        
        tab1, tab2, tab3 = st.tabs(["Import/Export", "Aggiornamenti", "Configurazione"])
        
        with tab1:
            st.subheader("📥 Import Dati")
            
            uploaded_file = st.file_uploader("Carica file CSV", type=['csv'])
            
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                st.write("Preview dati:")
                st.dataframe(df.head())
                
                if st.button("✅ Importa nel Database"):
                    st.success("Dati importati con successo!")
            
            st.divider()
            
            st.subheader("📤 Export Dati")
            
            export_type = st.selectbox("Tipo Export", [
                "Tutti i Giocatori",
                "Statistiche Partite",
                "Head-to-Head",
                "Performance Tornei"
            ])
            
            if st.button("📥 Genera Export"):
                # Simula export
                sample_data = {
                    'ID': [1, 2, 3],
                    'Nome': ['Player 1', 'Player 2', 'Player 3'],
                    'Ranking': [10, 25, 47]
                }
                
                df_export = pd.DataFrame(sample_data)
                csv = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="⬇️ Scarica CSV",
                    data=csv,
                    file_name=f"tennis_export_{export_type.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )
        
        with tab2:
            st.subheader("🔄 Aggiornamenti Automatici")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Ranking ATP/WTA**")
                if st.button("🔄 Aggiorna Rankings"):
                    with st.spinner("Aggiornamento rankings..."):
                        # Simula aggiornamento
                        import time
                        time.sleep(2)
                    st.success("Rankings aggiornati!")
            
            with col2:
                st.markdown("**Statistiche Giocatori**")
                if st.button("🔄 Aggiorna Statistiche"):
                    with st.spinner("Aggiornamento statistiche..."):
                        import time
                        time.sleep(3)
                    st.success("Statistiche aggiornate!")
            
            st.divider()
            
            st.markdown("**⏰ Programmazione Automatica**")
            
            auto_update_rankings = st.checkbox("Aggiorna rankings automaticamente (giornaliero)")
            auto_update_stats = st.checkbox("Aggiorna statistiche automaticamente (settimanale)")
            
            if st.button("💾 Salva Configurazione"):
                st.success("Configurazione salvata!")
        
        with tab3:
            st.subheader("⚙️ Configurazione Sistema")
            
            st.markdown("**🔗 Fonti Dati**")
            
            data_sources = st.multiselect(
                "Seleziona fonti dati attive",
                ["ATP Official", "WTA Official", "Ultimate Tennis Statistics", "Tennis Abstract", "Sofascore"],
                default=["ATP Official", "WTA Official"]
            )
            
            st.markdown("**📊 Metriche Calcolate**")
            
            enable_dominance = st.checkbox("Calcola Dominance Ratio", value=True)
            enable_momentum = st.checkbox("Calcola Momentum Score", value=True)
            enable_predictions = st.checkbox("Abilita Predizioni", value=True)
            
            st.markdown("**🎯 Soglie Avvisi**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                form_threshold = st.slider("Soglia Forma Critica", 0, 50, 30)
            
            with col2:
                ranking_change_threshold = st.slider("Soglia Cambio Ranking", 1, 20, 5)
            
            if st.button("💾 Salva Tutte le Configurazioni"):
                st.success("Configurazioni salvate con successo!")
    
    def _display_player_stats_card(self, stats: Dict[str, Any]):
        """Mostra card con statistiche giocatore"""
        
        # Metriche principali
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Elo Rating", f"{stats.get('elo_rating', 1800):.0f}")
            st.metric("Vittorie", stats.get('career_wins', 0))
            st.metric("Dominance Ratio", f"{stats.get('dominance_ratio', 1.0):.2f}")
        
        with col2:
            st.metric("Ranking", f"#{stats.get('atp_ranking', 999)}")
            st.metric("Sconfitte", stats.get('career_losses', 0))
            st.metric("Forma", f"{stats.get('recent_form_rating', 50):.0f}/100")
        
        # Statistiche servizio
        st.markdown("**🎾 Servizio**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"Prime: {stats.get('avg_first_serve_pct', 65):.1f}%")
        with col2:
            st.write(f"Aces/Match: {stats.get('avg_aces_per_match', 8):.1f}")
        with col3:
            st.write(f"DF/Match: {stats.get('avg_double_faults_per_match', 3):.1f}")
        
        # Statistiche risposta
        st.markdown("**🔄 Risposta**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"Prime Risposta: {stats.get('avg_first_return_won_pct', 35):.1f}%")
        with col2:
            st.write(f"Break Points: {stats.get('avg_break_points_converted_pct', 45):.1f}%")
        
        # Superfici
        st.markdown("**🏟️ Superfici**")
        hard_total = stats.get('hard_wins', 0) + stats.get('hard_losses', 0)
        clay_total = stats.get('clay_wins', 0) + stats.get('clay_losses', 0)
        grass_total = stats.get('grass_wins', 0) + stats.get('grass_losses', 0)
        
        if hard_total > 0:
            hard_pct = stats.get('hard_wins', 0) / hard_total * 100
            st.write(f"Hard: {hard_pct:.1f}% ({hard_total} match)")
        
        if clay_total > 0:
            clay_pct = stats.get('clay_wins', 0) / clay_total * 100
            st.write(f"Clay: {clay_pct:.1f}% ({clay_total} match)")
        
        if grass_total > 0:
            grass_pct = stats.get('grass_wins', 0) / grass_total * 100
            st.write(f"Grass: {grass_pct:.1f}% ({grass_total} match)")
