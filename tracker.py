"""
Echoes - Windows SMTC tracker (WaveFlow + Harmonoid)
Install: pip install -r requirements.txt
Run:     python tracker.py            (normal)
         python tracker.py --discover (print every media app Windows can see)
"""
import asyncio
import ctypes
import sqlite3
import sys
from datetime import datetime

import config
from config import DB_PATH, NOW_PATH, APP_NAME, PLAYER_MATCHES

POLL_INTERVAL    = 2      # seconds
MIN_PLAY_SECONDS = 10
GRACE_POLLS      = 3      # polls a vanished/odd state is tolerated before we call it "stopped"


def single_instance():
    """Stop a second tracker from fighting the first one over the DB and now_playing.json."""
    try:
        h = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\EchoesTrackerMutex")
        if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            print("[TRACKER] Another tracker is already running - exiting.")
            sys.exit(0)
        return h
    except AttributeError:
        return None   # not Windows


def save_play(title, artist, album, started_at, ended_at, duration_s, source):
    if duration_s < MIN_PLAY_SECONDS:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO plays (title,artist,album,started_at,ended_at,duration_s,source) VALUES (?,?,?,?,?,?,?)",
        (title, artist, album, started_at.isoformat(), ended_at.isoformat(), int(duration_s), source))
    conn.commit(); conn.close()
    m, s = divmod(int(duration_s), 60)
    print(f"[LOG] {artist} - {title}  ({m}m {s}s) [{source}]")


def player_name(app_id):
    a = (app_id or "").lower()
    for m in PLAYER_MATCHES:
        if m in a:
            return m
    return None


def secs(v):
    if v is None: return 0.0
    try: return float(v.total_seconds())
    except Exception:
        try: return float(v) / 1e7
        except Exception: return 0.0


async def run(discover=False):
    try:
        from winrt.windows.media.control import \
            GlobalSystemMediaTransportControlsSessionManager as SessionManager
        from winrt.windows.media.control import \
            GlobalSystemMediaTransportControlsSessionPlaybackStatus as PS
    except ImportError:
        print("[ERROR] winrt packages missing. Run: pip install -r requirements.txt")
        sys.exit(1)

    manager = await SessionManager.request_async()

    if discover:
        print("[DISCOVER] Play something in WaveFlow, then watch this list. Ctrl+C to stop.\n")
        seen = set()
        while True:
            for s in manager.get_sessions():
                aid = s.source_app_user_model_id
                try:
                    info = await s.try_get_media_properties_async()
                    t = f"{info.artist} - {info.title}"
                except Exception:
                    t = "?"
                line = f"{aid}  |  {t}"
                if line not in seen:
                    seen.add(line); print("[APP]", line)
            await asyncio.sleep(2)

    print(f"[TRACKER] {APP_NAME} running - watching: {', '.join(PLAYER_MATCHES)}")
    print("[TRACKER] Ctrl+C to stop.\n")

    cur = None            # dict of the play in progress: title, artist, album, start, source
    last = {"title": None, "artist": None}
    shown = {}            # last good display payload (kept while paused / during blips)
    miss = 0

    def finish(reason=""):
        nonlocal cur
        if cur:
            el = (datetime.now() - cur["start"]).total_seconds()
            save_play(cur["title"], cur["artist"], cur["album"], cur["start"], datetime.now(), el, cur["source"])
            last["title"], last["artist"] = cur["title"], cur["artist"]
        cur = None

    def publish(playing):
        d = dict(shown) if shown else {}
        d.update({
            "playing": bool(playing),
            "last_title": last["title"], "last_artist": last["artist"],
            "updated_at": datetime.now().isoformat(),
        })
        config.write_json_atomic(NOW_PATH, d)

    while True:
        try:
            sessions = [s for s in manager.get_sessions() if player_name(s.source_app_user_model_id)]
            # prefer a session that is actually playing
            chosen = None
            for s in sessions:
                pi = s.get_playback_info()
                if pi and pi.playback_status == PS.PLAYING:
                    chosen = s; break
            if chosen is None and sessions:
                chosen = sessions[0]

            info = None
            if chosen is not None:
                try: info = await chosen.try_get_media_properties_async()
                except Exception: info = None

            title = (info.title if info else "") or ""
            if chosen is None or info is None or not title:
                # Session vanished or metadata momentarily empty: do NOT flip state yet.
                miss += 1
                if miss >= GRACE_POLLS:
                    finish()
                    publish(False)
                elif shown:
                    publish(shown.get("playing", False))   # keep showing what we had
                await asyncio.sleep(POLL_INTERVAL)
                continue
            miss = 0

            artist = info.artist or "Unknown Artist"
            album  = info.album_title or ""
            src    = player_name(chosen.source_app_user_model_id)
            pi     = chosen.get_playback_info()
            playing = bool(pi and pi.playback_status == PS.PLAYING)

            pos = dur = 0.0
            try:
                tl = chosen.get_timeline_properties()
                if tl:
                    pos = secs(getattr(tl, "position", None))
                    dur = secs(getattr(tl, "end_time", None)) - secs(getattr(tl, "start_time", None))
                    if dur <= 0: dur = secs(getattr(tl, "max_seek_time", None))
                    if dur < 0 or dur > 6 * 3600: dur = 0.0
            except Exception:
                pass

            # track changed -> close previous play
            if cur and (cur["title"] != title or cur["artist"] != artist):
                finish()
            # paused -> close play so paused time isn't counted
            if cur and not playing:
                finish()
            # started playing a track
            if playing and not cur:
                cur = {"title": title, "artist": artist, "album": album,
                       "start": datetime.now(), "source": src}
                print(f"[NOW]  {artist} - {title} [{src}]")

            shown = {"title": title, "artist": artist, "album": album, "player": src,
                     "position_s": round(pos, 1), "duration_s": round(dur, 1)}
            publish(playing)
        except Exception as e:
            print(f"[WARN] {e}")
        await asyncio.sleep(POLL_INTERVAL)


def main():
    discover = "--discover" in sys.argv
    if not discover:
        single_instance()
    config.migrate_legacy_db()
    config.ensure_schema()
    try:
        asyncio.run(run(discover))
    except KeyboardInterrupt:
        print("\n[TRACKER] Stopped.")


if __name__ == "__main__":
    main()
