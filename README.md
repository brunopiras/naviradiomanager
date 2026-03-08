---

# 📻 Navidrome Radio Manager (V6.1.9-RC18) - Update Mar 8 2026

---

#### This tool uses the APIs of [https://api.radio-browser.info](https://api.radio-browser.info) to search for radio stations. (Thanks! ✨)

---

## 🇮🇹 Descrizione (Italiano)

**Navidrome Radio Manager** è una web-app leggera basata su Streamlit per gestire le stazioni radio del tuo server **Navidrome**. Cerca tra migliaia di stazioni globali e aggiungile con un clic, evitando i duplicati grazie all'integrazione con le API Subsonic.

## 🇬🇧 Description (English)

**Navidrome Radio Manager** is a lightweight Streamlit-based web app to manage your **Navidrome** radio stations. Browse thousands of global stations and add them instantly while avoiding duplicates using Subsonic APIs.

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
    ###Developers can use those to modify on air and test##
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
* **Container**: Docker (python:3.14-slim-trixie) - Optimized for `mac-vlan` networks.
* **🎧 Live Preview**: Integrated HTML5 Audio Player to test streams before adding them.
* **📊 Quality Visualizer**: Real-time bitrate analysis with color-coded progress bars (HQ/MQ/LQ).
* **🔥 Popularity Engine**: Dynamic "TOP" badges for high-voted global stations.
* **✅ Duplicate Check**: Real-time Subsonic query (shows a checkmark if the station is already in your DB).
* **🔄 Reliability**: Uses the `all.api` mirror system with automatic fallback.
* **📈 Stats Badge**: Real-time counter showing the total number of radios stored in your Navidrome DB.
* **🔥 Add Button Radio Vote**: Button to vote stations.
* **🇮🇹 Add Flags to each country (Maybe Windows user issue, I'm sorry!!).
* **🎧 Add JS to stop play only one stream at time.
  
### 🎨 Quality Indicators
- 🟢 **High Quality**: >192 kbps (Audiophile choice)
- 🔵 **Standard Quality**: 128-191 kbps (Solid stream)
- 🟠 **Low Quality**: <128 kbps (Mobile friendly)
- 🔥 **Top Voted**: Over 1000 community votes on Radio-Browser.

  
## 📝 Note / Notes

* **Safari Users**: ⚠️ Streamlit sometimes has problems with Safari (V6.1.9-RC5 should fix it). If you experience UI glitches, please try **Chrome** or **Firefox**.
* **Customization**: Developers can mount volumes to modify `radio_web.py` or `lang.py` without rebuilding (see the Portainer Stack section).

---

###### Special thanks to @WB2024 ([https://github.com/WB2024/Add-Navidrome-Radios](https://github.com/WB2024/Add-Navidrome-Radios))

###### This idea came to me while using @WB2024's tool. While his tool interacts directly with the database via CLI, Navidrome Radio Manager uses the **Subsonic API** for a simple, fast, and intuitive web interface!

---
