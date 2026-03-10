# 📻 Navidrome Radio Manager (V6.2) - Update Mar 10 2026

---

#### This tool uses the APIs of [https://api.radio-browser.info ](https://api.radio-browser.info ) to search for radio stations. (Thanks! ✨)

---

## 🇮🇹 Descrizione (Italiano)

**Navidrome Radio Manager** è una web-app leggera basata su Streamlit per gestire le stazioni radio del tuo server **Navidrome**. Cerca tra migliaia di stazioni globali e gestisci la tua libreria con un clic. Grazie all'integrazione bidirezionale con le API Subsonic, l'app riconosce le radio già presenti e ti permette di aggiungerle, modificarle o rimuoverle istantaneamente tramite un'interfaccia web intuitiva.

## 🇬🇧 Description (English)

**Navidrome Radio Manager** is a lightweight Streamlit-based web app to manage your **Navidrome** radio stations. Browse thousands of global stations and manage your library with one click. Thanks to bidirectional Subsonic API integration, the app recognizes existing stations and allows you to add, edit, or remove them instantly through an intuitive web interface.

---

## 🚀 Installazione / Installation

Scegli il metodo più adatto alle tue esigenze:

### Opzione A: Immagine Pronta (Consigliato / Recommended)

🇮🇹 Usa l'immagine pre-compilata da GitHub Container Registry. Ideale per chi vuole solo usare l'app.
🇬🇧 Use the pre-built image from GHCR. Perfect for users who just want to run the app.

```yaml
services:
  radio-manager:
    image: ghcr.io/brunopiras/naviradiomanager:latest
    container_name: radio-manager
    ports:
      - "8501:8501"
    environment:
      - APP_LANG=EN   # IT or EN
      - NAVIDROME_URL=http://YOUR_IP:4533
      - NAVIDROME_USER=your_user
      - NAVIDROME_PASS=your_password
      - NAVIDROME_SALT=your_salt_here
      - TZ=Europe/Rome #Your Country Time
    ###Developers can use to modify on air and test##
    #volumes:
      #- /path/to/radio_web.py:/app/radio_web.py #Optional to developers
      #- /path/to/lang.py:/app/lang.py #Optional to developers
      #- /path/to/.streamlit/config.toml:/app/.streamlit/config.toml
      #- /path/to/style.css:/app/style.css
```

### Opzione B: Build Locale (Sviluppatori / Developers)

🇮🇹 Clona il repository e costruisci l'immagine localmente. Utile per personalizzare il codice.
🇬🇧 Clone the repo and build the image locally. Best for customization.

```bash
git clone https://github.com/brunopiras/naviradiomanager.git 
cd naviradiomanager
docker-compose up -d --build
```

---

## 🛠️ Tech Stack & Features

* **UI**: Streamlit (Python) - *Featuring the custom "Petrol Blue" theme & Italian Flag sidebar!* 🇮🇹
* **APIs**: Radio-Browser API & Subsonic API (Navidrome).
* **Container**: Docker (python:3.14-slim-trixie).
* **🎧 Live Preview**: Integrated HTML5 Audio Player to test streams before adding them.
* **📊 Quality Visualizer**: Real-time bitrate analysis with color-coded progress bars (HQ/MQ/LQ).
* **🔥 Popularity Engine**: Dynamic "TOP" badges for high-voted global stations.
* **✅ Smart Library Sync**: Real-time Subsonic query. If a station is already in your DB, it shows a "Remove" button instead of "Add".
* **🗑️ Instant Removal**: Delete radio stations from your Navidrome library directly from the search results.
* **🔄 Reliability**: Uses the `all.api` mirror system with automatic fallback.
* **📈 Stats Badge**: Real-time counter showing the total number of radios stored in your Navidrome DB.
* **🗳️ Community Vote**: Integrated button to vote for your favorite stations on Radio-Browser.
* **🌍 International Flags**: Visual country flags for each station (Note: Windows might have emoji rendering issues).
* **🔇 Smart Playback**: Custom JS logic to ensure only one stream plays at a time.

### 🆕 New in V6.2 - Radio Management Dashboard

* **📻 My Radios Dashboard**: Dedicated section to view all your Navidrome radio stations in a clean grid layout with favicons.
* **🔍 Station Details**: Expandable detail view for each radio showing ID, name, homepage, stream URL, and vote count.
* **✏️ Edit Stations**: Modify radio name, stream URL, and homepage URL directly via `updateInternetRadioStation` Subsonic API (requires admin privileges).
* **📋 Copy URLs**: One-click copy buttons for both stream URL and homepage URL to clipboard.
* **🧪 Stream Test**: Built-in connectivity test to verify if a stream URL is reachable before saving changes.
* **📋 Quick Navigation**: "Back to List" button in sidebar and action section for fast navigation between detail view and radio grid.
* **🎨 Unified URL Display**: Stream and homepage URLs now displayed in consistent code-block format for better readability.

### 🎨 Quality Indicators

* 🟢 **High Quality**: >192 kbps (Audiophile choice)
* 🔵 **Standard Quality**: 128-191 kbps (Solid stream)
* 🟠 **Low Quality**: <128 kbps (Mobile friendly)
* 🔥 **Top Voted**: Over 1000 community votes on Radio-Browser.

## 📝 Note / Notes

* **Safari Users**: ⚠️ Streamlit sometimes has problems with Safari (V6.1.9-RC5 should fix it). If you experience UI glitches, please try **Chrome** or **Firefox**.
* **Removal Feature**: To remove a station, the app matches the exact URL saved in Navidrome. If the URL has been modified manually in Navidrome, the removal button might not find the ID.
* **Edit Feature**: Editing stations requires Navidrome admin privileges. The edit operation preserves the station ID and all associated metadata (starred status, etc.).

---

###### Special thanks to @WB2024 ([https://github.com/WB2024/Add-Navidrome-Radios ](https://github.com/WB2024/Add-Navidrome-Radios ))

###### This idea came to me while using @WB2024's tool. While his tool interacts directly with the database via CLI, Navidrome Radio Manager uses the **Subsonic API** for a simple, fast, and intuitive web interface!
