#!/usr/bin/env python3
"""Create or verify the production demo admin user in Neon/Postgres."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.base import engine, normalize_database_url
from app.db.init_db import DEMO_USER_EMAIL, DEMO_USER_PASSWORD, ensure_demo_user, init_database
from app.config import get_settings


async def main() -> int:
    settings = get_settings()
    print(f"Database: {normalize_database_url(settings.database_url).split('@')[-1]}")
    print(f"Creating demo user: {DEMO_USER_EMAIL}")

    try:
        await init_database()
        user = await ensure_demo_user()
        print(f"✓ User ready: {user.email} (id={user.id}, role={user.role})")
        print(f"  Password: {DEMO_USER_PASSWORD}")
        return 0
    except Exception as exc:
        print(f"✗ Failed: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
