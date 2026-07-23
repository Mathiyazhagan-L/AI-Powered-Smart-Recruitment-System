"""
migrate_auth.py — Safe ALTER TABLE migration for auth system upgrade.

Adds 3 new columns to the `users` table:
  - password_hash  VARCHAR(255) NULL
  - is_verified    TINYINT(1)   NOT NULL DEFAULT 0
  - auth_provider  VARCHAR(20)  NOT NULL DEFAULT 'email'

Safe to run multiple times — checks for column existence before adding.

Usage:
  cd c:\\Recruitment\\backend
  python migrate_auth.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from core.database import get_engine


def column_exists(conn, table: str, column: str) -> bool:
    """Return True if a column already exists in the given table."""
    result = conn.execute(
        text(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = :table "
            "AND COLUMN_NAME = :column"
        ),
        {"table": table, "column": column}
    )
    return result.scalar() > 0


def run_migration():
    engine = get_engine()

    migrations = [
        {
            "column": "password_hash",
            "sql": (
                "ALTER TABLE users "
                "ADD COLUMN password_hash VARCHAR(255) NULL "
                "AFTER phone_verified"
            ),
        },
        {
            "column": "is_verified",
            "sql": (
                "ALTER TABLE users "
                "ADD COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0 "
                "AFTER password_hash"
            ),
        },
        {
            "column": "auth_provider",
            "sql": (
                "ALTER TABLE users "
                "ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'email' "
                "AFTER is_verified"
            ),
        },
    ]

    with engine.connect() as conn:
        for m in migrations:
            col = m["column"]
            if column_exists(conn, "users", col):
                print(f"  [OK] Column '{col}' already exists - skipping.")
            else:
                print(f"  + Adding column '{col}'...")
                conn.execute(text(m["sql"]))
                conn.commit()
                print(f"    -> Done.")

        # Back-fill existing rows: mark them as verified email-login accounts
        print("\n  Backfilling auth_provider for existing rows...")
        conn.execute(
            text(
                "UPDATE users SET auth_provider = 'email' "
                "WHERE auth_provider IS NULL OR auth_provider = ''"
            )
        )

        print("  Backfilling is_verified for existing verified users...")
        conn.execute(
            text(
                "UPDATE users SET is_verified = 1 "
                "WHERE email_verified = 1 AND is_verified = 0"
            )
        )

        conn.commit()
        print("\nMigration complete.")


if __name__ == "__main__":
    print("Running auth migration...")
    run_migration()
