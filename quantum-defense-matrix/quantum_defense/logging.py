"""SQLite-backed logging helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS threat_intel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT UNIQUE,
        threat_type TEXT,
        risk_score INTEGER,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        attack_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS file_integrity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        file_hash TEXT,
        file_size INTEGER,
        permissions TEXT,
        last_modified TIMESTAMP,
        baseline_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS attack_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker_ip TEXT,
        attack_type TEXT,
        target_service TEXT,
        payload TEXT,
        risk_score INTEGER,
        response_action TEXT,
        timestamp TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS system_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        event_data TEXT,
        severity TEXT,
        timestamp TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


@dataclass
class QuantumLogger:
    """Persist events to SQLite."""

    db_path: Path

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    def log_system_event(self, event_type: str, data: str, severity: str = "INFO") -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO system_events (event_type, event_data, severity, timestamp)
                VALUES (?, ?, ?, ?)""",
                (event_type, data, severity, datetime.utcnow().isoformat()),
            )

    def log_attack_event(
        self,
        attacker_ip: str,
        attack_type: str,
        service: str,
        payload: str,
        risk_score: int,
        response_action: str = "logged",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO attack_events
                (attacker_ip, attack_type, target_service, payload, risk_score, response_action, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    attacker_ip,
                    attack_type,
                    service,
                    payload,
                    risk_score,
                    response_action,
                    datetime.utcnow().isoformat(),
                ),
            )

    def upsert_threat_indicator(self, ip_address: str, threat_type: str, risk_score: int) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO threat_intel
                (ip_address, threat_type, risk_score, first_seen, last_seen, attack_count)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(ip_address) DO UPDATE SET
                    threat_type=excluded.threat_type,
                    risk_score=excluded.risk_score,
                    last_seen=excluded.last_seen,
                    attack_count=threat_intel.attack_count + 1
                """,
                (ip_address, threat_type, risk_score, now, now, now),
            )

    def upsert_file_baseline(
        self, path: str, file_hash: str, size: int, permissions: str, modified: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO file_integrity
                (file_path, file_hash, file_size, permissions, last_modified, baseline_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_hash=excluded.file_hash,
                    file_size=excluded.file_size,
                    permissions=excluded.permissions,
                    last_modified=excluded.last_modified
                """,
                (path, file_hash, size, permissions, modified, file_hash),
            )

    def fetch_file_baseline(self, path: str) -> tuple[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT baseline_hash, file_hash FROM file_integrity WHERE file_path=?",
                (path,),
            ).fetchone()
        if not row:
            return None
        return row[0], row[1]

    def update_file_hash(
        self, path: str, file_hash: str, size: int, permissions: str, modified: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE file_integrity SET
                file_hash=?, file_size=?, permissions=?, last_modified=?
                WHERE file_path=?""",
                (file_hash, size, permissions, modified, path),
            )

    def create_file_record(
        self, path: str, file_hash: str, size: int, permissions: str, modified: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO file_integrity
                (file_path, file_hash, file_size, permissions, last_modified, baseline_hash)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (path, file_hash, size, permissions, modified, file_hash),
            )

    def fetch_high_risk_ips(self, threshold: int) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT ip_address FROM threat_intel WHERE risk_score>=?",
                (threshold,),
            ).fetchall()
        return [row[0] for row in rows]
