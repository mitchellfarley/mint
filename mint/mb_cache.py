from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class MBCache:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS releases ("
            "  key TEXT PRIMARY KEY,"
            "  data TEXT NOT NULL,"
            "  fetched_at INTEGER NOT NULL"
            ")"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS covers ("
            "  release_id TEXT PRIMARY KEY,"
            "  blob BLOB NOT NULL,"
            "  fetched_at INTEGER NOT NULL"
            ")"
        )
        self.conn.commit()

    def get(self, key: str) -> Any | None:
        row = self.conn.execute(
            "SELECT data FROM releases WHERE key = ?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, key: str, data: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO releases (key, data, fetched_at) VALUES (?, ?, ?)",
            (key, json.dumps(data), int(time.time())),
        )
        self.conn.commit()

    def get_cover(self, release_id: str) -> bytes | None:
        row = self.conn.execute(
            "SELECT blob FROM covers WHERE release_id = ?", (release_id,)
        ).fetchone()
        return bytes(row[0]) if row else None

    def set_cover(self, release_id: str, blob: bytes) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO covers (release_id, blob, fetched_at) VALUES (?, ?, ?)",
            (release_id, blob, int(time.time())),
        )
        self.conn.commit()
