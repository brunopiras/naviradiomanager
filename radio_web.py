####
import streamlit as st
import requests
import hashlib
import os
import time
from lang import TRANSLATIONS
st.set_page_config(
    page_title="NaviRadioManager",
    page_icon="📻",
    layout="wide", 
    initial_sidebar_state="auto" 
)
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
local_css("style.css")
NAVIDROME_URL = os.getenv("NAVIDROME_URL", "")
USERNAME = os.getenv("NAVIDROME_USER", "")
PASSWORD = os.getenv("NAVIDROME_PASS", "")
SALT = os.getenv("NAVIDROME_SALT", "")
TOKEN = hashlib.md5((PASSWORD + SALT).encode("utf-8")).hexdigest()
LANG_CODE = os.getenv("APP_LANG", "IT").upper()
T = TRANSLATIONS.get(LANG_CODE, TRANSLATIONS["IT"])
VERSION = f"6.2.b7-{LANG_CODE}"
FLAGS = {"IT": "🇮🇹", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "DE": "🇩🇪", "ES": "🇪🇸", "CH": "🇨🇭"}
def fix_url(url):
    if not url:
        return url
    if url.startswith("http:") and not url.startswith("http://"):
        return url.replace("http:", "http://", 1)
    if url.startswith("https:") and not url.startswith("https://"):
        return url.replace("https:", "https://", 1)
    return url
@st.cache_data
def get_world_countries():
    try:
        response = requests.get("https://flagcdn.com/en/codes.json")
        return response.json()
    except:
        return {}
WORLD_COUNTRIES = get_world_countries()
def get_flag_emoji(country_code):
    if not country_code or len(country_code) != 2:
        return "📻"
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)
def find_flag_in_string(text):
    if not text: 
        return None
    text_lower = text.lower()
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
    for code, country_name in WORLD_COUNTRIES.items():
        if len(country_name) > 3 and country_name.lower() in text_lower:
            return get_flag_emoji(code)
    return None
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
        if isinstance(stations, dict): stations = [stations]
        return [s['streamUrl'] for s in stations if 'streamUrl' in s]
    except:
        return []
def sync_to_sel():
    st.session_state.search_country_text = ""
def sync_to_text():
    st.session_state.search_country_sel = ""
if 'stage' not in st.session_state: st.session_state.stage = 0 
if 'results' not in st.session_state: st.session_state.results = []
if 'offset' not in st.session_state: st.session_state.offset = 0
if 'search_reverse' not in st.session_state: st.session_state.search_reverse = "true"
if 'search_name' not in st.session_state: st.session_state.search_name = ""
if 'search_country' not in st.session_state: st.session_state.search_country = ""
@st.cache_data(ttl=600)
def search_radio(name, country, offset, reverse="true"): # <--- Aggiungi reverse qui
    params = {
        "name": name, 
        "country": country, 
        "order": "votes", 
        "reverse": reverse, # <--- Usa il parametro diretto
        "limit": 20, 
        "offset": offset,
        "hidebroken": "true",
        "format": "json"
    }
    try:
        # Usa 'all' per evitare timeout su singoli server
        response = requests.get("https://all.api.radio-browser.info/json/stations/search", params=params, timeout=10)
        return response.json()
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
def get_radios():
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        "u": USERNAME, "t": TOKEN, "s": SALT, 
        "v": "1.16.1", "c": "NaviRadioManager", "f": "json"
    }
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        # Navidrome restituisce una lista dentro internetRadioStation
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
        # Se c'è una sola radio, Subsonic a volte restituisce un dizionario invece di una lista
        if isinstance(stations, dict):
            return [stations]
        return stations
    except Exception as e:
        st.error(f"Errore get_radios: {e}")
        return []

def delete_radio(radio_id):
    """Elimina una radio da Navidrome usando il suo ID"""
    url = f"{NAVIDROME_URL}/rest/deleteInternetRadioStation.view"
    params = {
        "u": USERNAME, "t": TOKEN, "s": SALT,
        "v": "1.16.1", "c": "NaviRadioManager", "f": "json",
        "id": radio_id
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"subsonic-response": {"status": "failed", "error": {"message": str(e)}}}
def vote_for_station(uuid):
    try:
        url = f"https://all.api.radio-browser.info/json/vote/{uuid}"
        response = requests.get(url)
        return response.ok
    except:
        return False
def get_total_radios():
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
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        if isinstance(stations, dict):
            return 1
        return len(stations)
    except Exception as e:
        return "?"
def bulk_add_radios():
    if not st.session_state.results:
        st.toast(T.get("bulk_no_results", "⚠️ Nessuna radio da aggiungere!"), icon="⚠️")
        return

    # Etichetta iniziale dello stato
    start_label = T.get("bulk_start", "🚀 Avvio aggiunta di massa...")
    
    with st.status(start_label, expanded=True) as status:
        added = 0
        skipped = 0
        
        # Recupero radio esistenti per evitare duplicati
        existing_urls = get_existing_radios() 
        
        for radio in st.session_state.results:
            name = radio.get('name', 'Unknown')
            url = radio.get('url_resolved', radio.get('url', ''))
            
            if url in existing_urls:
                # Testo Salto (già presente)
                skip_msg = T.get("bulk_skip", "⏩ Salto (già presente):")
                status.write(f"{skip_msg} {name}")
                skipped += 1
            else:
                # Testo Aggiunta in corso
                proc_msg = T.get("bulk_process", "➕ Aggiunta in corso:")
                status.write(f"{proc_msg} {name}")
                
                # Esegui l'aggiunta
                res = add_to_navidrome(radio)
                
                # CONTROLLO SE È ANDATA BENE
                if res.get('subsonic-response', {}).get('status') == 'ok':
                    added += 1
                else:
                    # SE C'È UN ERRORE, SCRIVILO NEL BOX DI STATO
                    err_msg = T.get("err_add", "❌ Errore")
                    status.write(f"{err_msg}: {name}")
                
                time.sleep(0.1)
        
        # Riassunto finale nel box di stato
        final_msg = T.get("bulk_done", "✅ Completato! Aggiunte: {added}, Saltate: {skipped}").format(added=added, skipped=skipped)
        status.update(label=final_msg, state="complete", expanded=False)
        
        # Messaggio di successo fisso e Toast finale
        st.success(final_msg)
        toast_finish = T.get("bulk_toast", "✅ Operazione riuscita! (+{added})").format(added=added)
        st.toast(toast_finish, icon="📻")
def trigger_search():
    # 1. Recupero parametri di ricerca
    name = st.session_state.get('search_name', "").strip()
    t = st.session_state.get('search_country_text', "").strip()
    s = st.session_state.get('search_country_sel', "")
    country = t if t else s
    
    # 2. Reset dello stato per una nuova ricerca
    st.session_state.final_country = country.strip()
    st.session_state.search_reverse = "true"  # Reset ordine a TOP
    st.session_state.offset = 0               # Reset a PAGINA 1
    st.session_state.stage = 1                # Passa alla visualizzazione risultati
    
    # 3. Chiamata alla funzione con TUTTI e 4 gli argomenti richiesti
    st.session_state.results = search_radio(
        name, 
        st.session_state.final_country, 
        0, 
        "true" # <--- L'argomento mancante che causava l'errore
    )

def reset_home():
    # Pulisce i risultati e torna allo stage 0 (Schermata Welcome)
    st.session_state.stage = 0
    st.session_state.results = []
    st.session_state.offset = 0
    st.session_state.search_reverse = "true"
    # Eventuale pulizia dei campi di input se necessario
    if 'search_name' in st.session_state:
        st.session_state.search_name = ""


def rerun():
    st.write("")
st.markdown("<style>[data-testid='stVerticalBlock'] > div {transition: none !important; opacity: 1 !important;}</style>", unsafe_allow_html=True)
st.title(T["title"])
lista_ufficiale = [""] + get_all_countries()
with st.sidebar:
    st.header(T["search_header"])
    modi = ["Nome", "Nazione"] if LANG_CODE == "IT" else ["Name", "Country"]
    mode = st.selectbox(T["mode"], modi)
    st.text_input(
        T["name_label"], 
        key="search_name", 
        on_change=trigger_search,
        placeholder="Write and wait..."
    )
    if mode in ["Nazione", "Country"]:
        st.write("---")
        st.selectbox(
            T["country_sel"], 
            options=lista_ufficiale, 
            key="search_country_sel", 
            on_change=trigger_search
        )
        st.text_input(
            T["country_text"], 
            key="search_country_text", 
            placeholder="es: America, Italy...", 
            on_change=trigger_search
        )
    st.button(T["btn_search"], on_click=trigger_search, use_container_width=True, type="primary")
    if st.session_state.get('stage') == 1:
        st.button(T["btn_home"], on_click=reset_home, use_container_width=True)
main_area = st.empty()
with main_area.container():
    if st.session_state.stage == 0:
        st.info(T["welcome"])
    elif st.session_state.stage == 1:
        existing_urls = get_existing_radios()  
        if st.session_state.results:
            btn_label = T.get("btn_bulk_add", "➕ Add entire page to Navidrome")
            if st.button(btn_label, use_container_width=True, type="primary"):
                bulk_add_radios()
                #st.rerun()
            col_home, col_top, col_low = st.columns([2, 1, 1])
            
            with col_home:
                st.button(f"🏠 {T['btn_home']}", on_click=reset_home, use_container_width=True, key="btn_home_main")
            
            with col_top:
                # Recuperiamo la traduzione per Top
                label_top = T.get("btn_sort_top", "🔥 Top Votes")
                if st.button(label_top, use_container_width=True, key="btn_sort_top"):
                    st.session_state.search_reverse = "true"
                    st.session_state.offset = 0
                    st.session_state.results = search_radio(
                        st.session_state.search_name, 
                        st.session_state.final_country, 
                        0, 
                        "true"
                    )
                    st.rerun()
            
            with col_low:
                # Recuperiamo la traduzione per Low
                label_low = T.get("btn_sort_low", "🧊 Low Votes")
                if st.button(label_low, use_container_width=True, key="btn_sort_low"):
                    st.session_state.search_reverse = "false"
                    st.session_state.offset = 0
                    st.session_state.results = search_radio(
                        st.session_state.search_name, 
                        st.session_state.final_country, 
                        0, 
                        "false"
                    )
                    st.rerun()

            st.write(f"### {T['results']}")
            
            all_my_radios = get_radios() 

            for s in st.session_state.results:
                raw_url = s.get('url_resolved', '')
                stream_url = fix_url(raw_url)
                
                # --- LOGICA RECUPERO ID (TIENI QUESTA) ---
                is_duplicate = False
                navidrome_id = None
                
                def clean_u(u): 
                    return str(u).strip().lower().rstrip('/')

                target_url = clean_u(stream_url)

                for my_r in all_my_radios:
                    # Navidrome a volte usa 'url' e a volte 'streamUrl'
                    current_nav_url = clean_u(my_r.get('url') or my_r.get('streamUrl', ''))
                    if target_url and current_nav_url and (target_url == current_nav_url or target_url in current_nav_url or current_nav_url in target_url):
                        is_duplicate = True
                        navidrome_id = my_r.get('id')
                        break
                
                # --- LOGICA BANDIERE E VOTI ---
                c_code = s.get('countrycode', '').upper()
                if c_code and c_code != "BY_NAME" and len(c_code) == 2:
                    flag = get_flag_emoji(c_code)
                else:
                    flag = find_flag_in_string(s.get('name', ''))
                    if not flag:
                        flag = find_flag_in_string(s.get('tags', ''))
                if not flag:
                    flag = "📻"
                
                votes = s.get('votes', 0)

                # !!! ATTENZIONE !!! 
                # LA RIGA "is_duplicate = stream_url in existing_urls" È STATA ELIMINATA QUI.
                # NON AGGIUNGERE ALTRO DOPO 'votes'.
                ##is_duplicate = stream_url in existing_urls
                if votes > 5000:
                    top_icon = "👑 " + "[Votes: " + str(votes) + "]"
                elif votes > 1000:
                    top_icon = "🔥 " + "[Votes: " + str(votes) + "]"
                else:
                    top_icon = "[Votes: " + str(votes) + "]"
                is_dup_tag = " ✅" if is_duplicate else ""
                hp = s.get('homepage', '').strip()
                icona = f"https://www.google.com/s2/favicons?sz=64&domain={hp}" if hp else None
                tags = s.get('tags', '')
                genere_list = [t.strip().capitalize() for t in tags.split(',') if t.strip()]
                genere_principale = genere_list[0] if genere_list else ("Radio" if LANG_CODE=="IT" else "Station")
                is_dup_tag = " ✅" if is_duplicate else ""
                titolo_elenco = f"{flag} - {s['name']} {top_icon} [{genere_principale}]{is_dup_tag}"
                with st.expander(titolo_elenco):
                    h_col1, h_col2 = st.columns([1, 6])
                    with h_col1:
                        if icona:
                            st.image(icona, width=55)
                        else:
                            st.write(f"### {flag}")
                    with h_col2:
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
                        try:
                            if stream_url:
                                st.audio(stream_url, format="audio/mp3")
                            else:
                                st.warning("URL not available")
                        except Exception as e:
                            st.error(f"Unable to load audio: {stream_url}")
                    d_col1, d_col2 = st.columns(2)
                    bitrate = s.get('bitrate', 0)
                    codec = s.get('codec', 'N/D')
                    if bitrate >= 192:
                        q_color, q_label = "green", ("High Quality" if LANG_CODE == "EN" else "Alta Qualità")
                    elif bitrate >= 128:
                        q_color, q_label = "blue", ("Standard Quality" if LANG_CODE == "EN" else "Qualità Standard")
                    else:
                        q_color, q_label = "orange", ("Low Quality" if LANG_CODE == "EN" else "Bassa Qualità")
                    with d_col1:
                        st.markdown(f"**{codec}** @ {bitrate} kbps")
                    with d_col2:
                        st.markdown(f":{q_color}[{q_label}]")
                    st.progress(min(bitrate / 320, 1.0))
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        st.caption(f"⭐ {votes} votes")
                    with f_col2:
                        if hp:
                            st.caption(f"🔗 [Web Site]({hp})")
                    st.divider()
                    col_v, col_a = st.columns([1, 1])
                    with col_v:
                        v_label = "👍 " + ("Vota Radio" if LANG_CODE == "IT" else "Vote Radio")
                        if st.button(v_label, key=f"vote_{s['stationuuid']}", use_container_width=True):
                            if vote_for_station(s['stationuuid']):
                                msg = "Voto inviato! Grazie! 🎉" if LANG_CODE == "IT" else "Vote sent! Thanks! 🎉"
                                st.toast(msg)
                            else:
                                err = "Errore nel voto" if LANG_CODE == "IT" else "Voting error"
                                st.error(err)

                    with col_a:
                        if is_duplicate:
                            btn_del_label = T.get("btn_delete", "🗑️ Remove")
                            if st.button(btn_del_label, key=f"del_{s['stationuuid']}", use_container_width=True):
                                if navidrome_id:
                                    res = delete_radio(navidrome_id)
                                    # Verifichiamo la risposta di Navidrome
                                    status = res.get('subsonic-response', {}).get('status')
                                    
                                    if status == 'ok':
                                        st.toast(T.get("msg_deleted", "🗑️ Removed!"), icon="🗑️")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        # Se Navidrome risponde "failed", mostriamo l'errore reale
                                        error_msg = res.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                                        st.error(f"Navidrome Error: {error_msg}")
                                else:
                                    st.error("Errore: ID radio non trovato nel database!")
                        else:
                            # Tasto Aggiungi (con gestione errore come da screenshot)
                            if st.button(T["add_btn"], key=f"add_{s['stationuuid']}", use_container_width=True, type="primary"):
                                res = add_to_navidrome(s)
                                if res.get('subsonic-response', {}).get('status') == 'ok': 
                                    st.success(T["success"])
                                    time.sleep(1)
                                    st.rerun() 
                                else: 
                                    st.error(T.get("err_add", "❌ Error adding station"))
                    if is_duplicate:
                        msg = "⚠️ Già presente in NAVIDROME" if LANG_CODE=="IT" else "⚠️ Already exists in NAVIDROME"
                        st.markdown(
                            f"""
                            <div style="text-align: center; color: gray; font-size: 0.8rem; margin-top: -10px; margin-bottom: 10px;">
                                {msg}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
            st.divider()
            col_back, col_info, col_next = st.columns([1, 1, 1])

            with col_back:
                if st.session_state.offset > 0:
                    if st.button("⬅️ " + ("Indietro" if LANG_CODE=="IT" else "Back"), use_container_width=True, key="nav_back"):
                        st.session_state.offset -= 20
                        # Recuperiamo l'ordine scelto (Top o Low) dalla sessione
                        current_rev = st.session_state.get('search_reverse', "true")
                        st.session_state.results = search_radio(st.session_state.search_name, st.session_state.final_country, st.session_state.offset, current_rev)
                        st.rerun()

            with col_info:
                pagina_attuale = (st.session_state.offset // 20) + 1
                st.markdown(f"<div style='text-align: center; padding-top: 10px; font-weight: bold; color: #ff4b1f;'>Pag. {pagina_attuale}</div>", unsafe_allow_html=True)

            with col_next:
                if len(st.session_state.results) >= 20:
                    if st.button(("Avanti" if LANG_CODE=="IT" else "Next") + " ➡️", use_container_width=True, key="nav_next"):
                        st.session_state.offset += 20
                        # Recuperiamo l'ordine scelto (Top o Low) dalla sessione
                        current_rev = st.session_state.get('search_reverse', "true")
                        st.session_state.results = search_radio(st.session_state.search_name, st.session_state.final_country, st.session_state.offset, current_rev)
                        st.rerun()
                else:
                    st.button("🏁 " + ("Fine" if LANG_CODE=="IT" else "End"), disabled=True, use_container_width=True)

            st.write("")
            if st.button("🏠 " + T["btn_home"], on_click=reset_home, use_container_width=True):
                st.rerun()
        else:
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
time.sleep(.1)
with st.sidebar:  
    v_safe = str(VERSION).replace("-", "--")
    footer_html = f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; padding: 10px;">
        <a href="https://github.com/brunopiras/naviradiomanager" target="_blank">
            <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="Github">
        </a>
        <a href="https://reddit.com/r/navidrome/comments/1rmklet/i_built_a_webgui_to_manage_navidrome_radio/" target="_blank">
            <img src="https://img.shields.io/badge/Reddit-FF4500?style=for-the-badge&logo=reddit&logoColor=white" alt="Reddit">
        </a>
    </div>
    <div style="text-align: center; margin-top: 5px;">
        <img src="https://img.shields.io/badge/Ver.-{v_safe}-blue?style=flat-square" alt="Ver.">
        <img src="https://img.shields.io/badge/Navi Stat.-{get_total_radios()}-blue?style=flat-square" alt="Navi Stat.">
    </div>
    """
with st.sidebar:
    st.markdown(footer_html, unsafe_allow_html=True)
    time.sleep(.1)
st.divider()
st.caption(f"© 2026 NaviRadioManager")
def inject_js(file_path):
    try:
        with open(file_path, 'r') as f:
            js_code = f.read()
            st.components.v1.html(f"<script>{js_code}</script>", height=0)
    except FileNotFoundError:
        pass
inject_js("audio_handler.js")