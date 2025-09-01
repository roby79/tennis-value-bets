
"""
Modulo per visualizzazioni grafiche delle statistiche tennis
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import streamlit as st

class TennisStatsVisualizer:
    """Classe per creare visualizzazioni delle statistiche tennis"""
    
    @staticmethod
    def create_player_comparison_radar(player1_stats: Dict[str, Any], player2_stats: Dict[str, Any],
                                     player1_name: str, player2_name: str) -> go.Figure:
        """Crea radar chart per confronto tra due giocatori"""
        
        categories = [
            'Servizio', 'Risposta', 'Winners', 'Errori (inv)', 
            'Rete', 'Break Points', 'Forma', 'Ranking (inv)'
        ]
        
        # Normalizza le statistiche (0-100)
        p1_values = [
            player1_stats.get('avg_first_serve_won_pct', 70),
            player1_stats.get('avg_first_return_won_pct', 35),
            min(100, player1_stats.get('avg_winners_per_match', 30) * 2),
            max(0, 100 - player1_stats.get('avg_unforced_errors_per_match', 25) * 2),
            player1_stats.get('avg_net_points_won_pct', 70),
            player1_stats.get('avg_break_points_converted_pct', 45),
            player1_stats.get('recent_form_rating', 50),
            max(0, 100 - player1_stats.get('atp_ranking', 50))
        ]
        
        p2_values = [
            player2_stats.get('avg_first_serve_won_pct', 70),
            player2_stats.get('avg_first_return_won_pct', 35),
            min(100, player2_stats.get('avg_winners_per_match', 30) * 2),
            max(0, 100 - player2_stats.get('avg_unforced_errors_per_match', 25) * 2),
            player2_stats.get('avg_net_points_won_pct', 70),
            player2_stats.get('avg_break_points_converted_pct', 45),
            player2_stats.get('recent_form_rating', 50),
            max(0, 100 - player2_stats.get('atp_ranking', 50))
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=p1_values,
            theta=categories,
            fill='toself',
            name=player1_name,
            line_color='blue',
            fillcolor='rgba(0, 100, 255, 0.2)'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=p2_values,
            theta=categories,
            fill='toself',
            name=player2_name,
            line_color='red',
            fillcolor='rgba(255, 0, 0, 0.2)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title=f"Confronto Statistiche: {player1_name} vs {player2_name}",
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_surface_performance_chart(player_stats: Dict[str, Any], player_name: str) -> go.Figure:
        """Crea grafico performance per superficie"""
        
        surfaces = ['Hard', 'Clay', 'Grass']
        wins = [
            player_stats.get('hard_wins', 0),
            player_stats.get('clay_wins', 0),
            player_stats.get('grass_wins', 0)
        ]
        losses = [
            player_stats.get('hard_losses', 0),
            player_stats.get('clay_losses', 0),
            player_stats.get('grass_losses', 0)
        ]
        
        win_percentages = [
            (w / (w + l) * 100) if (w + l) > 0 else 0 
            for w, l in zip(wins, losses)
        ]
        
        total_matches = [w + l for w, l in zip(wins, losses)]
        
        fig = go.Figure()
        
        # Barre per win percentage
        fig.add_trace(go.Bar(
            x=surfaces,
            y=win_percentages,
            name='Win %',
            text=[f'{pct:.1f}%<br>({total} match)' for pct, total in zip(win_percentages, total_matches)],
            textposition='auto',
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1']
        ))
        
        fig.update_layout(
            title=f'Performance per Superficie - {player_name}',
            xaxis_title='Superficie',
            yaxis_title='Win Percentage (%)',
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_head_to_head_history(h2h_data: Dict[str, Any], player1_name: str, player2_name: str) -> go.Figure:
        """Crea visualizzazione head-to-head"""
        
        total_matches = h2h_data.get('total_matches', 0)
        p1_wins = h2h_data.get('player1_wins', 0)
        p2_wins = h2h_data.get('player2_wins', 0)
        
        if total_matches == 0:
            # Nessun precedente
            fig = go.Figure()
            fig.add_annotation(
                text="Nessun precedente tra questi giocatori",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title=f"Head-to-Head: {player1_name} vs {player2_name}",
                height=300,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
            return fig
        
        # Grafico a torta per vittorie totali
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=("Vittorie Totali", "Per Superficie")
        )
        
        # Pie chart vittorie
        fig.add_trace(go.Pie(
            labels=[player1_name, player2_name],
            values=[p1_wins, p2_wins],
            name="Vittorie",
            marker_colors=['#FF6B6B', '#4ECDC4']
        ), row=1, col=1)
        
        # Bar chart per superficie
        surfaces = ['Hard', 'Clay', 'Grass']
        p1_surface_wins = []
        p2_surface_wins = []
        
        for surface in surfaces:
            surface_matches = h2h_data.get(f'{surface.lower()}_matches', 0)
            surface_p1_wins = h2h_data.get(f'{surface.lower()}_p1_wins', 0)
            surface_p2_wins = surface_matches - surface_p1_wins
            
            p1_surface_wins.append(surface_p1_wins)
            p2_surface_wins.append(surface_p2_wins)
        
        fig.add_trace(go.Bar(
            x=surfaces,
            y=p1_surface_wins,
            name=player1_name,
            marker_color='#FF6B6B'
        ), row=1, col=2)
        
        fig.add_trace(go.Bar(
            x=surfaces,
            y=p2_surface_wins,
            name=player2_name,
            marker_color='#4ECDC4'
        ), row=1, col=2)
        
        fig.update_layout(
            title=f"Head-to-Head: {player1_name} vs {player2_name} ({total_matches} match)",
            height=400,
            barmode='stack'
        )
        
        return fig
    
    @staticmethod
    def create_form_trend_chart(form_data: List[Dict[str, Any]], player_name: str) -> go.Figure:
        """Crea grafico trend forma recente"""
        
        if not form_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Dati forma non disponibili",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title=f"Trend Forma - {player_name}", height=300)
            return fig
        
        dates = [d['date'] for d in form_data]
        elo_ratings = [d.get('elo_rating', 1800) for d in form_data]
        form_ratings = [d.get('form_rating', 50) for d in form_data]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Elo Rating', 'Form Rating'),
            vertical_spacing=0.1
        )
        
        # Elo rating trend
        fig.add_trace(go.Scatter(
            x=dates,
            y=elo_ratings,
            mode='lines+markers',
            name='Elo Rating',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ), row=1, col=1)
        
        # Form rating trend
        fig.add_trace(go.Scatter(
            x=dates,
            y=form_ratings,
            mode='lines+markers',
            name='Form Rating',
            line=dict(color='green', width=2),
            marker=dict(size=6),
            fill='tonexty' if len(form_ratings) > 1 else None,
            fillcolor='rgba(0, 255, 0, 0.1)'
        ), row=2, col=1)
        
        fig.update_layout(
            title=f'Trend Forma - {player_name}',
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Data", row=2, col=1)
        fig.update_yaxes(title_text="Elo", row=1, col=1)
        fig.update_yaxes(title_text="Forma", row=2, col=1, range=[0, 100])
        
        return fig
    
    @staticmethod
    def create_match_stats_comparison(match_stats: Dict[str, Any], player1_name: str, player2_name: str) -> go.Figure:
        """Crea confronto statistiche dettagliate partita"""
        
        categories = [
            'Aces', 'Doppi Falli', 'Prime Servizio %', 'Vincenti', 
            'Errori Non Forzati', 'Punti Rete %', 'Break Points Conv.'
        ]
        
        p1_values = [
            match_stats.get('p1_aces', 0),
            match_stats.get('p1_double_faults', 0),
            match_stats.get('p1_first_serve_pct', 60),
            match_stats.get('p1_winners', 0),
            match_stats.get('p1_unforced_errors', 0),
            match_stats.get('p1_net_points_won', 0) / max(1, match_stats.get('p1_net_points_total', 1)) * 100,
            match_stats.get('p1_break_points_converted', 0) / max(1, match_stats.get('p1_break_points_opportunities', 1)) * 100
        ]
        
        p2_values = [
            match_stats.get('p2_aces', 0),
            match_stats.get('p2_double_faults', 0),
            match_stats.get('p2_first_serve_pct', 60),
            match_stats.get('p2_winners', 0),
            match_stats.get('p2_unforced_errors', 0),
            match_stats.get('p2_net_points_won', 0) / max(1, match_stats.get('p2_net_points_total', 1)) * 100,
            match_stats.get('p2_break_points_converted', 0) / max(1, match_stats.get('p2_break_points_opportunities', 1)) * 100
        ]
        
        fig = go.Figure()
        
        x_pos = np.arange(len(categories))
        
        fig.add_trace(go.Bar(
            x=categories,
            y=p1_values,
            name=player1_name,
            marker_color='#FF6B6B',
            text=[f'{v:.1f}' for v in p1_values],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=categories,
            y=[-v for v in p2_values],  # Valori negativi per effetto specchio
            name=player2_name,
            marker_color='#4ECDC4',
            text=[f'{v:.1f}' for v in p2_values],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Confronto Statistiche Partita',
            xaxis_title='Statistiche',
            yaxis_title='Valori',
            barmode='relative',
            height=500,
            xaxis_tickangle=-45
        )
        
        # Linea zero
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        return fig
    
    @staticmethod
    def create_dominance_momentum_chart(match_data: List[Dict[str, Any]]) -> go.Figure:
        """Crea grafico dominance ratio e momentum nel tempo"""
        
        if not match_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Dati partita non disponibili",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title="Dominance & Momentum", height=300)
            return fig
        
        points = list(range(len(match_data)))
        p1_dominance = [d.get('p1_dominance_ratio', 1.0) for d in match_data]
        p2_dominance = [d.get('p2_dominance_ratio', 1.0) for d in match_data]
        p1_momentum = [d.get('p1_momentum_score', 0.5) for d in match_data]
        p2_momentum = [d.get('p2_momentum_score', 0.5) for d in match_data]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Dominance Ratio', 'Momentum Score'),
            vertical_spacing=0.1
        )
        
        # Dominance Ratio
        fig.add_trace(go.Scatter(
            x=points,
            y=p1_dominance,
            mode='lines',
            name='Player 1 Dominance',
            line=dict(color='blue', width=2)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=points,
            y=p2_dominance,
            mode='lines',
            name='Player 2 Dominance',
            line=dict(color='red', width=2)
        ), row=1, col=1)
        
        # Momentum Score
        fig.add_trace(go.Scatter(
            x=points,
            y=p1_momentum,
            mode='lines',
            name='Player 1 Momentum',
            line=dict(color='lightblue', width=2),
            fill='tonexty'
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=points,
            y=p2_momentum,
            mode='lines',
            name='Player 2 Momentum',
            line=dict(color='lightcoral', width=2)
        ), row=2, col=1)
        
        # Linee di riferimento
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=1, col=1)
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", row=2, col=1)
        
        fig.update_layout(
            title='Dominance Ratio e Momentum durante la Partita',
            height=600,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Punti", row=2, col=1)
        fig.update_yaxes(title_text="Dominance Ratio", row=1, col=1)
        fig.update_yaxes(title_text="Momentum Score", row=2, col=1, range=[0, 1])
        
        return fig
    
    @staticmethod
    def create_tournament_performance_heatmap(tournament_data: List[Dict[str, Any]], player_name: str) -> go.Figure:
        """Crea heatmap performance nei tornei"""
        
        if not tournament_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Dati tornei non disponibili",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title=f"Performance Tornei - {player_name}", height=300)
            return fig
        
        # Crea matrice per heatmap
        tournaments = list(set(d['tournament_name'] for d in tournament_data))
        years = sorted(list(set(d['year'] for d in tournament_data)))
        
        # Matrice win percentage
        z_data = []
        for tournament in tournaments:
            row = []
            for year in years:
                match = next((d for d in tournament_data 
                            if d['tournament_name'] == tournament and d['year'] == year), None)
                if match:
                    total = match['wins'] + match['losses']
                    win_pct = (match['wins'] / total * 100) if total > 0 else 0
                    row.append(win_pct)
                else:
                    row.append(None)
            z_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=years,
            y=tournaments,
            colorscale='RdYlGn',
            zmid=50,
            text=[[f'{v:.0f}%' if v is not None else 'N/A' for v in row] for row in z_data],
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=f'Performance nei Tornei - {player_name}',
            xaxis_title='Anno',
            yaxis_title='Torneo',
            height=max(400, len(tournaments) * 30)
        )
        
        return fig
