
# 🎾 Tennis Value Bets - Integrazione Betfair Italia

Dashboard avanzata per l'analisi di value bets nel tennis con integrazione completa per **Betfair Italia** (betfair.it).

## 🚀 Caratteristiche Principali

- **🇮🇹 Integrazione Betfair Italia**: Configurazione specifica per betfair.it
- **📊 Dati Real-time**: Quote live dai mercati tennis italiani
- **🎯 Value Bet Detection**: Algoritmi per identificare opportunità di valore
- **💰 Piazzamento Scommesse**: Interface sicura per bet reali (opzionale)
- **📈 Analytics**: Dashboard completa con grafici e statistiche
- **🔒 Sicurezza**: Rate limiting, gestione errori, validazioni

## 🛠️ Installazione Rapida

```bash
# Clone repository
git clone <repository-url>
cd tennis-value-bets

# Installa dipendenze
pip install -r requirements.txt

# Configura Betfair (copia e modifica)
cp .env.betfair .env
# Modifica .env con le tue credenziali Betfair

# Avvia applicazione
streamlit run app.py
```

## ⚙️ Configurazione Betfair Italia

### 1. Prerequisiti

- Account registrato su [betfair.it](https://betfair.it)
- App Key dal [Developer Portal](https://developer.betfair.com/)
- Credenziali o certificato SSL per autenticazione

### 2. File `.env`

```bash
BETFAIR_APP_KEY=your_app_key_here
BETFAIR_USERNAME=your_username
BETFAIR_PASSWORD=your_password
DEMO_MODE=false  # true per dati simulati
```

### 3. Modalità Disponibili

- **🔧 DEMO**: Dati simulati, nessuna connessione reale
- **🟢 LIVE**: Connessione reale a betfair.it con dati live

## 📋 Funzionalità

### 🎾 Analisi Tennis

- **Eventi Live**: Partite tennis dai principali tornei
- **Quote Real-time**: Back/Lay prices da Betfair Italia
- **Mercati Supportati**: Match Odds, Over/Under, Set Betting
- **Filtri Avanzati**: Per torneo, superficie, ranking giocatori

### 💡 Value Betting

- **Calcolo Probabilità**: Basato su quote implicite Betfair
- **Edge Detection**: Identificazione automatica value bets
- **Soglie Personalizzabili**: Filtri per edge minimo
- **Export CSV**: Download opportunità identificate

### 📊 Dashboard

- **Grafici Interattivi**: Confronto quote vs fair value
- **Statistiche Giocatori**: Elo rating, ranking, performance
- **Monitoraggio Real-time**: Aggiornamenti automatici
- **Stato Connessione**: Monitoring Betfair API

### 🎯 Scommesse (Opzionale)

- **Interface Sicura**: Validazione regole italiane
- **Conferme Multiple**: Protezione contro errori
- **Gestione Bankroll**: Controlli automatici
- **Log Completi**: Tracciamento tutte le operazioni

## 🔧 Architettura Tecnica

### Struttura Progetto

```
tennis-value-bets/
├── app.py                 # Streamlit app principale
├── config/
│   ├── betfair_it.py     # Configurazioni Betfair Italia
│   └── __init__.py
├── services/
│   ├── betfair_session.py # Gestione autenticazione
│   ├── betfair_client.py  # Client API Betfair
│   └── __init__.py
├── docs/
│   └── Betfair_IT.md     # Documentazione dettagliata
├── requirements.txt       # Dipendenze Python
└── .env.betfair          # Template configurazione
```

### Tecnologie

- **Frontend**: Streamlit + Plotly
- **Backend**: Python + Requests
- **API**: Betfair Exchange API
- **Database**: SQLite (per cache e analytics)
- **Deployment**: Docker ready

## 🇮🇹 Specifiche Mercato Italiano

### Endpoint Betfair Italia

- **Login**: `identitysso.betfair.it`
- **API**: `api.betfair.com` (filtrato per Italia)
- **Rate Limits**: 5 req/sec, 100 login/min

### Regole Scommesse

- **Puntata minima**: €2.00
- **Incrementi**: €0.50
- **Vincita massima**: €10,000
- **Valuta**: EUR
- **Ordini**: Max 50 istruzioni/richiesta

## 📖 Documentazione

- **[Guida Betfair Italia](docs/Betfair_IT.md)**: Setup completo e troubleshooting
- **[API Reference](config/betfair_it.py)**: Configurazioni e endpoint
- **[Esempi Codice](services/)**: Implementazioni client e sessioni

## 🔒 Sicurezza e Compliance

### Best Practices

- ✅ Rate limiting automatico
- ✅ Gestione sicura credenziali
- ✅ Validazione input utente
- ✅ Log audit completi
- ✅ Modalità demo per test

### Compliance Italia

- ✅ Endpoint specifici betfair.it
- ✅ Regole mercato italiano
- ✅ Valuta EUR
- ✅ Limitazioni ADM

## 🆘 Supporto

### Problemi Comuni

**Connessione fallita**:
```bash
# Verifica configurazione
cat .env | grep BETFAIR

# Test modalità demo
DEMO_MODE=true streamlit run app.py
```

**Rate limit superato**:
- L'app gestisce automaticamente con pause
- Ridurre frequenza aggiornamenti se necessario

### Risorse

- 📚 [Documentazione Betfair](https://docs.developer.betfair.com/)
- 🔧 [Developer Portal](https://developer.betfair.com/)
- 💬 [Issues GitHub](../../issues)

## 📈 Roadmap

### v1.1 (Prossima Release)
- [ ] Streaming real-time quote
- [ ] Algoritmi ML per value detection
- [ ] Gestione automatica bankroll
- [ ] Mobile responsive design

### v1.2 (Futuro)
- [ ] Multi-bookmaker support
- [ ] Advanced analytics
- [ ] API REST per integrazioni
- [ ] Backtesting storico

## 🤝 Contributi

Contributi benvenuti! Aree di interesse:

- **Algoritmi**: Miglioramenti value betting
- **UI/UX**: Enhancements dashboard
- **Testing**: Unit tests e integration tests
- **Documentazione**: Guide e tutorials

## ⚖️ Disclaimer

**⚠️ IMPORTANTE**: 
- Questo software è per scopi educativi e di ricerca
- Il gambling può creare dipendenza
- Scommettere solo con fondi che ci si può permettere di perdere
- Verificare la legalità nel proprio paese
- Gli autori non sono responsabili per perdite finanziarie

## 📄 Licenza

MIT License - Vedi [LICENSE](LICENSE) per dettagli.

---

**Sviluppato con ❤️ per la comunità tennis italiana**

🎾 Buona fortuna con i tuoi value bets! 🍀
