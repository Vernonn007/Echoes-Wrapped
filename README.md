# Echoes (formerly Harmonoid Wrapped)

Local listening stats, a Wrapped recap, a live dashboard and a phone remote. Tracks **WaveFlow** and **Harmonoid** through Windows' media controls (SMTC). Everything stays on your PC.

## Setup
1. `pip install -r requirements.txt`
2. Start the tracker: `python tracker.py` (or `start_tracker_silent.vbs` for hidden)
3. Start the server: `python server.py` (or `start_server_silent.vbs`)
4. Open http://localhost:8765. Phone: http://YOUR-PC-IP:8765/mobile

## Keeping your old data
On first start, `harmonoid_stats.db` is copied to `echoes_stats.db`. The original is never changed; keep it as a backup. Old plays stay labelled `harmonoid`.

## WaveFlow not detected?
Run `python tracker.py --discover` while WaveFlow plays. Copy the app id it prints and add a distinctive part of it to `PLAYER_MATCHES` in `config.py`.

## Rename
Change `APP_NAME` in `config.py`.

## Startup (Task Scheduler)
Two tasks at log on: `pythonw.exe tracker.py` and `pythonw.exe server.py`, with "Start in" set to this folder. Delete the old Harmonoid tasks.
