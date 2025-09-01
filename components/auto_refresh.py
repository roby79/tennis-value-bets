"""
Componente per auto-refresh dell'applicazione
"""
import streamlit as st
import time
from datetime import datetime, timedelta

def auto_refresh_component(refresh_interval_minutes=5):
    """
    Componente per auto-refresh automatico della pagina
    
    Args:
        refresh_interval_minutes: Intervallo di refresh in minuti
    """
    
    # JavaScript per auto-refresh
    refresh_js = f"""
    <script>
        // Auto-refresh ogni {refresh_interval_minutes} minuti
        setTimeout(function() {{
            window.location.reload();
        }}, {refresh_interval_minutes * 60 * 1000});
        
        // Mostra countdown
        let timeLeft = {refresh_interval_minutes * 60};
        const countdownElement = document.getElementById('refresh-countdown');
        
        const countdown = setInterval(function() {{
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            
            if (countdownElement) {{
                countdownElement.innerHTML = `Prossimo aggiornamento: ${{minutes}}:${{seconds.toString().padStart(2, '0')}}`;
            }}
            
            timeLeft--;
            
            if (timeLeft < 0) {{
                clearInterval(countdown);
            }}
        }}, 1000);
    </script>
    
    <div id="refresh-countdown" style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(45deg, #2d5aa0, #1f4e79);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        border: 2px solid rgba(255,255,255,0.2);
    ">
        🔄 Caricamento automatico attivo
    </div>
    """
    
    st.markdown(refresh_js, unsafe_allow_html=True)

def get_last_update_info():
    """Restituisce informazioni sull'ultimo aggiornamento"""
    now = datetime.now()
    
    # Salva timestamp in session state
    if 'last_update' not in st.session_state:
        st.session_state.last_update = now
    
    last_update = st.session_state.last_update
    time_diff = now - last_update
    
    if time_diff.total_seconds() < 60:
        time_str = f"{int(time_diff.total_seconds())} secondi fa"
    elif time_diff.total_seconds() < 3600:
        time_str = f"{int(time_diff.total_seconds() / 60)} minuti fa"
    else:
        time_str = f"{int(time_diff.total_seconds() / 3600)} ore fa"
    
    return {
        'last_update': last_update,
        'time_ago': time_str,
        'timestamp': now.strftime("%H:%M:%S")
    }

def update_timestamp():
    """Aggiorna il timestamp dell'ultimo aggiornamento"""
    st.session_state.last_update = datetime.now()

def show_refresh_status():
    """Mostra lo status del refresh nella sidebar"""
    update_info = get_last_update_info()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Status Aggiornamento")
    st.sidebar.info(f"⏰ Ultimo aggiornamento: {update_info['time_ago']}")
    st.sidebar.caption(f"Timestamp: {update_info['timestamp']}")
    
    # Pulsante refresh manuale
    if st.sidebar.button("🔄 Aggiorna Ora", type="primary", use_container_width=True):
        st.cache_data.clear()
        update_timestamp()
        st.rerun()
