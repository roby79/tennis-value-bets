import streamlit as st

# Test base
st.title("🎾 Tennis Value Bets - Test")
st.write("Se vedi questo messaggio, Streamlit funziona!")

# Test import base
try:
    import numpy as np
    import pandas as pd
    import plotly.express as px
    from datetime import datetime
    import os
    import logging
    from dotenv import load_dotenv
    st.success("✅ Import base OK")
except Exception as e:
    st.error(f"❌ Errore import base: {e}")

# Test import custom modules
try:
    from db import DatabaseManager
    st.success("✅ Import DatabaseManager OK")
except Exception as e:
    st.error(f"❌ Errore import DatabaseManager: {e}")

try:
    from services.betfair_session import BetfairItalySession
    from services.betfair_client import BetfairItalyClient
    st.success("✅ Import Betfair modules OK")
except Exception as e:
    st.error(f"❌ Errore import Betfair modules: {e}")

try:
    from config.betfair_it import TENNIS_CONFIG, ITALIAN_BETTING_RULES
    st.success("✅ Import config OK")
except Exception as e:
    st.error(f"❌ Errore import config: {e}")

# Test caricamento env
try:
    load_dotenv()
    load_dotenv('.env.betfair')
    st.success("✅ Caricamento .env OK")
except Exception as e:
    st.error(f"❌ Errore caricamento .env: {e}")

# Test inizializzazione DB
try:
    db = DatabaseManager()
    st.success("✅ Inizializzazione DatabaseManager OK")
except Exception as e:
    st.error(f"❌ Errore inizializzazione DatabaseManager: {e}")

st.write("Test completato!")
