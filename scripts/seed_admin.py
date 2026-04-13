"""CLI untuk buat admin user pertama.

Usage:
    python scripts/seed_admin.py
"""
from __future__ import annotations

import getpass
import sys
from datetime import datetime, timezone

from passlib.hash import bcrypt

from app.database.connection import _get_session_factory
from app.database.models import Admin


def main() -> int:
    print("=== Seed Admin User ===")
    username = input("Username: ").strip()
    if not username:
        print("Username wajib diisi.", file=sys.stderr)
        return 1

    email = input("Email: ").strip()
    full_name = input("Nama Lengkap: ").strip()
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Ulangi Password: ")

    if password != password2:
        print("Password tidak cocok.", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Password minimal 8 karakter.", file=sys.stderr)
        return 1

    session_factory = _get_session_factory()
    db = session_factory()
    try:
        existing = db.query(Admin).filter_by(username=username).first()
        if existing:
            print(f"Admin '{username}' sudah ada.", file=sys.stderr)
            return 1

        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=bcrypt.using(rounds=12).hash(password),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        print(f"OK — admin '{username}' berhasil dibuat.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
