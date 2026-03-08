####
import streamlit as st
import requests
import hashlib
import os
import time
from lang import TRANSLATIONS

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Carica il file CSS
local_css("style.css")
# Inietta il "Regista Audio" JavaScript
st.components.v1.html(
    """
    <script>
    // Funzione che ferma tutti gli altri audio quando ne parte uno
    const stopOtherAudio = (event) => {
        const allAudios = window.parent.document.querySelectorAll('audio');
        allAudios.forEach(audio => {
            if (audio !== event.target) {
                audio.pause();
                audio.currentTime = 0; // Opzionale: resetta all'inizio
            }
        });
    };

    // Monitoriamo costantemente la pagina per nuovi player audio (Streamlit li crea dinamicamente)
    const observer = new MutationObserver(() => {
        const audios = window.parent.document.querySelectorAll('audio');
        audios.forEach(audio => {
            audio.removeEventListener('play', stopOtherAudio); // Evita duplicati
            audio.addEventListener('play', stopOtherAudio);
        });
    });

    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    height=0, # Lo rendiamo invisibile
)
# --- CONFIGURAZIONE (ENV) ---
NAVIDROME_URL = os.getenv("NAVIDROME_URL", "")
USERNAME = os.getenv("NAVIDROME_USER", "")
PASSWORD = os.getenv("NAVIDROME_PASS", "")
SALT = os.getenv("NAVIDROME_SALT", "")
TOKEN = hashlib.md5((PASSWORD + SALT).encode("utf-8")).hexdigest()

LANG_CODE = os.getenv("APP_LANG", "IT").upper()
T = TRANSLATIONS.get(LANG_CODE, TRANSLATIONS["IT"])

VERSION = f"V6.1.9.RC18-{LANG_CODE}"
FLAGS = {"IT": "🇮🇹", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "DE": "🇩🇪", "ES": "🇪🇸", "CH": "🇨🇭"}

# --- FLAGS ---
@st.cache_data
def get_world_countries():
    # Recuperiamo una lista completa di nazioni (Nome -> Codice ISO)
    try:
        response = requests.get("https://flagcdn.com/en/codes.json")
        return response.json()
    except:
        return {}

WORLD_COUNTRIES = get_world_countries()

def get_flag_emoji(country_code):
    """Trasforma un codice ISO (es. 'IT') in un'emoji bandiera 🇮🇹"""
    if not country_code or len(country_code) != 2:
        return "📻"
    # Formula magica per convertire i codici regionali in emoji
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)

def find_flag_in_string(text):
    """Cerca nazioni nel testo e restituisce l'emoji generata al volo"""
    if not text: 
        return None
    
    text_lower = text.lower()
    
    # 1. Controlliamo le varianti comuni per mappare al codice ISO
    common_variants = {
        "it": ["italia", "italian", "itally"],
        "gb": ["uk", "united kingdom", "british", "england"],
        "us": ["usa", "america", "united states"],
        "br": ["brazil", "brazilian", "brasil"],
        "jp": ["japan", "japanese", "nippon"],
        "ru": ["russia", "russian"],
        "ca": ["canada", "canadian"]
    }

    for code, keywords in common_variants.items():
        if any(k in text_lower for k in keywords):
            return get_flag_emoji(code)

    # 2. Controlliamo la lista globale WORLD_COUNTRIES
    for code, country_name in WORLD_COUNTRIES.items():
        if len(country_name) > 3 and country_name.lower() in text_lower:
            return get_flag_emoji(code)
            
    return None

# --- FUNZIONI DI SUPPORTO ---
@st.cache_data(ttl=86400)
def get_all_countries():
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

st.set_page_config(
    page_title="NaviRadio Manager", 
    page_icon="📻", # Puoi usare un'emoji o un URL di un'immagine
    layout="wide"
)


lista_ufficiale = [""] + get_all_countries()

with st.sidebar:
    st.header(T["search_header"])
    modi = ["Nome", "Nazione"] if LANG_CODE == "IT" else ["Name", "Country"]
    mode = st.selectbox(T["mode"], modi)
    
    # --- RICERCA LIVE SUL NOME ---
    # Aggiungiamo 'on_change' che punta alla funzione che già usavi per il tasto (trigger_search)
    st.text_input(
        T["name_label"], 
        key="search_name", 
        on_change=trigger_search, # <--- La magia è qui!
        placeholder="Write and wait..."
    )
    
    if mode in ["Nazione", "Country"]:
        st.write("---")
        # Anche qui, se cambi nazione, vogliamo che la ricerca parta subito
        st.selectbox(
            T["country_sel"], 
            options=lista_ufficiale, 
            key="search_country_sel", 
            on_change=trigger_search # <--- Cerca appena selezioni
        )
        st.text_input(
            T["country_text"], 
            key="search_country_text", 
            placeholder="es: America, Italy...", 
            on_change=trigger_search # <--- Cerca appena scrivi la nazione
        )

    # Il tasto cerca ora diventa quasi opzionale, ma teniamolo come 'invio' manuale
    st.button(T["btn_search"], on_click=trigger_search, use_container_width=True, type="primary")
    
    if st.session_state.get('stage') == 1:
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
            ###Ciclo FOR per creare le stazioni###
            for s in st.session_state.results:
                stream_url = s['url_resolved']
                is_duplicate = stream_url in existing_urls
                
                # 1. Tentativo dal codice ufficiale dell'API
                c_code = s.get('countrycode', '').upper()
                
                # Se il codice c'è, generiamo la bandiera subito (senza guardare FLAGS)
                if c_code and c_code != "BY_NAME" and len(c_code) == 2:
                    flag = get_flag_emoji(c_code)
                else:
                    # 2. Investigazione nel Nome e nei Tag
                    flag = find_flag_in_string(s.get('name', ''))
                    if not flag:
                        flag = find_flag_in_string(s.get('tags', ''))

                # 3. Fallback finale
                if not flag:
                    flag = "📻"
                
                # --- LOGICA TITOLO E PREFISSO ---
                votes = s.get('votes', 0)
                is_duplicate = stream_url in existing_urls

                if votes > 5000:
                    top_icon = "👑 " + "[Votes: " + str(votes) + "]"
                elif votes > 1000:
                    top_icon = "🔥 " + "[Votes: " + str(votes) + "]"
                else:
                    top_icon = "[Votes: " + str(votes) + "]"
                is_dup_tag = " ✅" if is_duplicate else ""

                # --- RECUPERO ICONA (FAVICON) ---
                hp = s.get('homepage', '').strip()
                icona = f"https://www.google.com/s2/favicons?sz=64&domain={hp}" if hp else None

                # --- ESTRAZIONE GENERE ---
                tags = s.get('tags', '')
                genere_list = [t.strip().capitalize() for t in tags.split(',') if t.strip()]
                genere_principale = genere_list[0] if genere_list else ("Radio" if LANG_CODE=="IT" else "Station")

                is_dup_tag = " ✅" if is_duplicate else ""

                # --- TITOLO DELL'ELENCO UNIFICATO ---
                titolo_elenco = f"{flag} - {s['name']} {top_icon} [{genere_principale}]{is_dup_tag}"

                with st.expander(titolo_elenco):
                    # Header interno con Logo grande e Titolo
                    h_col1, h_col2 = st.columns([1, 6])
                    with h_col1:
                        if icona:
                            st.image(icona, width=40)
                        else:
                            st.write(f"### {flag}")
                    with h_col2:
                        st.subheader(s['name'])
                        if votes > 1000:
                            st.markdown(f"<span class='top-voted'>🔥 TOP {votes} VOTI</span>", unsafe_allow_html=True)
                    
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
                        
                    st.divider()
                    # Header preview con animazione equalizzatore
                    st.markdown(f"""
                        <div style="display: flex; align-items: center;">
                            <span style="font-weight: bold; margin-right: 10px;">🎧 Quick Preview:</span>
                            <span style="color: #ff4b1f; font-size: 0.8rem; font-weight: bold;">LIVE</span>
                            <div class="eq-container">
                                <div class="eq-bar"></div>
                                <div class="eq-bar"></div>
                                <div class="eq-bar"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.audio(stream_url, format="audio/mp3")
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

            ##
            # Controlliamo se ci sono risultati e se sono almeno pari al numero richiesto (es. 20)
            # Se ne abbiamo ricevuti meno di 20, significa che non ce ne sono altri.
            # Mostriamo il tasto 'More' solo se l'ultima ricerca ha restituito il massimo dei risultati (20)
            # Se ne ha restituiti meno (es. 15), significa che non ce ne sono altri.
            # --- NAVIGAZIONE PAGINATA ---
            # --- NAVIGAZIONE PAGINATA SIMMETRICA ---
            st.divider()
            col_back, col_info, col_next = st.columns([1, 1, 1])

            with col_back:
                # Mostra "Back" solo se non siamo alla prima pagina
                if st.session_state.offset > 0:
                    if st.button("⬅️ " + ("Indietro" if LANG_CODE=="IT" else "Back"), use_container_width=True):
                        st.session_state.offset -= 20
                        st.session_state.results = search_radio(st.session_state.search_name, st.session_state.final_country, st.session_state.offset)
                        st.rerun()
                else:
                    # Bottone disabilitato per mantenere la simmetria
                    st.button("⬅️", disabled=True, use_container_width=True)

            with col_info:
                # Indicatore di pagina centrale (molto utile!)
                pagina_attuale = (st.session_state.offset // 20) + 1
                st.markdown(f"<div style='text-align: center; padding-top: 10px; font-weight: bold; color: #ff4b1f;'>Pag. {pagina_attuale}</div>", unsafe_allow_html=True)

            with col_next:
                # Mostra "Next" solo se abbiamo 20 risultati
                if len(st.session_state.results) >= 20:
                    if st.button(("Avanti" if LANG_CODE=="IT" else "Next") + " ➡️", use_container_width=True):
                        st.session_state.offset += 20
                        st.session_state.results = search_radio(st.session_state.search_name, st.session_state.final_country, st.session_state.offset)
                        st.rerun()
                else:
                    # Bottone disabilitato che indica la fine dei risultati
                    st.button("🏁 " + ("Fine" if LANG_CODE=="IT" else "End"), disabled=True, use_container_width=True)

            st.write("") # Un po' di spazio
            if st.button("🏠 " + T["btn_home"], on_click=reset_home, use_container_width=True):
                st.rerun()
        else:
            # Questo else appartiene al controllo iniziale 'if st.session_state.results:'
            st.warning(T["no_results"])
            st.button(T["btn_home"], on_click=reset_home, use_container_width=True)
start_ping = time.time()
st.divider()
col1, col2 = st.columns([1.2, 0.8])
with col1:
    try:
        requests.get(NAVIDROME_URL, timeout=2)
        ping = int((time.time() - start_ping) * 1000)
        st.markdown(f":gray-badge[:material/check: Navidrome URL: {NAVIDROME_URL} 🟢 Connected ({ping}ms)]")
    except:
        st.markdown(f":gray-badge[:material/check: Navidrome URL: {NAVIDROME_URL} 🔴 Offline]")
with col2:
    st.markdown(f":gray-badge[:material/check: User: {USERNAME} ]")
    
st.divider()

# Proporzioni colonne per evitare che vadano a capo
col1, col2, col3, col4 = st.columns([1.2, 1.2, 0.8, 0.8])

with col1:
    st.markdown(f"""
        <div class="custom-badge">
            <span style="background-color: #8a2be2; color: white; padding: 4px 8px;">⭐ Version</span>
            <span style="background-color: #2e2e2e; color: #fff; padding: 4px 8px;">{VERSION}</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    total = get_total_radios()
    st.markdown(f"""
        <div class="custom-badge">
            <span style="background-color: #007ec6; color: white; padding: 4px 8px;">📻 {T.get('total_radios', 'Radios')}</span>
            <span style="background-color: #2e2e2e; color: #fff; padding: 4px 8px;">{total}</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-Repo-orange?logo=github)](https://github.com/brunopiras/naviradiomanager)")

with col4:
    st.markdown("[![Reddit](https://img.shields.io/badge/Reddit-Discuss-orange?logo=reddit&logoColor=white)](https://www.reddit.com/r/navidrome/comments/1rmklet/i_built_a_webgui_to_manage_navidrome_radio/)")
time.sleep(.1)