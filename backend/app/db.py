"""SQLite layer (stdlib sqlite3). One short-lived connection per request."""
import sqlite3
from contextlib import contextmanager
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  member_no TEXT,
  society_name TEXT,
  preferred_language TEXT NOT NULL DEFAULT 'hi',
  rfid_uid TEXT UNIQUE,
  fingerprint_id INTEGER UNIQUE,
  phone TEXT,
  address TEXT,
  profession TEXT,
  land_owned INTEGER,
  land_area TEXT,
  pending_schemes TEXT NOT NULL DEFAULT '[]',
  registration_status TEXT NOT NULL DEFAULT 'approved',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), method TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'en', created_at TEXT NOT NULL DEFAULT (datetime('now')), expires_at TEXT NOT NULL, ended_at TEXT
);
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_token TEXT NOT NULL REFERENCES sessions(token), user_id INTEGER,
  kind TEXT NOT NULL, language TEXT NOT NULL, question TEXT, question_en TEXT, answer TEXT, payload TEXT, mode TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS complaints (
  id INTEGER PRIMARY KEY AUTOINCREMENT, reference TEXT NOT NULL UNIQUE, user_id INTEGER, session_token TEXT,
  category TEXT NOT NULL, society_type TEXT NOT NULL DEFAULT 'unknown', member_name TEXT, society_name TEXT, member_no TEXT,
  details TEXT, language TEXT NOT NULL DEFAULT 'en', letter_text TEXT, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS scanned_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, session_token TEXT, filename TEXT, file_path TEXT, language TEXT, text TEXT, ocr_engine TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS system_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, source TEXT NOT NULL, message TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE INDEX IF NOT EXISTS ix_conv_session ON conversations(session_token);
CREATE INDEX IF NOT EXISTS ix_conv_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS ix_complaints_user ON complaints(user_id);
"""


def connect():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn; conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def db_dep():
    with get_conn() as conn: yield conn

def _add_column(conn, table, column, definition):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols: conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def init_db(seed_demo: bool = True):
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        for name, definition in [
            ("phone", "TEXT"), ("address", "TEXT"), ("profession", "TEXT"), ("land_owned", "INTEGER"),
            ("land_area", "TEXT"), ("pending_schemes", "TEXT NOT NULL DEFAULT '[]'"),
            ("registration_status", "TEXT NOT NULL DEFAULT 'approved'")]: _add_column(conn, "users", name, definition)
        if seed_demo and conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO users(name, member_no, society_name, preferred_language, rfid_uid, fingerprint_id, profession, land_owned, land_area, pending_schemes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                [("Ramesh Kumar (demo)", "42", "Sunrise PACS", "hi", "DEMO0001", 1, "Farmer", 1, "2 acres", "[]"),
                 ("Sunita Devi (demo)", "108", "Gram Dairy Society", "hi", "DEMO0002", 2, "Dairy", 0, None, "[]")])

def log_event(conn, level: str, source: str, message: str, detail: str | None = None):
    conn.execute("INSERT INTO system_logs(level, source, message, detail) VALUES (?,?,?,?)", (level, source, message, detail))