# -*- coding: utf-8 -*-
"""طبقة تخزين SQLite للنسخة المحلية من منصة ملف العائلة القانونية."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("family_legal_case.sqlite3")


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)


def load_case(case_id=1):
    init_db()
    with connect() as connection:
        row = connection.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
    return json.loads(row["payload"]) if row else None


def save_case(case):
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as connection:
        connection.execute(
            """INSERT INTO cases(id, title, owner, status, payload, updated_at)
               VALUES(?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET title=excluded.title,
               owner=excluded.owner, status=excluded.status,
               payload=excluded.payload, updated_at=excluded.updated_at""",
            (case.get("id", 1), case.get("title", ""), case.get("owner", ""),
             case.get("status", ""), json.dumps(case, ensure_ascii=False), now),
        )


def append_audit(case_id, action, detail=""):
    init_db()
    with connect() as connection:
        connection.execute(
            "INSERT INTO audit_log(case_id, action, detail, created_at) VALUES(?, ?, ?, ?)",
            (case_id, action, detail, datetime.now().isoformat(timespec="seconds")),
        )


def list_cases():
    init_db()
    with connect() as connection:
        return connection.execute(
            "SELECT id, title, owner, status, updated_at FROM cases ORDER BY updated_at DESC"
        ).fetchall()
