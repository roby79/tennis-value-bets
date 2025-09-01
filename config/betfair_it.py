
"""
Configurazione specifica per Betfair Italia (betfair.it)
Endpoint, rate limits e costanti per il mercato italiano
"""

# Endpoint specifici per Betfair Italia
BETFAIR_IT_ENDPOINTS = {
    # Login endpoints per betfair.it
    'login_interactive': 'https://identitysso.betfair.it/api/login',
    'login_cert': 'https://identitysso-cert.betfair.it/api/certlogin',
    'logout': 'https://identitysso.betfair.it/api/logout',
    'keep_alive': 'https://identitysso.betfair.it/api/keepAlive',
    
    # API endpoints (dopo login, si usano gli endpoint UK che filtrano per mercato italiano)
    'betting_json_rpc': 'https://api.betfair.com/exchange/betting/json-rpc/v1',
    'betting_rest': 'https://api.betfair.com/exchange/betting/rest/v1.0/',
    'accounts_json_rpc': 'https://api.betfair.com/exchange/account/json-rpc/v1',
    'accounts_rest': 'https://api.betfair.com/exchange/account/rest/v1.0/',
    'stream_api': 'stream-api.betfair.com:443'
}

# Rate limits specifici per il mercato italiano
RATE_LIMITS = {
    'login_requests_per_minute': 100,
    'data_request_weight_limit': 200,  # Peso massimo per richiesta dati
    'place_orders_instructions_limit': 50,  # Limite ridotto per Italia vs 200 globale
    'connection_idle_timeout': 180,  # 3 minuti prima della chiusura connessione
    'requests_per_second': 5,  # Rate limit generale conservativo
    'burst_requests': 10  # Burst massimo
}

# Regole specifiche per il betting italiano
ITALIAN_BETTING_RULES = {
    'min_back_stake_euro_cents': 200,  # Puntata minima 2 euro
    'stake_increment_euro_cents': 50,  # Incrementi di 50 centesimi
    'min_lay_back_equivalent_euro_cents': 50,  # Minimo per lay corrispondente
    'max_winnings_per_bet_euros': 10000,  # Massimo vincita per scommessa
    'currency': 'EUR',
    'locale': 'it_IT'
}

# Headers standard per le richieste
DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'keep-alive',
    'User-Agent': 'TennisValueBets/1.0 (Italy)'
}

# Configurazione per il tennis
TENNIS_CONFIG = {
    'event_type_id': '2',  # Tennis su Betfair
    'market_types': [
        'MATCH_ODDS',  # 1X2 (vincitore partita)
        'OVER_UNDER_25',  # Over/Under 2.5 set
        'CORRECT_SCORE',  # Risultato esatto
        'SET_BETTING'  # Betting sui set
    ],
    'competition_filters': [
        'ATP',
        'WTA', 
        'ITF',
        'Challenger',
        'Roland Garros',
        'Wimbledon',
        'US Open',
        'Australian Open'
    ]
}

# Configurazione timeout e retry
NETWORK_CONFIG = {
    'connect_timeout': 10,
    'read_timeout': 30,
    'max_retries': 3,
    'backoff_factor': 0.5,
    'retry_status_codes': [429, 500, 502, 503, 504]
}

# Messaggi di errore comuni
ERROR_MESSAGES = {
    'INVALID_USERNAME_OR_PASSWORD': 'Credenziali non valide',
    'SECURITY_RESTRICTED_LOCATION': 'Accesso limitato dalla posizione geografica',
    'TOO_MUCH_DATA': 'Troppi dati richiesti (limite peso: 200)',
    'TOO_MANY_REQUESTS': 'Troppi richieste (rate limit superato)',
    'INVALID_APP_KEY': 'App Key non valida o non attivata',
    'SESSION_EXPIRED': 'Sessione scaduta, necessario nuovo login',
    'INSUFFICIENT_FUNDS': 'Fondi insufficienti per la scommessa',
    'BET_TAKEN_OR_LAPSED': 'Scommessa già accettata o scaduta'
}

# Configurazione logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/betfair_it.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}
