
# Integrazione Betfair Italia - Guida Completa

## 🇮🇹 Panoramica

Questa guida spiega come configurare e utilizzare l'integrazione con Betfair Italia (betfair.it) per il progetto Tennis Value Bets. L'integrazione è specificamente configurata per il mercato italiano con tutti gli endpoint, regole e limitazioni appropriate.

## 📋 Prerequisiti

### 1. Account Betfair Italia
- Registrazione obbligatoria su [betfair.it](https://register.betfair.it/account/registration)
- Account verificato e attivo
- Fondi disponibili per le scommesse (se si intende piazzare bet)

### 2. App Key Betfair
- Accesso al [Developer Portal](https://developer.betfair.com/)
- Creazione di un'applicazione con App Key
- App Key attivata (€299 per la versione live)

### 3. Metodo di Autenticazione
Scegliere uno dei due metodi:

**Opzione A: Login Interattivo**
- Username e password dell'account betfair.it
- Più semplice per test e sviluppo

**Opzione B: Certificato SSL (Raccomandato)**
- Certificato SSL client per login non-interattivo
- Ideale per applicazioni automatizzate
- Maggiore sicurezza

## ⚙️ Configurazione

### 1. File di Configurazione

Creare un file `.env` nella root del progetto:

```bash
# App Key Betfair (obbligatorio)
BETFAIR_APP_KEY=your_app_key_here

# Credenziali per login interattivo
BETFAIR_USERNAME=your_username_here
BETFAIR_PASSWORD=your_password_here

# Certificati SSL per login non-interattivo (raccomandato)
BETFAIR_CERT_PATH=/path/to/your/certificate.crt
BETFAIR_KEY_PATH=/path/to/your/private.key

# Modalità (true per demo, false per dati reali)
DEMO_MODE=false

# Logging
LOG_LEVEL=INFO
```

### 2. Installazione Dipendenze

```bash
pip install -r requirements.txt
```

Le dipendenze includono:
- `betfairlightweight>=2.18.0` - Client Betfair ufficiale
- `requests>=2.31.0` - HTTP requests
- `python-dotenv>=1.0.0` - Gestione variabili ambiente

## 🔧 Endpoint e Configurazioni

### Endpoint Specifici per betfair.it

```python
# Login endpoints
LOGIN_INTERACTIVE = 'https://identitysso.betfair.it/api/login'
LOGIN_CERT = 'https://identitysso-cert.betfair.it/api/certlogin'

# API endpoints (dopo login, filtrati per mercato italiano)
BETTING_API = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
ACCOUNTS_API = 'https://api.betfair.com/exchange/account/json-rpc/v1'
```

### Rate Limits Specifici

- **Login**: 100 richieste/minuto
- **API Generali**: 5 richieste/secondo
- **Dati**: Peso massimo 200 punti per richiesta
- **Ordini**: Massimo 50 istruzioni per richiesta (vs 200 globale)

## 🎾 Regole Mercato Italiano

### Limitazioni Scommesse

- **Puntata minima**: €2.00 (200 centesimi)
- **Incrementi**: €0.50 (50 centesimi)
- **Vincita massima**: €10,000 per scommessa
- **Valuta**: EUR
- **Lay minimo**: Equivalente back di almeno €0.50

### Mercati Tennis Supportati

- `MATCH_ODDS` - Vincitore partita (1X2)
- `OVER_UNDER_25` - Over/Under 2.5 set
- `CORRECT_SCORE` - Risultato esatto
- `SET_BETTING` - Scommesse sui set

## 🚀 Utilizzo

### 1. Avvio Applicazione

```bash
streamlit run app.py
```

### 2. Modalità Demo vs Reale

**Modalità Demo** (`DEMO_MODE=true`):
- Utilizza dati simulati
- Nessuna connessione a Betfair
- Sicura per test e sviluppo

**Modalità Reale** (`DEMO_MODE=false`):
- Connessione reale a betfair.it
- Dati live dai mercati
- Possibilità di piazzare scommesse reali

### 3. Funzionalità Principali

#### Recupero Dati Tennis
```python
# Automatico nell'app Streamlit
tennis_odds = client.get_tennis_odds_realtime()
```

#### Analisi Value Bets
- Calcolo automatico delle probabilità implicite
- Confronto con quote Betfair
- Identificazione opportunità di valore

#### Piazzamento Scommesse (Opzionale)
- Interface sicura per scommesse reali
- Validazione regole italiane
- Conferme multiple per sicurezza

## 🔒 Sicurezza

### Best Practices

1. **Non condividere mai** App Key o credenziali
2. **Utilizzare certificati SSL** per produzione
3. **Testare sempre** in modalità demo prima
4. **Monitorare** rate limits e saldo account
5. **Backup** delle configurazioni

### Gestione Errori

L'applicazione gestisce automaticamente:
- Scadenza sessioni (re-login automatico)
- Rate limiting (pause automatiche)
- Errori di rete (retry con backoff)
- Validazione scommesse (regole italiane)

## 📊 Monitoraggio

### Log Files

I log sono salvati in `logs/betfair_it.log` con informazioni su:
- Connessioni e login
- Richieste API e rate limiting
- Errori e retry
- Scommesse piazzate

### Metriche Dashboard

L'app Streamlit mostra:
- Stato connessione Betfair
- Saldo account disponibile
- Numero partite caricate
- Value bets identificati

## 🆘 Troubleshooting

### Problemi Comuni

**Errore: "SECURITY_RESTRICTED_LOCATION"**
- Soluzione: Verificare IP italiano o utilizzare VPN

**Errore: "INVALID_APP_KEY"**
- Soluzione: Verificare App Key e attivazione

**Errore: "SESSION_EXPIRED"**
- Soluzione: Automatico (re-login), verificare credenziali

**Errore: "TOO_MANY_REQUESTS"**
- Soluzione: Automatico (rate limiting), ridurre frequenza richieste

### Supporto

Per problemi specifici:
1. Controllare i log in `logs/betfair_it.log`
2. Verificare configurazione `.env`
3. Testare in modalità demo
4. Consultare [documentazione Betfair](https://docs.developer.betfair.com/)

## 📈 Sviluppi Futuri

### Funzionalità Pianificate

- [ ] Streaming real-time delle quote
- [ ] Algoritmi ML per value betting
- [ ] Gestione automatica del bankroll
- [ ] Integrazione con altri bookmaker italiani
- [ ] Dashboard analytics avanzate

### Contributi

Il progetto è open source. Contributi benvenuti per:
- Miglioramenti algoritmi value betting
- Nuovi mercati tennis
- Ottimizzazioni performance
- Documentazione e test

---

**⚠️ Disclaimer**: Questo software è per scopi educativi. Il gambling può creare dipendenza. Scommettere responsabilmente e solo con fondi che ci si può permettere di perdere.
