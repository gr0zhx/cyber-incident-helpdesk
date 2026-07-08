"""Seed 4 dummy admin users untuk pengembangan/demo.

Usage:
    python scripts/seed_dummy_admins.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from passlib.hash import bcrypt

from app.database.connection import _get_session_factory
from app.database.models import Admin

DUMMY_ADMINS = [
    {"username": "admin1", "email": "admin1@pusdatin.go.id", "full_name": "Budi Santoso"},
    {"username": "admin2", "email": "admin2@pusdatin.go.id", "full_name": "Dewi Rahayu"},
    {"username": "admin3", "email": "admin3@pusdatin.go.id", "full_name": "Rudi Hermawan"},
    {"username": "admin4", "email": "admin4@pusdatin.go.id", "full_name": "Siti Aisyah"},
]
DEFAULT_PASSWORD = "admin1234"


def main() -> int:
    session_factory = _get_session_factory()
    db = session_factory()
    created = 0
    skipped = 0
    try:
        pw_hash = bcrypt.using(rounds=12).hash(DEFAULT_PASSWORD)
        for data in DUMMY_ADMINS:
            existing = db.query(Admin).filter_by(username=data["username"]).first()
            if existing:
                print(f"SKIP — '{data['username']}' sudah ada.")
                skipped += 1
                continue
            admin = Admin(
                username=data["username"],
                email=data["email"],
                full_name=data["full_name"],
                password_hash=pw_hash,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(admin)
            created += 1
            print(f"OK   — '{data['username']}' ({data['full_name']}) dibuat.")
        db.commit()
    finally:
        db.close()

    print(f"\nSelesai: {created} dibuat, {skipped} dilewati.")
    print(f"Password default: {DEFAULT_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
