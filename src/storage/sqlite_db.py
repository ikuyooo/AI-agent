from __future__ import annotations
import sqlite3, json, os
from contextlib import contextmanager
from src.core.config import SQLITE_DB_PATH

@contextmanager
def _conn():
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE NOT NULL, file_path TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                num_pages INTEGER DEFAULT 0, num_chunks INTEGER DEFAULT 0,
                section_confidence REAL DEFAULT 0.0);
            CREATE TABLE IF NOT EXISTS paper_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL, card_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)

def save_document(file_name, file_path, num_pages, num_chunks, confidence):
    with _conn() as c:
        c.execute("""INSERT INTO documents (file_name,file_path,num_pages,num_chunks,section_confidence)
            VALUES (?,?,?,?,?) ON CONFLICT(file_name) DO UPDATE SET
            num_pages=excluded.num_pages, num_chunks=excluded.num_chunks,
            section_confidence=excluded.section_confidence,
            uploaded_at=CURRENT_TIMESTAMP""",
            (file_name, file_path, num_pages, num_chunks, confidence))

def get_all_documents():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")]

def delete_document(file_name):
    with _conn() as c:
        c.execute("DELETE FROM documents WHERE file_name=?", (file_name,))
        c.execute("DELETE FROM paper_cards WHERE file_name=?", (file_name,))

def save_paper_card(file_name, card):
    with _conn() as c:
        c.execute("INSERT INTO paper_cards (file_name,card_json) VALUES (?,?)",
                  (file_name, json.dumps(card, ensure_ascii=False)))

def get_paper_card(file_name):
    with _conn() as c:
        row = c.execute("SELECT card_json FROM paper_cards WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
                        (file_name,)).fetchone()
    return json.loads(row["card_json"]) if row else None
