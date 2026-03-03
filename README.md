```markdown
# 📻 Navidrome Radio Manager (V6.1)



---

## 🇮🇹 Descrizione (Italiano)
**Navidrome Radio Manager** è una web-app leggera basata su Streamlit per gestire le stazioni radio
del tuo server **Navidrome**. Cerca tra migliaia di stazioni globali e aggiungile con un clic, evitando i duplicati.

### ✨ Caratteristiche
* **Ricerca Ibrida**: Cerca per nome o seleziona una nazione dalla lista ufficiale.
* **Controllo Duplicati**: L'app interroga Navidrome e ti avvisa (con l'icona ✅) se una radio è già presente.
* **Internazionale**: Supporto per Italiano e Inglese tramite variabili d'ambiente.
* **Affidabilità**: Utilizza il sistema di mirror `all.api` per una ricerca sempre attiva.

---

## 🇬🇧 Description (English)
**Navidrome Radio Manager** is a lightweight Streamlit-based web app to manage your **Navidrome** radio stations.
Browse thousands of global stations and add them instantly while avoiding duplicates.

### ✨ Features
* **Hybrid Search**: Search by name or pick a country from the official list.
* **Duplicate Check**: Real-time query to Navidrome to flag stations already in your database (✅ icon).
* **International**: Built-in Italian and English support via environment variables.
* **Reliability**: Uses the `all.api` mirror system for maximum availability.

---

## 🚀 Installazione / Installation

### 1. Requisiti / Requirements
* 🇮🇹 Navidrome attivo e Docker installato.
* 🇬🇧 Active Navidrome instance and Docker installed.

### 2. Docker Compose
🇮🇹 Crea un file `docker-compose.yml` / 🇬🇧 Create a `docker-compose.yml` file:

```yaml
services:
  radio-manager:
    build: .
    container_name: radio-manager
    ports:
      - "8501:8501"
    environment:
      - APP_LANG=IT                  # IT or EN
      - NAVIDROME_URL=http://YOUR_IP:4533
      - NAVIDROME_USER=your_user
      - NAVIDROME_PASS=your_password
      - NAVIDROME_SALT=sfggdsfgegefgefghss
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
      - STREAMLIT_SERVER_COOKIE_SECRET=hjdgakasjkdasljdkekjekekjjssjss
      - STREAMLIT_SERVER_ADDRESS=YOUR_IP
      - STREAMLIT_GLOBAL_DATA_FRAME_SERIALIZATION=legacy
    restart: unless-stopped

```

### 3. Avvio / Startup

🇮🇹 Costruisci e avvia il container / 🇬🇧 Build and run the container:

```bash
docker-compose up -d --build

```

---

## 🛠️ Tech Stack

* **UI**: Streamlit (Python)
* **APIs**: Radio-Browser API & Subsonic API (Navidrome)
* **Container**: Docker (Python 3.11-slim)
* **i18n**: Custom dictionary-based localization (`lang.py`)

```
* **IMAGE**: If you want, use the docker-compose and pre-built image
     (docker pull ghcr.io/brunopiras/naviradiomanager:latest)
```
