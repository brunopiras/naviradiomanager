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
VERSION = f"6.2-{LANG_CODE}"

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
        if isinstance(stations, dict): 
            stations = [stations]
        return [s['streamUrl'] for s in stations if 'streamUrl' in s]
    except:
        return []

@st.cache_data(ttl=300)
def get_all_my_radios_with_details():
    """Recupera tutte le radio da Navidrome con dettagli completi"""
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        "u": USERNAME,
        "t": TOKEN,
        "s": SALT,
        "v": "1.16.1",
        "c": "NaviRadioManager",
        "f": "json"
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
        if isinstance(stations, dict):
            return [stations]
        return stations if stations else []
    except Exception as e:
        st.error(f"Errore recupero radio: {e}")
        return []

def sync_to_sel():
    st.session_state.search_country_text = ""

def sync_to_text():
    st.session_state.search_country_sel = ""

# ========== INIZIALIZZAZIONE STATI SESSIONE ==========
if 'stage' not in st.session_state: 
    st.session_state.stage = 0 
if 'results' not in st.session_state: 
    st.session_state.results = []
if 'offset' not in st.session_state: 
    st.session_state.offset = 0
if 'search_reverse' not in st.session_state: 
    st.session_state.search_reverse = "true"
if 'search_name' not in st.session_state: 
    st.session_state.search_name = ""
if 'search_country' not in st.session_state: 
    st.session_state.search_country = ""
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "search"
if 'my_radios' not in st.session_state:
    st.session_state.my_radios = []
if 'selected_radio' not in st.session_state:
    st.session_state.selected_radio = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'editing_radio' not in st.session_state:
    st.session_state.editing_radio = None

@st.cache_data(ttl=600)
def search_radio(name, country, offset, reverse="true"):
    params = {
        "name": name, 
        "country": country, 
        "order": "votes", 
        "reverse": reverse,
        "limit": 20, 
        "offset": offset,
        "hidebroken": "true",
        "format": "json"
    }
    try:
        response = requests.get("https://all.api.radio-browser.info/json/stations/search", params=params, timeout=10)
        return response.json()
    except:
        return []

def add_to_navidrome(station):
    endpoint = f"{NAVIDROME_URL}/rest/createInternetRadioStation"
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": VERSION, "c": "NaviRadioManager", "f": "json",
              "name": station['name'], "streamUrl": station['url_resolved'], "homePageUrl": station.get('homepage', '')}
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
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
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

# ========== NUOVA FUNZIONE UPDATE CORRETTA ==========
def update_radio(radio_id, name, stream_url, homepage_url):
    """
    Aggiorna una radio esistente usando l'API ufficiale updateInternetRadioStation.
    Richiede privilegi di amministratore.
    """
    endpoint = f"{NAVIDROME_URL}/rest/updateInternetRadioStation.view"
    params = {
        "u": USERNAME,
        "t": TOKEN,
        "s": SALT,
        "v": "1.16.1",
        "c": "NaviRadioManager",
        "f": "json",
        "id": radio_id,
        "name": name,
        "url": stream_url,  # Nota: l'API usa 'url' non 'streamUrl' per l'update
        "homePageUrl": homepage_url
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"subsonic-response": {"status": "failed", "error": {"message": str(e)}}}


def enter_edit_mode(radio):
    st.session_state.edit_mode = True
    st.session_state.editing_radio = radio


def cancel_edit():
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

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

    start_label = T.get("bulk_start", "🚀 Avvio aggiunta di massa...")
    
    with st.status(start_label, expanded=True) as status:
        added = 0
        skipped = 0
        
        existing_urls = get_existing_radios() 
        
        for radio in st.session_state.results:
            name = radio.get('name', 'Unknown')
            url = radio.get('url_resolved', radio.get('url', ''))
            
            if url in existing_urls:
                skip_msg = T.get("bulk_skip", "⏩ Salto (già presente):")
                status.write(f"{skip_msg} {name}")
                skipped += 1
            else:
                proc_msg = T.get("bulk_process", "➕ Aggiunta in corso:")
                status.write(f"{proc_msg} {name}")
                
                res = add_to_navidrome(radio)
                
                if res.get('subsonic-response', {}).get('status') == 'ok':
                    added += 1
                else:
                    err_msg = T.get("err_add", "❌ Errore")
                    status.write(f"{err_msg}: {name}")
                
                time.sleep(0.1)
        
        final_msg = T.get("bulk_done", "✅ Completato! Aggiunte: {added}, Saltate: {skipped}").format(added=added, skipped=skipped)
        status.update(label=final_msg, state="complete", expanded=False)
        
        st.success(final_msg)
        toast_finish = T.get("bulk_toast", "✅ Operazione riuscita! (+{added})").format(added=added)
        st.toast(toast_finish, icon="📻")

def trigger_search():
    name = st.session_state.get('search_name', "").strip()
    t = st.session_state.get('search_country_text', "").strip()
    s = st.session_state.get('search_country_sel', "")
    country = t if t else s
    
    st.session_state.final_country = country.strip()
    st.session_state.search_reverse = "true"
    st.session_state.offset = 0
    st.session_state.stage = 1
    st.session_state.view_mode = "search"
    
    st.session_state.results = search_radio(
        name, 
        st.session_state.final_country, 
        0, 
        "true"
    )

def reset_home():
    st.session_state.stage = 0
    st.session_state.results = []
    st.session_state.offset = 0
    st.session_state.search_reverse = "true"
    st.session_state.view_mode = "search"
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None
    
    if 'search_name' in st.session_state:
        st.session_state.search_name = ""

def switch_to_manage_mode():
    """Passa alla modalità gestione radio e carica la lista"""
    st.session_state.view_mode = "manage"
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None
    st.session_state.my_radios = get_all_my_radios_with_details()

def select_radio_for_details(radio):
    """Seleziona una radio per vedere i dettagli"""
    st.session_state.selected_radio = radio
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

def back_to_radio_list():
    """Torna alla lista delle radio"""
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

def copy_to_clipboard(text):
    """Utility per copiare testo (simulato con codice JS)"""
    js_code = f"""
    <script>
    navigator.clipboard.writeText(`{text}`);
    </script>
    """
    st.components.v1.html(js_code, height=0)
    st.toast("📋 Copiato negli appunti!", icon="📋")

def rerun():
    st.write("")

st.markdown("<style>[data-testid='stVerticalBlock'] > div {transition: none !important; opacity: 1 !important;}</style>", unsafe_allow_html=True)

st.title(T["title"])

lista_ufficiale = [""] + get_all_countries()

with st.sidebar:

    st.header(T["search_header"])
    st.divider()   
    # Bottone per gestione radio
    manage_label = T.get("btn_manage_radios", "📻 Navidrome Radio" if LANG_CODE == "IT" else "📻 Navidrome Radios")
    if st.button(manage_label, use_container_width=True, type="secondary"):
        switch_to_manage_mode()
        st.rerun()
    
    st.divider()
    
    # Sezione ricerca originale (visibile solo in modalità ricerca)
    if st.session_state.view_mode == "search":
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
    
    # Sidebar in modalità gestione
    else:
        #st.subheader("📻 " + (T.get("my_radios_title", "Le mie Radio") if LANG_CODE == "IT" else "My Radios"))
        
        back_label = "🔙 " + (T.get("back_to_search", "Torna alla Ricerca") if LANG_CODE == "IT" else "Back to Search")
        if st.button(back_label, use_container_width=True):
            st.session_state.view_mode = "search"
            st.session_state.selected_radio = None
            st.session_state.edit_mode = False
            st.rerun()
        
        st.divider()
        
        if st.session_state.selected_radio:
            back_list_label = "📋 " + (T.get("back_to_list", "Torna alla Lista") if LANG_CODE == "IT" else "Back to List")
            if st.button(back_list_label, use_container_width=True, type="secondary"):
                back_to_radio_list()
                st.rerun()

main_area = st.empty()

with main_area.container():
    
    # ============================================
    # MODALITÀ GESTIONE RADIO
    # ============================================
    if st.session_state.view_mode == "manage":
        
        # --- Vista Dettaglio Singola Radio ---
        if st.session_state.selected_radio:
            radio = st.session_state.selected_radio
            hp = radio.get('homePageUrl', '').strip()
            stream_url = radio.get('streamUrl', radio.get('url', 'N/D'))
            
            # ========== HEADER CON ICONA E NOME ==========
            header_cols = st.columns([1, 4])
            with header_cols[0]:
                if hp:
                    icona = f"https://www.google.com/s2/favicons?sz=128&domain={hp}"
                    st.image(icona, width=80)
                else:
                    st.markdown("## 📻")
            with header_cols[1]:
                st.title(radio.get('name', 'Unknown'))
                st.caption(f"ID: `{radio.get('id', 'N/D')}`")
            
            st.divider()
            
            # ========== SEZIONE URL E LINK ==========
            st.subheader("🔗 " + (T.get("links", "Info") if LANG_CODE == "IT" else "Info"))
            
            url_cols = st.columns(2)
            
            with url_cols[0]:
                st.markdown("**🌐 Sito Web**" if LANG_CODE == "IT" else "**🌐 Website**")
                if hp:
                    st.code(hp, language=None)  # ← Cambiato da st.markdown(f"[{hp}]({hp})")
                    st.button((T.get("copy_url", "Copia URL") if LANG_CODE == "IT" else "Copy URL"), 
                             key="copy_hp", on_click=lambda: copy_to_clipboard(hp))
                else:
                    st.caption("—")
            
            with url_cols[1]:
                st.markdown("**📡 Stream URL**")
                st.code(stream_url, language=None)
                st.button("📋 " + (T.get("copy_stream", "Copia Stream") if LANG_CODE == "IT" else "Copy Stream"), 
                         key="copy_stream", on_click=lambda: copy_to_clipboard(stream_url))
            
            st.divider()
            
            # ========== SEZIONE STATISTICHE ==========
            stats_cols = st.columns(3)
            
            with stats_cols[0]:
                st.metric(
                    label="⭐ " + (T.get("votes", "Voti") if LANG_CODE == "IT" else "Votes"),
                    value=radio.get('starred', 0) or 0
                )
            
            with stats_cols[1]:
                status = "🟢 Attiva" if LANG_CODE == "IT" else "🟢 Active"
                st.metric(label=T.get("status", "Stato") if LANG_CODE == "IT" else "Status", value=status)
            
            with stats_cols[2]:
                # Placeholder per futura statistica (es. bitrate se disponibile)
                st.metric(label="📊 Info", value="Radio")
            
            st.divider()
            
            # ========== SEZIONE PLAYER ==========
            st.subheader("▶️ " + (T.get("preview", "Anteprima Audio") if LANG_CODE == "IT" else "Audio Preview"))
            
            fixed_url = fix_url(stream_url)
            try:
                if fixed_url:
                    st.audio(fixed_url, format="audio/mp3")
                else:
                    st.warning(T.get("no_preview", "Anteprima non disponibile") if LANG_CODE == "IT" else "Preview not available")
            except Exception as e:
                st.error(f"Errore player: {str(e)}")
            
            st.divider()
            
            # ========== SEZIONE AZIONI CON EDIT FUNZIONANTE (API CORRETTA) ============
            st.subheader("⚡ " + (T.get("actions", "Azioni") if LANG_CODE == "IT" else "Actions"))
            
            # Se siamo in modalità edit, mostra il form
            if st.session_state.edit_mode and st.session_state.editing_radio.get('id') == radio.get('id'):
                st.info("✏️ " + (T.get("edit_mode_info", "Modifica i campi e conferma") if LANG_CODE == "IT" else "Edit fields and confirm"))
                
                with st.form(key=f"edit_form_{radio.get('id')}"):
                    edit_name = st.text_input(
                        T.get("name_label", "Nome") if LANG_CODE == "IT" else "Name",
                        value=radio.get('name', '')
                    )
                    edit_url = st.text_input(
                        T.get("stream_url", "URL Stream") if LANG_CODE == "IT" else "Stream URL",
                        value=radio.get('streamUrl', radio.get('url', ''))
                    )
                    edit_homepage = st.text_input(
                        T.get("homepage_url", "Sito Web") if LANG_CODE == "IT" else "Homepage",
                        value=radio.get('homePageUrl', '')
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button(
                            "💾 " + (T.get("save", "Salva") if LANG_CODE == "IT" else "Save"),
                            use_container_width=True,
                            type="primary"
                        )
                    with col_cancel:
                        cancelled = st.form_submit_button(
                            "❌ " + (T.get("cancel", "Annulla") if LANG_CODE == "IT" else "Cancel"),
                            use_container_width=True
                        )
                    
                    if submitted:
                        if not edit_name or not edit_url:
                            st.error(T.get("err_required_fields", "Nome e URL sono obbligatori") if LANG_CODE == "IT" else "Name and URL are required")
                        else:
                            with st.spinner(T.get("saving", "Salvataggio...") if LANG_CODE == "IT" else "Saving..."):
                                res = update_radio(
                                    radio.get('id'),
                                    edit_name,
                                    edit_url,
                                    edit_homepage
                                )
                                
                                if res.get('subsonic-response', {}).get('status') == 'ok':
                                    st.success(T.get("msg_updated", "✅ Radio aggiornata con successo!") if LANG_CODE == "IT" else "✅ Radio updated successfully!")
                                    cancel_edit()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    err_msg = res.get('subsonic-response', {}).get('error', {}).get('message', 'Errore sconosciuto')
                                    st.error(f"❌ Errore: {err_msg}")
                    
                    if cancelled:
                        cancel_edit()
                        st.rerun()

            else:
                # Visualizzazione normale: 4 bottoni in griglia 2x2
                act_col1, act_col2 = st.columns(2)
                
                with act_col1:
                    if st.button("🧪 " + (T.get("test_stream", "Test Stream") if LANG_CODE == "IT" else "Test Stream"), 
                               use_container_width=True):
                        try:
                            test_resp = requests.get(fixed_url, timeout=5, stream=True)
                            if test_resp.status_code == 200:
                                st.success("✅ Stream raggiungibile!")
                            else:
                                st.warning(f"⚠️ Status: {test_resp.status_code}")
                        except Exception as e:
                            st.error(f"❌ Errore: {str(e)}")
                    
                    # NUOVO: Bottone Torna alla Lista (prima posizione, colore neutro)
                    back_list_color = "secondary"  # o "primary" se vuoi più visibilità
                    if st.button("📋 " + (T.get("back_to_list", "Torna alla Lista") if LANG_CODE == "IT" else "Back to List"), 
                               use_container_width=True, 
                               type=back_list_color):
                        back_to_radio_list()
                        st.rerun()
                
                with act_col2:
                    if st.button("✏️ " + (T.get("edit", "Modifica") if LANG_CODE == "IT" else "Edit"), 
                               use_container_width=True, 
                               type="secondary"):
                        enter_edit_mode(radio)
                        st.rerun()
                    
                    del_label = "🗑️ " + (T.get("delete", "Elimina") if LANG_CODE == "IT" else "Delete")
                    if st.button(del_label, use_container_width=True, type="primary"):
                        # Conferma inline invece di colonne separate
                        confirm_key = f"confirm_del_{radio.get('id')}"
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False
                        
                        if not st.session_state[confirm_key]:
                            st.session_state[confirm_key] = True
                            st.warning("⚠️ " + (T.get("confirm_delete", "Clicca di nuovo per confermare l'eliminazione") if LANG_CODE == "IT" else "Click again to confirm deletion"))
                            st.rerun()
                        else:
                            res = delete_radio(radio.get('id'))
                            if res.get('subsonic-response', {}).get('status') == 'ok':
                                st.success("🗑️ " + (T.get("msg_deleted", "Eliminata!") if LANG_CODE == "IT" else "Deleted!"))
                                # Reset conferma per future eliminazioni
                                st.session_state[confirm_key] = False
                                time.sleep(1)
                                back_to_radio_list()
                                st.rerun()
                            else:
                                err = res.get('subsonic-response', {}).get('error', {}).get('message', 'Errore sconosciuto')
                                st.error(f"❌ {err}")
                                st.session_state[confirm_key] = False
            # ========== FINE SEZIONE AZIONI ==========
        
        # --- Vista Lista di tutte le radio ---
        else:
            st.header(T.get("my_radios_title", "Le mie Radio" if LANG_CODE == "IT" else "My Radios"))
            
            if st.button("🔄 " + (T.get("refresh", "Aggiorna Lista") if LANG_CODE == "IT" else "Refresh List"), 
                       use_container_width=True):
                st.cache_data.clear()
                switch_to_manage_mode()
                st.rerun()
            
            st.divider()
            
            if not st.session_state.my_radios:
                st.warning(T.get("no_radios_found", "Nessuna radio trovata in Navidrome" if LANG_CODE == "IT" 
                               else "No radios found in Navidrome"))
            else:
                st.success(f"📻 {len(st.session_state.my_radios)} " + 
                          (T.get("radios_count", "radio trovate") if LANG_CODE == "IT" else "radios found"))
                
                cols_per_row = 3
                radios = st.session_state.my_radios
                
                for i in range(0, len(radios), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(radios):
                            radio = radios[idx]
                            with cols[j]:
                                hp = radio.get('homePageUrl', '').strip()
                                icona = f"https://www.google.com/s2/favicons?sz=64&domain={hp}" if hp else None
                                
                                with st.container():
                                    if icona:
                                        st.image(icona, width=40)
                                    
                                    st.markdown(f"**{radio.get('name', 'Unknown')[:25]}**")
                                    
                                    det_label = T.get("btn_details", "🔍 Dettagli") if LANG_CODE == "IT" else "🔍 Details"
                                    if st.button(det_label, key=f"det_{radio.get('id')}", use_container_width=True):
                                        select_radio_for_details(radio)
                                        st.rerun()
                                    
                                    st.divider()
    
    # ============================================
    # MODALITÀ RICERCA (ORIGINALE - INVARIATA)
    # ============================================
    else:
        if st.session_state.stage == 0:
            st.info(T["welcome"])
            
        elif st.session_state.stage == 1:
            existing_urls = get_existing_radios()  
            if st.session_state.results:
                btn_label = T.get("btn_bulk_add", "➕ Add entire page to Navidrome")
                if st.button(btn_label, use_container_width=True, type="primary"):
                    bulk_add_radios()
                    
                col_home, col_top, col_low = st.columns([2, 1, 1])
                
                with col_home:
                    st.button(f"🏠 {T['btn_home']}", on_click=reset_home, use_container_width=True, key="btn_home_main")
                
                with col_top:
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
                    
                    is_duplicate = False
                    navidrome_id = None
                    
                    def clean_u(u): 
                        return str(u).strip().lower().rstrip('/')

                    target_url = clean_u(stream_url)

                    for my_r in all_my_radios:
                        current_nav_url = clean_u(my_r.get('url') or my_r.get('streamUrl', ''))
                        if target_url and current_nav_url and (target_url == current_nav_url or target_url in current_nav_url or current_nav_url in target_url):
                            is_duplicate = True
                            navidrome_id = my_r.get('id')
                            break
                    
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
                                        status = res.get('subsonic-response', {}).get('status')
                                        
                                        if status == 'ok':
                                            st.toast(T.get("msg_deleted", "🗑️ Removed!"), icon="🗑️")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            error_msg = res.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                                            st.error(f"Navidrome Error: {error_msg}")
                                    else:
                                        st.error("Errore: ID radio non trovato nel database!")
                            else:
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

# Footer
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