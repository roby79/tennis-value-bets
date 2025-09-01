
"""
Gestione sessione e autenticazione per Betfair Italia
Supporta login interattivo e certificato per betfair.it
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from config.betfair_it import (
    BETFAIR_IT_ENDPOINTS, 
    DEFAULT_HEADERS, 
    RATE_LIMITS,
    NETWORK_CONFIG,
    ERROR_MESSAGES
)

class BetfairItalySession:
    """Gestisce l'autenticazione e la sessione per Betfair Italia"""
    
    def __init__(self, app_key: str, username: str = None, password: str = None):
        self.app_key = app_key
        self.username = username
        self.password = password
        self.session_token = None
        self.session_expires = None
        self.last_request_time = 0
        self.request_count = 0
        self.session = requests.Session()
        
        # Configurazione timeout e retry
        self.session.timeout = (NETWORK_CONFIG['connect_timeout'], NETWORK_CONFIG['read_timeout'])
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _rate_limit_check(self):
        """Controlla e applica rate limiting"""
        current_time = time.time()
        
        # Reset contatore ogni minuto
        if current_time - self.last_request_time > 60:
            self.request_count = 0
            
        # Controlla limite richieste per minuto
        if self.request_count >= RATE_LIMITS['requests_per_second'] * 60:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit raggiunto, attendo {sleep_time:.2f} secondi")
                time.sleep(sleep_time)
                self.request_count = 0
        
        # Rate limiting tra richieste
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / RATE_LIMITS['requests_per_second']
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        self.request_count += 1
    
    def login_interactive(self) -> bool:
        """
        Login interattivo con username/password per betfair.it
        """
        if not self.username or not self.password:
            raise ValueError("Username e password richiesti per login interattivo")
            
        self._rate_limit_check()
        
        headers = DEFAULT_HEADERS.copy()
        headers['X-Application'] = self.app_key
        
        data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = self.session.post(
                BETFAIR_IT_ENDPOINTS['login_interactive'],
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'SUCCESS':
                    self.session_token = result.get('token')
                    # Sessione valida per 8 ore di default
                    self.session_expires = datetime.now() + timedelta(hours=8)
                    self.logger.info("Login interattivo completato con successo")
                    return True
                else:
                    error_code = result.get('error', 'UNKNOWN_ERROR')
                    error_msg = ERROR_MESSAGES.get(error_code, f"Errore sconosciuto: {error_code}")
                    self.logger.error(f"Login fallito: {error_msg}")
                    return False
            else:
                self.logger.error(f"Login fallito con status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore di rete durante login: {e}")
            return False
    
    def login_certificate(self, cert_path: str, key_path: str) -> bool:
        """
        Login non-interattivo con certificato SSL per betfair.it
        Raccomandato per applicazioni automatizzate
        """
        self._rate_limit_check()
        
        headers = DEFAULT_HEADERS.copy()
        headers['X-Application'] = self.app_key
        
        try:
            response = self.session.post(
                BETFAIR_IT_ENDPOINTS['login_cert'],
                headers=headers,
                cert=(cert_path, key_path)
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'SUCCESS':
                    self.session_token = result.get('token')
                    self.session_expires = datetime.now() + timedelta(hours=8)
                    self.logger.info("Login certificato completato con successo")
                    return True
                else:
                    error_code = result.get('error', 'UNKNOWN_ERROR')
                    error_msg = ERROR_MESSAGES.get(error_code, f"Errore sconosciuto: {error_code}")
                    self.logger.error(f"Login certificato fallito: {error_msg}")
                    return False
            else:
                self.logger.error(f"Login certificato fallito con status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore di rete durante login certificato: {e}")
            return False
    
    def keep_alive(self) -> bool:
        """Mantiene attiva la sessione"""
        if not self.is_logged_in():
            return False
            
        self._rate_limit_check()
        
        headers = DEFAULT_HEADERS.copy()
        headers['X-Application'] = self.app_key
        headers['X-Authentication'] = self.session_token
        
        try:
            response = self.session.post(
                BETFAIR_IT_ENDPOINTS['keep_alive'],
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'SUCCESS':
                    # Estende la sessione
                    self.session_expires = datetime.now() + timedelta(hours=8)
                    self.logger.debug("Keep alive completato con successo")
                    return True
                    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore durante keep alive: {e}")
            
        return False
    
    def logout(self) -> bool:
        """Termina la sessione"""
        if not self.session_token:
            return True
            
        headers = DEFAULT_HEADERS.copy()
        headers['X-Application'] = self.app_key
        headers['X-Authentication'] = self.session_token
        
        try:
            response = self.session.post(
                BETFAIR_IT_ENDPOINTS['logout'],
                headers=headers
            )
            
            self.session_token = None
            self.session_expires = None
            self.logger.info("Logout completato")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore durante logout: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """Verifica se la sessione è attiva e valida"""
        if not self.session_token:
            return False
            
        if self.session_expires and datetime.now() >= self.session_expires:
            self.logger.warning("Sessione scaduta")
            self.session_token = None
            self.session_expires = None
            return False
            
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Restituisce gli headers per le richieste autenticate"""
        if not self.is_logged_in():
            raise RuntimeError("Sessione non attiva. Effettuare login prima.")
            
        headers = DEFAULT_HEADERS.copy()
        headers['X-Application'] = self.app_key
        headers['X-Authentication'] = self.session_token
        
        return headers
    
    def auto_login(self, cert_path: str = None, key_path: str = None) -> bool:
        """
        Login automatico con fallback
        Prova prima certificato (se disponibile), poi interattivo
        """
        if cert_path and key_path:
            if self.login_certificate(cert_path, key_path):
                return True
                
        if self.username and self.password:
            return self.login_interactive()
            
        raise ValueError("Nessun metodo di login disponibile")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
