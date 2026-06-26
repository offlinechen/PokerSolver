#!/usr/bin/env python3
"""Convenience script to run Alembic migrations.

Usage:
  python scripts/migrate.py upgrade   # apply all pending migrations
  python scripts/migrate.py downgrade # roll back one revision
  python scripts/migrate.py current   # show current revision
  python scripts/migrate.py history   # show migration history
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def run_migrations():
    """Run all pending alembic migrations against the configured database."""
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            # Create alembic_version table if not exists
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL PRIMARY KEY
                )
            """))
            # Check current version
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            current = row[0] if row else None
            print(f"Current DB revision: {current or 'none'}")

            if current != "001":
                # Apply the initial migration
                from alembic.versions import _001_initial_schema
                await conn.run_sync(_001_initial_schema.upgrade)
                await conn.execute(text("DELETE FROM alembic_version"))
                await conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
                    {"v": "001"},
                )
                await conn.commit()
                print("Migration 001 applied successfully.")
            else:
                print("Already at latest revision (001).")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migrations())
