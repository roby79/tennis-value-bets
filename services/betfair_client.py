
"""
Client principale per Betfair Italia API
Gestisce recupero dati tennis, quote e piazzamento scommesse
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from config.betfair_it import (
    BETFAIR_IT_ENDPOINTS,
    RATE_LIMITS,
    TENNIS_CONFIG,
    ITALIAN_BETTING_RULES,
    ERROR_MESSAGES,
    NETWORK_CONFIG
)
from services.betfair_session import BetfairItalySession

class BetfairItalyClient:
    """Client per interagire con Betfair Italia API"""
    
    def __init__(self, session: BetfairItalySession):
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        
    def _rate_limit_check(self):
        """Applica rate limiting tra richieste"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / RATE_LIMITS['requests_per_second']
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_api_request(self, method: str, params: Dict[str, Any], endpoint: str = 'betting_json_rpc') -> Dict[str, Any]:
        """
        Effettua richiesta API con gestione errori e retry
        """
        if not self.session.is_logged_in():
            raise RuntimeError("Sessione non attiva")
            
        self._rate_limit_check()
        
        headers = self.session.get_auth_headers()
        
        # Payload JSON-RPC
        payload = {
            'jsonrpc': '2.0',
            'method': f'SportsAPING/v1.0/{method}',
            'params': params,
            'id': str(uuid.uuid4())
        }
        
        url = BETFAIR_IT_ENDPOINTS[endpoint]
        
        for attempt in range(NETWORK_CONFIG['max_retries']):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(NETWORK_CONFIG['connect_timeout'], NETWORK_CONFIG['read_timeout'])
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'error' in result:
                        error_code = result['error'].get('code', 'UNKNOWN')
                        error_message = result['error'].get('message', 'Errore sconosciuto')
                        self.logger.error(f"Errore API: {error_code} - {error_message}")
                        raise RuntimeError(f"Errore API: {error_message}")
                    
                    return result.get('result', {})
                
                elif response.status_code in NETWORK_CONFIG['retry_status_codes']:
                    if attempt < NETWORK_CONFIG['max_retries'] - 1:
                        wait_time = NETWORK_CONFIG['backoff_factor'] * (2 ** attempt)
                        self.logger.warning(f"Errore {response.status_code}, retry in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                
                response.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                if attempt < NETWORK_CONFIG['max_retries'] - 1:
                    wait_time = NETWORK_CONFIG['backoff_factor'] * (2 ** attempt)
                    self.logger.warning(f"Errore rete: {e}, retry in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Richiesta fallita dopo {NETWORK_CONFIG['max_retries']} tentativi: {e}")
                    raise
        
        raise RuntimeError("Richiesta API fallita dopo tutti i tentativi")
    
    def get_tennis_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Recupera eventi tennis disponibili nei prossimi giorni
        """
        params = {
            'filter': {
                'eventTypeIds': [TENNIS_CONFIG['event_type_id']],
                'marketStartTime': {
                    'from': datetime.now().isoformat(),
                    'to': (datetime.now() + timedelta(days=days_ahead)).isoformat()
                }
            }
        }
        
        try:
            result = self._make_api_request('listEvents', params)
            self.logger.info(f"Recuperati {len(result)} eventi tennis")
            return result
        except Exception as e:
            self.logger.error(f"Errore recupero eventi tennis: {e}")
            return []
    
    def get_tennis_markets(self, event_ids: List[str] = None, market_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera mercati tennis per eventi specifici
        """
        if market_types is None:
            market_types = TENNIS_CONFIG['market_types']
            
        params = {
            'filter': {
                'eventTypeIds': [TENNIS_CONFIG['event_type_id']],
                'marketTypeCodes': market_types
            },
            'maxResults': 1000,
            'marketProjection': ['COMPETITION', 'EVENT', 'EVENT_TYPE', 'MARKET_START_TIME', 'RUNNER_DESCRIPTION']
        }
        
        if event_ids:
            params['filter']['eventIds'] = event_ids
            
        try:
            result = self._make_api_request('listMarketCatalogue', params)
            self.logger.info(f"Recuperati {len(result)} mercati tennis")
            return result
        except Exception as e:
            self.logger.error(f"Errore recupero mercati tennis: {e}")
            return []
    
    def get_market_odds(self, market_ids: List[str], price_projection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Recupera quote in tempo reale per mercati specifici
        """
        if price_projection is None:
            price_projection = {
                'priceData': ['EX_BEST_OFFERS', 'EX_ALL_OFFERS'],
                'exBestOffersOverrides': {
                    'bestPricesDepth': 3,
                    'rollupModel': 'STAKE',
                    'rollupLimit': 20
                }
            }
        
        # Controllo limite peso richiesta (max 200 punti)
        weight_per_market = 5  # Peso stimato per mercato con EX_BEST_OFFERS
        if len(market_ids) * weight_per_market > RATE_LIMITS['data_request_weight_limit']:
            self.logger.warning(f"Richiesta troppo pesante, limitando a {RATE_LIMITS['data_request_weight_limit'] // weight_per_market} mercati")
            market_ids = market_ids[:RATE_LIMITS['data_request_weight_limit'] // weight_per_market]
        
        params = {
            'marketIds': market_ids,
            'priceProjection': price_projection
        }
        
        try:
            result = self._make_api_request('listMarketBook', params)
            self.logger.info(f"Recuperate quote per {len(result)} mercati")
            return result
        except Exception as e:
            self.logger.error(f"Errore recupero quote: {e}")
            return []
    
    def get_tennis_odds_realtime(self, competition_filter: List[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera quote tennis in tempo reale con filtri
        """
        # Step 1: Recupera eventi tennis
        events = self.get_tennis_events(days_ahead=3)
        
        if competition_filter:
            events = [e for e in events if any(comp in e.get('event', {}).get('name', '') 
                     for comp in competition_filter)]
        
        if not events:
            return []
        
        # Step 2: Recupera mercati per gli eventi
        event_ids = [e['event']['id'] for e in events]
        markets = self.get_tennis_markets(event_ids, ['MATCH_ODDS'])
        
        if not markets:
            return []
        
        # Step 3: Recupera quote per i mercati
        market_ids = [m['marketId'] for m in markets]
        odds_data = self.get_market_odds(market_ids)
        
        # Step 4: Combina dati per output strutturato
        tennis_odds = []
        for market in markets:
            market_id = market['marketId']
            market_odds = next((o for o in odds_data if o['marketId'] == market_id), None)
            
            if market_odds and market_odds.get('status') == 'OPEN':
                match_info = {
                    'market_id': market_id,
                    'event_name': market['event']['name'],
                    'competition': market['competition']['name'],
                    'market_start_time': market['marketStartTime'],
                    'runners': []
                }
                
                for runner in market_odds.get('runners', []):
                    runner_info = {
                        'selection_id': runner['selectionId'],
                        'runner_name': next((r['runnerName'] for r in market['runners'] 
                                           if r['selectionId'] == runner['selectionId']), 'Unknown'),
                        'status': runner['status'],
                        'back_prices': runner.get('ex', {}).get('availableToBack', []),
                        'lay_prices': runner.get('ex', {}).get('availableToLay', []),
                        'last_price_traded': runner.get('lastPriceTraded')
                    }
                    match_info['runners'].append(runner_info)
                
                tennis_odds.append(match_info)
        
        return tennis_odds
    
    def place_bet(self, market_id: str, selection_id: int, side: str, size: float, price: float) -> Dict[str, Any]:
        """
        Piazza una scommessa (ATTENZIONE: usa fondi reali!)
        
        Args:
            market_id: ID del mercato
            selection_id: ID della selezione
            side: 'B' per back, 'L' per lay
            size: Importo in euro
            price: Quota
        """
        # Validazione regole italiane
        size_cents = int(size * 100)
        
        if side == 'B':  # Back bet
            if size_cents < ITALIAN_BETTING_RULES['min_back_stake_euro_cents']:
                raise ValueError(f"Puntata minima: {ITALIAN_BETTING_RULES['min_back_stake_euro_cents']/100}€")
            if size_cents % ITALIAN_BETTING_RULES['stake_increment_euro_cents'] != 0:
                raise ValueError(f"Puntata deve essere multipla di {ITALIAN_BETTING_RULES['stake_increment_euro_cents']/100}€")
        
        # Controllo vincita massima
        potential_winnings = size * (price - 1) if side == 'B' else size
        if potential_winnings > ITALIAN_BETTING_RULES['max_winnings_per_bet_euros']:
            raise ValueError(f"Vincita potenziale supera il limite di {ITALIAN_BETTING_RULES['max_winnings_per_bet_euros']}€")
        
        params = {
            'marketId': market_id,
            'instructions': [{
                'selectionId': selection_id,
                'handicap': 0,
                'side': side,
                'orderType': 'LIMIT',
                'limitOrder': {
                    'size': size,
                    'price': price,
                    'persistenceType': 'LAPSE'
                }
            }]
        }
        
        try:
            result = self._make_api_request('placeOrders', params)
            self.logger.info(f"Scommessa piazzata: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Errore piazzamento scommessa: {e}")
            raise
    
    def get_account_funds(self) -> Dict[str, Any]:
        """Recupera informazioni sui fondi dell'account"""
        try:
            result = self._make_api_request('getAccountFunds', {}, 'accounts_json_rpc')
            return result
        except Exception as e:
            self.logger.error(f"Errore recupero fondi: {e}")
            return {}
    
    def get_current_orders(self) -> List[Dict[str, Any]]:
        """Recupera ordini correnti"""
        try:
            result = self._make_api_request('listCurrentOrders', {})
            return result.get('currentOrders', [])
        except Exception as e:
            self.logger.error(f"Errore recupero ordini correnti: {e}")
            return []
