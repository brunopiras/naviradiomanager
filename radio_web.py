####
import streamlit as st
import requests
import hashlib
import os
import time
from lang import TRANSLATIONS



# --- STUPISCIMI: CSS PER BANDIERA ITALIANA NELLA SIDEBAR ---
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
        
        /* Assicura che i widget (input, select) siano ben visibili */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] > input {
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #1a1a1a !important;
            border-radius: 4px;
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

VERSION = f"V6.1.8-{LANG_CODE}"
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
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": "1.16.1", "c": "web-manager", "f": "json"}
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
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": "1.16.1", "c": "web-manager", "f": "json",
              "name": station['name'], "streamUrl": station['url_resolved'], "homepageUrl": station.get('homepage', '')}
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        return r.json()
    except:
        return {"subsonic-response": {"status": "failed"}}

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
                
                # Aggiungiamo un check se è duplicata nel titolo
                titolo = f"{flag} **{s['name']}**" + (" ✅" if is_duplicate else "")
                
                with st.expander(f"{titolo} | ⭐ {s.get('votes', 0)}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"Bitrate: {s.get('bitrate', 0)} | Codec: {s.get('codec', 'N/D')}")
                    with col2:
                        hp = s.get('homepage', '').strip()
                        if hp:
                            st.image(f"https://www.google.com/s2/favicons?sz=64&domain={hp}", width=24)
                    
                    st.divider()
                    st.code(stream_url, language=None)
                    
                    if is_duplicate:
                        st.warning("⚠️ " + ( "Radio già presente in NAVIDROME" if LANG_CODE=="IT" else "Radio already exists in NAVIDROME" ))
                    else:
                        if st.button(T["add_btn"], key=f"add_{s['stationuuid']}", use_container_width=True):
                            res = add_to_navidrome(s)
                            if res.get('subsonic-response', {}).get('status') == 'ok': 
                                st.success(T["success"])
                                st.rerun() # Forza ricarica per aggiornare il check ✅
                            else: 
                                st.error("Error")
            
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
col1, col2, col3= st.columns([1, 1, 1])
with col1:
    st.markdown(f":violet-badge[:material/star: {VERSION}]")
with col2:
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-Repo-orange?logo=github)](https://github.com/brunopiras/naviradiomanager)")
with col3:
    st.markdown("[![Reddit](https://img.shields.io/badge/Reddit-Discuss-orange?logo=reddit&logoColor=white)](https://www.reddit.com/r/navidrome/comments/1rjntju/search_and_add_stream_radio_from_webapp/)")
