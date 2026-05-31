import sqlite3
import os
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tts.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tts_records (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            text TEXT NOT NULL,
            preset_id TEXT,
            reference_audio TEXT,
            output_audio TEXT NOT NULL,
            duration REAL,
            params TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_tts_created ON tts_records(created_at DESC);
    """)
    conn.commit()
    conn.close()


def save_record(id, type, text, output_audio, duration=None, preset_id=None, reference_audio=None, params=None):
    conn = _connect()
    conn.execute(
        "INSERT INTO tts_records (id, type, text, preset_id, reference_audio, output_audio, duration, params) VALUES (?,?,?,?,?,?,?,?)",
        (id, type, text, preset_id, reference_audio, output_audio, duration, params),
    )
    conn.commit()
    conn.close()


def get_history(page=1, per_page=20):
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM tts_records").fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM tts_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    ).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "total": total}


def get_record(id):
    conn = _connect()
    row = conn.execute("SELECT * FROM tts_records WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_record(id):
    conn = _connect()
    conn.execute("DELETE FROM tts_records WHERE id = ?", (id,))
    conn.commit()
    conn.close()


def cleanup_old_records(hours=24):
    conn = _connect()
    cutoff = datetime.now().replace(microsecond=0)
    from datetime import timedelta
    cutoff = (cutoff - timedelta(hours=hours)).isoformat()
    rows = conn.execute("SELECT id, output_audio FROM tts_records WHERE created_at < ?", (cutoff,)).fetchall()
    for r in rows:
        path = r["output_audio"]
        if os.path.exists(path):
            os.remove(path)
        if r["reference_audio"] and os.path.exists(r["reference_audio"]):
            os.remove(r["reference_audio"])
    conn.execute("DELETE FROM tts_records WHERE created_at < ?", (cutoff,))
    conn.commit()
    print(f"[cleanup] removed {len(rows)} old records")
    conn.close()
