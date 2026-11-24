"""
Shared settings for Echoes (formerly "Harmonoid Wrapped").
Change APP_NAME here to rename the whole app (dashboard, phone remote, console).
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

APP_NAME = "Echoes"
BASE_DIR = Path(__file__).parent

# Any SMTC session whose app id contains one of these (case-insensitive) is tracked.
# Run `python tracker.py --discover` while playing to see the exact ids on your PC.
PLAYER_MATCHES = ["waveflow", "harmonoid"]

DB_PATH     = BASE_DIR / "echoes_stats.db"
LEGACY_DB   = BASE_DIR / "harmonoid_stats.db"      # old name - never modified or deleted
NOW_PATH    = BASE_DIR / "now_playing.json"
ARTWORK_DIR = BASE_DIR / "artwork_cache"
PORT        = 8765


def migrate_legacy_db():
    """If the old Harmonoid DB exists and the new one doesn't, make a safe copy.
    The original file is opened read-only and left untouched. Old rows keep
    source='harmonoid'."""
    if DB_PATH.exists() or not LEGACY_DB.exists():
        return False
    src = sqlite3.connect(f"file:{LEGACY_DB.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(DB_PATH)
    try:
        src.backup(dst)           # consistent copy even if the old tracker is running
        dst.commit()
    finally:
        src.close(); dst.close()
    print(f"[MIGRATE] Copied your existing stats {LEGACY_DB.name} -> {DB_PATH.name} (original kept as backup)")
    return True


def ensure_schema():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            artist     TEXT,
            album      TEXT,
            started_at TEXT NOT NULL,
            ended_at   TEXT,
            duration_s INTEGER DEFAULT 0,
            source     TEXT DEFAULT 'harmonoid'
        )""")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(plays)")]
    if "source" not in cols:
        conn.execute("ALTER TABLE plays ADD COLUMN source TEXT DEFAULT 'harmonoid'")
    conn.commit(); conn.close()


def write_json_atomic(path, data):
    """Write to a temp file then swap it in, so readers never see a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=str(Path(path).parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        for _ in range(5):
            try:
                os.replace(tmp, path); return True
            except PermissionError:
                import time; time.sleep(0.02)
    except Exception:
        pass
    try: os.unlink(tmp)
    except Exception: pass
    return False
