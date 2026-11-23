#!/usr/bin/env python3
"""SQLite master-data API for SocietyPay.

Stores only master records:
- society settings
- apartments/flats
- residents/users

Expenses, dues, meters, bill attachments, and payment status remain in browser localStorage.
"""

from __future__ import annotations

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / os.getenv("SOCIETYPAY_DB", "societypay.sqlite3")
PORT = int(os.getenv("SOCIETYPAY_API_PORT", "4181"))


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS society_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                society_name TEXT NOT NULL DEFAULT 'SocietyPay',
                month_label TEXT NOT NULL DEFAULT '',
                flat_share REAL NOT NULL DEFAULT 0,
                opening_balance REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS apartments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flat_number TEXT NOT NULL UNIQUE,
                share_amount REAL NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartment_id INTEGER NOT NULL,
                resident_name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apartment_id) REFERENCES apartments(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_apartment ON users(apartment_id);
        """)
        db.execute("INSERT OR IGNORE INTO society_settings(id, society_name, month_label, flat_share, opening_balance) VALUES(1, 'SocietyPay', '', 0, 0)")


def apartment_records():
    with connect() as db:
        rows = db.execute("""
            SELECT a.id, a.flat_number, a.share_amount,
                   COALESCE(u.resident_name, '') AS resident_name,
                   a.active AS apartment_active
            FROM apartments a
            LEFT JOIN users u ON u.apartment_id = a.id AND u.active = 1
            WHERE a.active = 1
            ORDER BY a.flat_number
        """).fetchall()
    return [dict(row) for row in rows]


def settings_record():
    with connect() as db:
        row = db.execute("SELECT society_name, month_label, flat_share, opening_balance FROM society_settings WHERE id=1").fetchone()
    return dict(row) if row else {"society_name":"SocietyPay","month_label":"","flat_share":0,"opening_balance":0}


class Handler(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, DELETE, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def json_response(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.json_response(200, {"ok": True, "database": str(DB_PATH)})
            return
        if parsed.path == "/api/master":
            self.json_response(200, {"ok": True, "settings": settings_record(), "apartments": apartment_records()})
            return
        self.json_response(404, {"ok": False, "error": "Not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        try:
            body = self.read_json()
            if parsed.path == "/api/settings":
                society_name = str(body.get("societyName", "SocietyPay")).strip() or "SocietyPay"
                month_label = str(body.get("monthLabel", "")).strip()
                flat_share = max(0, float(body.get("flatShare", 0) or 0))
                opening_balance = float(body.get("openingBalance", 0) or 0)
                with connect() as db:
                    db.execute("""
                        UPDATE society_settings SET society_name=?, month_label=?, flat_share=?, opening_balance=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=1
                    """, (society_name, month_label, flat_share, opening_balance))
                    if flat_share:
                        db.execute("UPDATE apartments SET share_amount=?, updated_at=CURRENT_TIMESTAMP", (flat_share,))
                self.json_response(200, {"ok": True, "settings": settings_record()})
                return

            if parsed.path == "/api/apartments":
                flat_number = str(body.get("flatNumber", "")).strip()
                resident_name = str(body.get("residentName", "")).strip()
                share_amount = max(0, float(body.get("shareAmount", 0) or 0))
                apartment_id = body.get("id")
                if not flat_number or not resident_name:
                    self.json_response(400, {"ok": False, "error": "Flat number and resident name are required"})
                    return

                with connect() as db:
                    if apartment_id:
                        row = db.execute("SELECT id FROM apartments WHERE id=?", (apartment_id,)).fetchone()
                        if not row:
                            self.json_response(404, {"ok": False, "error": "Apartment not found"})
                            return
                        db.execute("UPDATE apartments SET flat_number=?, share_amount=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (flat_number, share_amount, apartment_id))
                        db.execute("UPDATE users SET resident_name=?, updated_at=CURRENT_TIMESTAMP WHERE apartment_id=? AND active=1", (resident_name, apartment_id))
                        if not db.execute("SELECT id FROM users WHERE apartment_id=? AND active=1", (apartment_id,)).fetchone():
                            db.execute("INSERT INTO users(apartment_id, resident_name) VALUES(?, ?)", (apartment_id, resident_name))
                    else:
                        existing = db.execute("SELECT id FROM apartments WHERE flat_number=?", (flat_number,)).fetchone()
                        if existing:
                            apartment_id = existing["id"]
                            db.execute("UPDATE apartments SET share_amount=?, active=1, updated_at=CURRENT_TIMESTAMP WHERE id=?", (share_amount, apartment_id))
                            db.execute("UPDATE users SET resident_name=?, active=1, updated_at=CURRENT_TIMESTAMP WHERE apartment_id=?", (resident_name, apartment_id))
                        else:
                            cursor = db.execute("INSERT INTO apartments(flat_number, share_amount) VALUES(?, ?)", (flat_number, share_amount))
                            apartment_id = cursor.lastrowid
                            db.execute("INSERT INTO users(apartment_id, resident_name) VALUES(?, ?)", (apartment_id, resident_name))

                self.json_response(200, {"ok": True, "apartments": apartment_records()})
                return

            self.json_response(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self.json_response(400, {"ok": False, "error": str(exc)})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/master":
                with connect() as db:
                    db.execute("DELETE FROM users")
                    db.execute("DELETE FROM apartments")
                    db.execute("UPDATE society_settings SET society_name='SocietyPay', month_label='', flat_share=0, opening_balance=0, updated_at=CURRENT_TIMESTAMP WHERE id=1")
                self.json_response(200, {"ok": True, "settings": settings_record(), "apartments": []})
                return

            apartment_id = parse_qs(parsed.query).get("id", [""])[0]
            if parsed.path != "/api/apartments" or not apartment_id:
                self.json_response(400, {"ok": False, "error": "Apartment id is required"})
                return
            with connect() as db:
                db.execute("UPDATE apartments SET active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?", (apartment_id,))
                db.execute("UPDATE users SET active=0, updated_at=CURRENT_TIMESTAMP WHERE apartment_id=?", (apartment_id,))
            self.json_response(200, {"ok": True, "apartments": apartment_records()})
        except Exception as exc:
            self.json_response(400, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"SQLite master-data API listening on http://127.0.0.1:{PORT}")
    print(f"Database: {DB_PATH}")
    server.serve_forever()
