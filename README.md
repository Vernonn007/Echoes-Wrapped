<div align="center">

# 🎧 Echoes

**Your listening story, tracked locally.**
A Spotify-Wrapped-style dashboard and phone remote for **WaveFlow** and **Harmonoid** on Windows.

`Python 3.10+` · `Windows 10/11` · `100% local` · `no accounts, no cloud`

</div>

## 🎬 Demo

![Harmonoid Wrapped Demo](assets/harmonoid-demo.gif)

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

---

## ✨ Features

- 📊 **Dashboard** — total plays, listening time, top tracks/artists, hourly activity chart
- 🎁 **Wrapped** — a Spotify-Wrapped-style recap of your listening
- 📈 **Charts** — monthly trends, artist breakdown, day-of-week activity
- 🏆 **Achievements** — unlockable milestones based on your listening habits
- 🎵 **Live "Now Playing"** with album art, pulled automatically from iTunes
- 🎼 **Synced lyrics** on mobile, fetched from [LRCLIB](https://lrclib.net)
- 📱 **Mobile remote** — play/pause/skip and view stats from your phone over WiFi
- 🌌 **Ambient background** — colours shift to match the current track's album art
- 🔊 **Beat sync** — background visuals pulse in time with your system audio
- 🔒 **Local only** — your data stays in a SQLite file on your PC

---

## 🧩 How it works

Neither WaveFlow nor Harmonoid exposes a public API, so Echoes taps into the **Windows System Media Transport Controls (SMTC)** — the same system that shows "Now Playing" in your volume flyout and taskbar.

```
┌───────────┐   SMTC    ┌────────────┐   HTTP    ┌───────────┐
│ WaveFlow  │ ────────▶ │ tracker.py │ ────────▶ │ server.py │
│ Harmonoid │           └────────────┘ (localhost)└───────────┘
└───────────┘                 │                         │
                              ▼                         ▼
                     echoes_stats.db        dashboard.html / mobile.html
                          (SQLite)         (served to browser / phone)
```

- **`tracker.py`** polls SMTC every couple of seconds, logs every play to a local SQLite database, and writes the current "now playing" state to a small JSON file.
- **`server.py`** is a lightweight local HTTP server that reads the database and serves the dashboard, stats API, album art (proxied from iTunes), lyrics (proxied from LRCLIB) and playback controls.
- **`config.py`** holds the player list, file paths and the database migration.

---

## 📋 Requirements

- Windows 10 or 11
- [Python 3.10+](https://www.python.org/downloads/) — tick **Add Python to PATH** when installing
- WaveFlow or Harmonoid
- Internet access, only for album art and lyrics

---

## 🚀 Installation

```bash
git clone https://github.com/<your-username>/echoes.git
cd echoes
pip install -r requirements.txt
```

---

## ▶️ Usage

Open two terminals in the project folder:

```bash
python tracker.py    # logs what you play
python server.py     # serves the dashboard
```

Open **http://localhost:8765** in your browser.

### 📱 Phone remote

Use the address `server.py` prints, for example `http://192.168.x.x:8765/mobile`. The phone must be on the same WiFi. If it can't connect, allow inbound TCP port **8765** in Windows Firewall.

---

## 🌙 Run silently on startup

Create two Task Scheduler tasks with the trigger **At log on**:

| Task | Program | Arguments |
|------|---------|-----------|
| Echoes tracker | `wscript.exe` | `"C:\path\to\echoes\start_tracker_silent.vbs"` |
| Echoes server | `wscript.exe` | `"C:\path\to\echoes\start_server_silent.vbs"` |

Set **Start in** to the project folder. If Python isn't on PATH for the task, edit the `.vbs` files to use the full path to `python.exe`.

---

## 🔎 WaveFlow not detected?

```bash
python tracker.py --discover
```

Play a song in WaveFlow. This prints every media app Windows can see. Add part of WaveFlow's app id to `PLAYER_MATCHES` in `config.py`.

---

## 🔄 Migrating from Harmonoid Wrapped

On first start, `harmonoid_stats.db` is copied to `echoes_stats.db`. The original is never modified, and old plays keep the source `harmonoid`.

## 🧹 Reset your stats

Stop both programs, then run `python reset_stats.py`.

---

## 🗂️ Project layout

| File | Purpose |
|------|---------|
| `tracker.py` | Reads Windows media sessions and logs plays |
| `server.py` | Local web server and API |
| `config.py` | Player list, paths, database migration |
| `dashboard.html` | Desktop dashboard |
| `mobile.html` | Phone remote |
| `reset_stats.py` | Clears your listening history |
| `seed_demo.py` | Fills a demo database for screenshots |

---

## 🔐 Privacy

Everything runs on your machine. The server listens on your local network so your phone can reach it, so don't expose port 8765 to the internet.

## ⚠️ Notes

- Seeking from the phone depends on the player honouring Windows seek commands.
- Only plays longer than 10 seconds are counted.
- Add `*.db`, `now_playing.json` and `artwork_cache/` to `.gitignore` so your history isn't published.
