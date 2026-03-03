
```markdown
# 📻 Navidrome Radio Manager (V6.1)

Una Web-App leggera e intuitiva per gestire le stazioni radio del tuo server **Navidrome**. Ricerca migliaia di stazioni globali e aggiungile con un clic, evitando i duplicati.

---

## 🇮🇹 Descrizione (Italiano)
**Navidrome Radio Manager** semplifica la gestione delle radio nel tuo ecosistema Navidrome. Invece di inserire manualmente URL e metadati, questa app ti permette di cercare nel database globale di Radio-Browser.

### ✨ Funzionalità
* **Ricerca Ibrida**: Cerca per nome della stazione o seleziona una nazione dalla lista ufficiale.
* **Controllo Duplicati**: L'app interroga Navidrome e ti avvisa (con l'icona ✅) se una radio è già presente.
* **Internazionale**: Supporto integrato per Italiano e Inglese tramite variabili d'ambiente.
* **Stabilità**: Utilizza un sistema di mirror bilanciato (`all.api`) per la massima affidabilità.

---

## 🇬🇧 Description (English)
**Navidrome Radio Manager** streamlines radio station management for your **Navidrome** server. Instead of manually copying URLs, browse thousands of global stations and add them instantly.

### ✨ Features
* **Hybrid Search**: Search by station name or pick a country from the official list.
* **Duplicate Check**: Real-time query to Navidrome to flag stations already in your database (✅ icon).
* **International**: Built-in Italian and English support via environment variables.
* **Reliability**: Uses a balanced mirror system (`all.api`) to ensure 24/7 availability.

---

## 🚀 Installazione / Installation

### 1. Preparazione File / File Setup
Assicurati di avere questi file nella stessa cartella:
* `radio_web.py` (Lo script principale)
* `lang.py` (Il file delle traduzioni)
* `Dockerfile`

### 2. Docker Compose
Crea un file `docker-compose.yml`:

```yaml
services:
  radio-manager:
    build: .
    container_name: radio-manager
    ports:
      - "8501:8501"
    environment:
      - APP_LANG=IT    # Options: IT, EN
      - NAVIDROME_URL=http://YOUR_IP:4533
      - NAVIDROME_USER=your_user
      - NAVIDROME_PASS=your_password
      - NAVIDROME_SALT=una_frase_qualsiasi
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
      - STREAMLIT_SERVER_COOKIE_SECRET=ccfsffshhhshkddkhjkskksjjjjss
      - STREAMLIT_SERVER_ADDRESS=YOUR_IP
      - STREAMLIT_GLOBAL_DATA_FRAME_SERIALIZATION=legacy
    restart: unless-stopped

```

### 3. Build & Run

Esegui il comando:

```bash
docker-compose up -d --build

```

---

## 🛠️ Tech Stack

* **UI**: Streamlit
* **API**: Radio-Browser API & Subsonic API (Navidrome)
* **Platform**: Docker (Python 3.11-slim)
```
