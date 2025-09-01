
"""
Modulo per calcolo metriche avanzate di tennis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import math
from datetime import datetime, timedelta

class TennisAdvancedMetrics:
    """Calcolatore di metriche avanzate per tennis"""
    
    @staticmethod
    def calculate_dominance_ratio(return_points_won_pct: float, service_points_lost_pct: float) -> float:
        """
        Dominance Ratio = (% punti vinti in risposta) / (% punti persi al servizio)
        DR > 1.0 indica dominanza del giocatore
        """
        if service_points_lost_pct == 0:
            return float('inf') if return_points_won_pct > 0 else 1.0
        return return_points_won_pct / service_points_lost_pct
    
    @staticmethod
    def calculate_games_dominance_ratio(return_games_won_pct: float, service_games_lost_pct: float) -> float:
        """
        Games Dominance Ratio a livello di giochi invece che punti
        """
        if service_games_lost_pct == 0:
            return float('inf') if return_games_won_pct > 0 else 1.0
        return return_games_won_pct / service_games_lost_pct
    
    @staticmethod
    def calculate_momentum_score(recent_points: List[bool], leverage_weights: Optional[List[float]] = None) -> float:
        """
        Momentum Score usando exponentially weighted moving average
        recent_points: lista di boolean (True = punto vinto, False = punto perso)
        leverage_weights: pesi per importanza dei punti (opzionale)
        """
        if not recent_points:
            return 0.5
        
        if leverage_weights is None:
            # Pesi esponenziali decrescenti (più recente = più importante)
            leverage_weights = [0.5 ** i for i in range(len(recent_points))]
        
        if len(leverage_weights) != len(recent_points):
            leverage_weights = leverage_weights[:len(recent_points)]
        
        weighted_sum = sum(point * weight for point, weight in zip(recent_points, leverage_weights))
        total_weight = sum(leverage_weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    @staticmethod
    def calculate_leverage(current_score: Dict[str, int], match_format: str = "best_of_3") -> float:
        """
        Calcola leverage di un punto = quanto cambia la probabilità di vittoria
        current_score: {"sets_p1": 1, "sets_p2": 0, "games_p1": 4, "games_p2": 3, "points_p1": 30, "points_p2": 40}
        """
        # Implementazione semplificata - in produzione userebbe modelli più sofisticati
        sets_p1 = current_score.get("sets_p1", 0)
        sets_p2 = current_score.get("sets_p2", 0)
        games_p1 = current_score.get("games_p1", 0)
        games_p2 = current_score.get("games_p2", 0)
        points_p1 = current_score.get("points_p1", 0)
        points_p2 = current_score.get("points_p2", 0)
        
        # Situazioni ad alto leverage
        leverage = 0.1  # base
        
        # Set point
        if (match_format == "best_of_3" and max(sets_p1, sets_p2) == 1) or \
           (match_format == "best_of_5" and max(sets_p1, sets_p2) == 2):
            if games_p1 >= 5 and games_p1 > games_p2:
                leverage += 0.3
            elif games_p2 >= 5 and games_p2 > games_p1:
                leverage += 0.3
        
        # Break point
        if points_p1 >= 40 and points_p2 < 40:
            leverage += 0.2
        elif points_p2 >= 40 and points_p1 < 40:
            leverage += 0.2
        
        # Deuce situations
        if points_p1 >= 40 and points_p2 >= 40:
            leverage += 0.15
        
        # Tiebreak
        if games_p1 == 6 and games_p2 == 6:
            leverage += 0.25
        
        return min(leverage, 1.0)
    
    @staticmethod
    def calculate_pressure_points_performance(break_points_won: int, break_points_total: int,
                                            set_points_won: int, set_points_total: int,
                                            match_points_won: int, match_points_total: int) -> float:
        """
        Calcola performance nei punti sotto pressione
        """
        total_pressure_points = break_points_total + set_points_total + match_points_total
        total_pressure_won = break_points_won + set_points_won + match_points_won
        
        if total_pressure_points == 0:
            return 0.5
        
        return total_pressure_won / total_pressure_points
    
    @staticmethod
    def calculate_hot_hand_probability(recent_results: List[bool], window_size: int = 5) -> float:
        """
        Calcola probabilità "hot hand" basata su risultati recenti
        """
        if len(recent_results) < window_size:
            return 0.5
        
        recent_window = recent_results[-window_size:]
        wins_in_window = sum(recent_window)
        
        # Modello semplificato: più vittorie recenti = maggiore probabilità
        base_prob = 0.5
        hot_hand_boost = (wins_in_window / window_size - 0.5) * 0.2
        
        return max(0.1, min(0.9, base_prob + hot_hand_boost))
    
    @staticmethod
    def calculate_match_quality_score(stats: Dict[str, Any]) -> float:
        """
        Calcola punteggio qualità partita basato su varie metriche
        """
        quality_factors = []
        
        # Durata partita (partite troppo corte o lunghe = qualità minore)
        duration = stats.get("match_duration_minutes", 120)
        if 90 <= duration <= 180:
            quality_factors.append(0.8)
        elif 60 <= duration <= 240:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.4)
        
        # Equilibrio nel punteggio
        p1_points = stats.get("p1_total_points_won", 100)
        p2_points = stats.get("p2_total_points_won", 100)
        total_points = p1_points + p2_points
        
        if total_points > 0:
            balance = min(p1_points, p2_points) / total_points
            quality_factors.append(balance * 2)  # Max 1.0 quando 50-50
        
        # Numero di break points (più break points = partita più combattuta)
        total_bp = stats.get("p1_break_points_opportunities", 0) + stats.get("p2_break_points_opportunities", 0)
        bp_factor = min(1.0, total_bp / 10)  # Normalizza a max 1.0
        quality_factors.append(bp_factor)
        
        # Winners vs Unforced Errors ratio
        p1_winners = stats.get("p1_winners", 20)
        p1_ue = stats.get("p1_unforced_errors", 20)
        p2_winners = stats.get("p2_winners", 20)
        p2_ue = stats.get("p2_unforced_errors", 20)
        
        total_winners = p1_winners + p2_winners
        total_ue = p1_ue + p2_ue
        
        if total_ue > 0:
            winners_ratio = total_winners / (total_winners + total_ue)
            quality_factors.append(winners_ratio)
        
        # Media pesata dei fattori
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
    
    @staticmethod
    def calculate_surface_adjustment(player_stats: Dict[str, Any], surface: str) -> float:
        """
        Calcola fattore di aggiustamento per superficie
        """
        surface_stats = {
            "Hard": {
                "wins": player_stats.get("hard_wins", 0),
                "losses": player_stats.get("hard_losses", 0)
            },
            "Clay": {
                "wins": player_stats.get("clay_wins", 0),
                "losses": player_stats.get("clay_losses", 0)
            },
            "Grass": {
                "wins": player_stats.get("grass_wins", 0),
                "losses": player_stats.get("grass_losses", 0)
            }
        }
        
        surface_data = surface_stats.get(surface, {"wins": 0, "losses": 0})
        total_matches = surface_data["wins"] + surface_data["losses"]
        
        if total_matches == 0:
            return 1.0  # Nessun aggiustamento se non ci sono dati
        
        win_rate = surface_data["wins"] / total_matches
        
        # Aggiustamento basato su win rate della superficie vs media generale
        total_wins = sum(s["wins"] for s in surface_stats.values())
        total_losses = sum(s["losses"] for s in surface_stats.values())
        overall_matches = total_wins + total_losses
        
        if overall_matches == 0:
            return 1.0
        
        overall_win_rate = total_wins / overall_matches
        
        # Fattore di aggiustamento: +/- 20% max
        adjustment = (win_rate - overall_win_rate) * 0.4
        return max(0.8, min(1.2, 1.0 + adjustment))
    
    @staticmethod
    def calculate_elo_rating_change(winner_elo: float, loser_elo: float, 
                                  tournament_k_factor: float = 32) -> Tuple[float, float]:
        """
        Calcola cambiamento Elo rating dopo una partita
        """
        # Probabilità attesa di vittoria
        expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
        expected_loser = 1 - expected_winner
        
        # Cambiamento rating
        winner_change = tournament_k_factor * (1 - expected_winner)
        loser_change = tournament_k_factor * (0 - expected_loser)
        
        return winner_change, loser_change
    
    @staticmethod
    def calculate_form_rating(recent_matches: List[Dict[str, Any]], days: int = 90) -> float:
        """
        Calcola rating forma basato su performance recenti
        """
        if not recent_matches:
            return 50.0  # Rating neutro
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_matches = [m for m in recent_matches 
                         if datetime.fromisoformat(m.get("date", "2000-01-01")) >= cutoff_date]
        
        if not recent_matches:
            return 50.0
        
        # Peso decrescente per partite più vecchie
        total_weight = 0
        weighted_score = 0
        
        for i, match in enumerate(reversed(recent_matches)):  # Più recenti prima
            weight = 0.9 ** i  # Peso decrescente esponenziale
            
            # Punteggio partita basato su risultato e qualità avversario
            if match.get("won", False):
                match_score = 70 + min(30, match.get("opponent_ranking", 100) / 10)
            else:
                match_score = 30 - min(20, match.get("opponent_ranking", 100) / 20)
            
            weighted_score += match_score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 50.0
    
    @staticmethod
    def predict_match_outcome(player1_stats: Dict[str, Any], player2_stats: Dict[str, Any],
                            surface: str, tournament_level: str = "ATP250") -> Dict[str, float]:
        """
        Predice outcome partita basato su statistiche e metriche avanzate
        """
        # Elo ratings
        p1_elo = player1_stats.get("elo_rating", 1800)
        p2_elo = player2_stats.get("elo_rating", 1800)
        
        # Aggiustamenti superficie
        p1_surface_adj = TennisAdvancedMetrics.calculate_surface_adjustment(player1_stats, surface)
        p2_surface_adj = TennisAdvancedMetrics.calculate_surface_adjustment(player2_stats, surface)
        
        adjusted_p1_elo = p1_elo * p1_surface_adj
        adjusted_p2_elo = p2_elo * p2_surface_adj
        
        # Forma recente
        p1_form = player1_stats.get("recent_form_rating", 50)
        p2_form = player2_stats.get("recent_form_rating", 50)
        
        # Dominance ratios
        p1_dr = player1_stats.get("dominance_ratio", 1.0)
        p2_dr = player2_stats.get("dominance_ratio", 1.0)
        
        # Calcolo probabilità base da Elo
        elo_diff = adjusted_p1_elo - adjusted_p2_elo
        base_prob_p1 = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # Aggiustamenti per forma e dominance
        form_adjustment = (p1_form - p2_form) / 200  # Max +/- 0.25
        dr_adjustment = (p1_dr - p2_dr) / 10  # Aggiustamento più piccolo
        
        # Probabilità finale
        final_prob_p1 = base_prob_p1 + form_adjustment + dr_adjustment
        final_prob_p1 = max(0.05, min(0.95, final_prob_p1))  # Clamp tra 5% e 95%
        
        return {
            "player1_win_probability": final_prob_p1,
            "player2_win_probability": 1 - final_prob_p1,
            "confidence": abs(final_prob_p1 - 0.5) * 2,  # 0 = no confidence, 1 = max confidence
            "elo_difference": elo_diff,
            "surface_advantage_p1": p1_surface_adj - 1.0,
            "surface_advantage_p2": p2_surface_adj - 1.0,
            "form_difference": p1_form - p2_form
        }
