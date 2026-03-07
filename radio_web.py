####
import streamlit as st
import requests
import hashlib
import os
import time
from lang import TRANSLATIONS

st.markdown("""
    <style>
        /* Seleziona il contenitore principale della sidebar */
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(
                to bottom,
                #008c45 0%, #008c45 33.33%,    /* VERDE UFFICIALE 1/3 */
                #f4f5f0 33.33%, #f4f5f0 66.66%, /* BIANCO UFFICIALE 1/3 */
                #cd212a 66.66%, #cd212a 100%   /* ROSSO UFFICIALE 1/3 */
            ) !important;
            background-attachment: fixed; /* Mantiene le strisce ferme allo scorrimento */
        }

        /* --- OTTIMIZZAZIONE TESTO SIDEBAR --- */
        /* Rende il testo nella sidebar scuro e leggibile su verde/bianco */
        [data-testid="stSidebar"] .stMarkdown, 
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stTextInput label {
            color: #1a1a1a !important; 
            font-weight: 500;
        }
        
        * Assicura che i widget (input, select) siano ben visibili */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] > input {
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #1a1a1a !important;
            border-radius: 4px;
        }

        /* Rende le icone delle radio smussate e aggiunge un'ombra leggera */
        img {
            border-radius: 8px !important; 
            box-shadow: 0px 4px 8px rgba(0,0,0,0.3); 
            transition: transform 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1); /* Un sottile bordo per farle staccare dallo sfondo petrolio */
        }

        /* Effetto zoom al passaggio del mouse */
        img:hover {
            transform: scale(1.2);
            box-shadow: 0px 6px 12px rgba(0,0,0,0.5);
        }
        /* Mini Player Trasparente */
        audio {
            width: 100%;
            height: 40px;
            opacity: 0.5; 
            filter: invert(100%) hue-rotate(180deg) brightness(1.5); 
            transition: opacity 0.3s;
        }
        audio:hover {
            opacity: 1;
        }
        .top-voted {
            background-color: #FFD700;
            color: black;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 12px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
""", unsafe_allow_html=True)
# --- CONFIGURAZIONE (ENV) ---
NAVIDROME_URL = os.getenv("NAVIDROME_URL", "")
USERNAME = os.getenv("NAVIDROME_USER", "")
PASSWORD = os.getenv("NAVIDROME_PASS", "")
SALT = os.getenv("NAVIDROME_SALT", "")
TOKEN = hashlib.md5((PASSWORD + SALT).encode("utf-8")).hexdigest()

LANG_CODE = os.getenv("APP_LANG", "IT").upper()
T = TRANSLATIONS.get(LANG_CODE, TRANSLATIONS["IT"])

VERSION = f"V6.1.9.RC11-{LANG_CODE}"
FLAGS = {"IT": "🇮🇹", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "DE": "🇩🇪", "ES": "🇪🇸", "CH": "🇨🇭"}

# --- FUNZIONI DI SUPPORTO ---
@st.cache_data(ttl=86400)
def get_all_countries():
    """Scarica la lista ufficiale delle nazioni dai mirror."""
    for mirror in ["at1", "de1", "nl1", "all"]:
        try:
            url = f"https://{mirror}.api.radio-browser.info/json/countries"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return sorted([c['name'] for c in r.json() if c['name']])
        except:
            continue
    return ["Italy", "America", "France", "Germany", "United Kingdom"]

def get_existing_radios():
    """Recupera gli URL delle radio già salvate su Navidrome per evitare duplicati."""
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": VERSION, "c": "NaviRadioManager", "f": "json"}
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        if isinstance(stations, dict): stations = [stations] # Gestione singola stazione
        return [s['streamUrl'] for s in stations if 'streamUrl' in s]
    except:
        return []

def sync_to_sel():
    st.session_state.search_country_text = ""

def sync_to_text():
    st.session_state.search_country_sel = ""

# --- STATO SESSIONE ---
if 'stage' not in st.session_state: st.session_state.stage = 0 
if 'results' not in st.session_state: st.session_state.results = []
if 'offset' not in st.session_state: st.session_state.offset = 0

# --- FUNZIONI CORE ---
@st.cache_data(ttl=600)
def search_radio(name="", country="", offset=0):
    url = "https://all.api.radio-browser.info/json/stations/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"name": name, "country": country, "order": "votes", "reverse": "true", "limit": 20, "offset": offset}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        return r.json()
    except:
        return []

def add_to_navidrome(station):
    endpoint = f"{NAVIDROME_URL}/rest/createInternetRadioStation"
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": VERSION, "c": "NaviRadioManager", "f": "json",
              "name": station['name'], "streamUrl": station['url_resolved'], "homepageUrl": station.get('homepage', '')}
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        return r.json()
    except:
        return {"subsonic-response": {"status": "failed"}}
def vote_for_station(uuid):
    try:
        # Usiamo uno dei mirror della API
        url = f"https://all.api.radio-browser.info/json/vote/{uuid}"
        response = requests.get(url)
        return response.ok
    except:
        return False
def get_total_radios():
    """Recupera il numero totale di stazioni radio configurate su Navidrome"""
    # Usiamo le variabili globali già definite all'inizio del file
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        'u': USERNAME,
        't': TOKEN,
        's': SALT,
        'v': VERSION,
        'c': 'NaviRadioManager',
        'f': 'json'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        # Navidrome restituisce la lista dentro questo percorso JSON
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
        # Gestione caso singola stazione (Subsonic a volte restituisce un dict invece di una lista)
        if isinstance(stations, dict):
            return 1
        return len(stations)
    except Exception as e:
        # Se c'è un errore di connessione, restituisce "?" invece di 0 per non confondere
        return "?"
def trigger_search():
    st.session_state.stage = 1
    st.session_state.offset = 0
    name = st.session_state.get('search_name', "").strip()
    t = st.session_state.get('search_country_text', "").strip()
    s = st.session_state.get('search_country_sel', "")
    country = t if t else s
    st.session_state.final_country = country.strip()
    st.session_state.results = search_radio(name, st.session_state.final_country, 0)

def reset_home():
    # 1. Reset degli stati logici
    st.session_state.stage = 0
    st.session_state.results = []
    st.session_state.offset = 0
    st.session_state["search_name"] = ""
    st.session_state["search_country_text"] = ""
    st.session_state["search_country_sel"] = ""

def rerun():
    st.write("")

# --- INTERFACCIA ---
st.set_page_config(page_title="NaviRadioManager", page_icon="📻", layout="centered")
st.markdown("<style>[data-testid='stVerticalBlock'] > div {transition: none !important; opacity: 1 !important;}</style>", unsafe_allow_html=True)

st.title(T["title"])



lista_ufficiale = [""] + get_all_countries()

with st.sidebar:
    st.header(T["search_header"])
    modi = ["Nome", "Nazione"] if LANG_CODE == "IT" else ["Name", "Country"]
    mode = st.selectbox(T["mode"], modi)
    
    st.text_input(T["name_label"], key="search_name")
    
    if mode in ["Nazione", "Country"]:
        st.write("---")
        st.selectbox(T["country_sel"], options=lista_ufficiale, key="search_country_sel", on_change=sync_to_sel)
        st.text_input(T["country_text"], key="search_country_text", placeholder="es: USA, Italy...", on_change=sync_to_text)

    st.button(T["btn_search"], on_click=trigger_search, use_container_width=True, type="primary")
    
    if st.session_state.stage == 1:
        st.button(T["btn_home"], on_click=reset_home, use_container_width=True)

# --- AREA PRINCIPALE ---
main_area = st.empty()
with main_area.container():
    if st.session_state.stage == 0:
        st.info(T["welcome"])
    elif st.session_state.stage == 1:
        # Recuperiamo la lista esistente per il check duplicati
        existing_urls = get_existing_radios()
        
        if st.session_state.results:
            st.button(f"⬅️ {T['btn_home']}", on_click=reset_home, use_container_width=True)
            st.write(f"### {T['results']}")
            
            for s in st.session_state.results:
                stream_url = s['url_resolved']
                is_duplicate = stream_url in existing_urls
                flag = FLAGS.get(s.get('countrycode', '').upper(), "🌐")
                # --- LOGICA TITOLO ---
                votes = s.get('votes', 0)

                # Se è una TOP radio, mettiamo il badge arancione, altrimenti solo il numero di stelle
                if votes > 1000:
                    top_tag = f" :orange[🔥 TOP {votes}]"
                else:
                    top_tag = f" ⭐ {votes}"

                is_dup_tag = " ✅" if is_duplicate else ""
                # Aggiungiamo un check se è duplicata nel titolo
                titolo = f"{flag} **{s['name']}**{top_tag}{is_dup_tag}"             
                with st.expander(f"{titolo}"):
                    if votes > 1000:
                        st.markdown(f"<span class='top-voted'>🔥 TOP {votes} VOTES</span>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        # Recuperiamo il bitrate
                        bitrate = s.get('bitrate', 0)
                        codec = s.get('codec', 'N/D')
                        
                        # Determiniamo colore e etichetta in base alla qualità
                        if bitrate >= 192:
                            q_color = "green"
                            q_label = "High Quality" if LANG_CODE == "EN" else "Alta Qualità"
                        elif bitrate >= 128:
                            q_color = "blue"
                            q_label = "Standard Quality" if LANG_CODE == "EN" else "Qualità Standard"
                        else:
                            q_color = "orange"
                            q_label = "Low Quality" if LANG_CODE == "EN" else "Bassa Qualità"

                        st.write(f"Bitrate: {bitrate} | Codec: {codec}")
                        
                        # Inseriamo la barra di progresso (max 320 kbps)
                        # Usiamo la sintassi colorata per l'etichetta
                        st.markdown(f":{q_color}[{q_label}]")
                        st.progress(min(bitrate / 320, 1.0))
                        
                    with col2:
                        hp = s.get('homepage', '').strip()
                        if hp:
                            st.image(f"https://www.google.com/s2/favicons?sz=64&domain={hp}", width=24)
                    st.divider()
                    ###TEST MINI PLAYER 
                    st.write("🎧 **Quick Preview:**")
                    st.audio(stream_url, format="audio/mp3")
                    st.code(stream_url, language=None)
                    # --- AZIONI (Voto e Aggiunta) ---
                    st.divider()
                    
                    # CSS per forzare l'altezza del bottone uguale a quella dell'info box
                    st.markdown("""
                        <style>
                            div.stButton > button {
                                height: 52px !important;
                                margin-top: 0px !important;
                            }
                        </style>
                    """, unsafe_allow_html=True)

                    col_v, col_a = st.columns([1, 1])
                    
                    with col_v:
                        # Testo del bottone dinamico (es: "👍 Vota" o "👍 Vote")
                        v_label = "👍 " + ("Vota Radio" if LANG_CODE == "IT" else "Vote Radio")
                        
                        if st.button(v_label, key=f"vote_{s['stationuuid']}", use_container_width=True):
                            if vote_for_station(s['stationuuid']):
                                # Messaggio toast in doppia lingua
                                msg = "Voto inviato! Grazie! 🎉" if LANG_CODE == "IT" else "Vote sent! Thanks! 🎉"
                                st.toast(msg)
                            else:
                                # Errore in doppia lingua
                                err = "Errore nel voto" if LANG_CODE == "IT" else "Voting error"
                                st.error(err)

                    with col_a:
                        if is_duplicate:
                            # Il box info ha un'altezza di circa 52px
                            st.info("✅ " + ("In Libreria" if LANG_CODE=="IT" else "In Library"))
                        else:
                            # Tasto Aggiungi (alto come il box info)
                            if st.button(T["add_btn"], key=f"add_{s['stationuuid']}", use_container_width=True, type="primary"):
                                res = add_to_navidrome(s)
                                if res.get('subsonic-response', {}).get('status') == 'ok': 
                                    st.success(T["success"])
                                    time.sleep(1)
                                    st.rerun() 
                                else: 
                                    st.error("Error adding station")

                    # Avviso extra rimosso o spostato per pulizia
                    if is_duplicate:
                        st.caption("⚠️ " + ( "Radio già presente in NAVIDROME" if LANG_CODE=="IT" else "Radio already exists in NAVIDROME" ))

            
            if st.button("More ➡️", use_container_width=True):
                st.session_state.offset += 20
                st.session_state.results = search_radio(st.session_state.search_name, st.session_state.final_country, st.session_state.offset)
                st.rerun()
        else:
            st.warning(T["no_results"])
            st.button(T["btn_home"], on_click=reset_home)
st.divider()
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f":gray-badge[:material/check: Navidrome URL: {NAVIDROME_URL} ]")
with col2:
    st.markdown(f":gray-badge[:material/check: User: {USERNAME} ]")
    
st.divider()

col1, col2, col3, col4 = st.columns([1.2, 1.2, 0.8, 0.8])

# Badge Versione (Stile GitHub/Reddit)
with col1:
    st.markdown(f"""
        <div style="display: flex; align-items: center; background-color: #555; border-radius: 4px; overflow: hidden; width: fit-content; font-family: sans-serif; font-size: 12px; font-weight: bold;">
            <span style="background-color: #8a2be2; color: white; padding: 4px 8px; display: flex; align-items: center;">⭐ Version</span>
            <span style="background-color: #2e2e2e; color: #fff; padding: 4px 8px;">{VERSION}</span>
        </div>
    """, unsafe_allow_html=True)

# Badge Stazioni Totali
with col2:
    total = get_total_radios()
    st.markdown(f"""
        <div style="display: flex; align-items: center; background-color: #555; border-radius: 4px; overflow: hidden; width: fit-content; font-family: sans-serif; font-size: 12px; font-weight: bold;">
            <span style="background-color: #007ec6; color: white; padding: 4px 8px; display: flex; align-items: center;">📻 {T['total_radios']}</span>
            <span style="background-color: #2e2e2e; color: #fff; padding: 4px 8px;">{total}</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-Repo-orange?logo=github)](https://github.com/brunopiras/naviradiomanager)")

with col4:
    st.markdown("[![Reddit](https://img.shields.io/badge/Reddit-Discuss-orange?logo=reddit&logoColor=white)](https://www.reddit.com/r/navidrome/comments/1rmklet/i_built_a_webgui_to_manage_navidrome_radio/)")
time.sleep(.1)