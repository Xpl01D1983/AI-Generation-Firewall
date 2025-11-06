"""Tripwire-style file integrity monitoring."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import TripwireConfig
from .logging import QuantumLogger


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class IntegrityMonitor:
    config: TripwireConfig
    logger: QuantumLogger
    stop_event: threading.Event = field(default_factory=threading.Event)

    def _walk_paths(self):
        for entry in self.config.paths:
            path = Path(entry)
            if path.is_file():
                yield path
            elif path.is_dir():
                for root, _, files in os.walk(path):
                    for file in files:
                        yield Path(root) / file

    def baseline(self) -> None:
        for path in self._walk_paths():
            try:
                stat = path.stat()
                file_hash = hash_file(path)
                self.logger.create_file_record(
                    str(path),
                    file_hash,
                    stat.st_size,
                    oct(stat.st_mode & 0o777),
                    datetime.fromtimestamp(stat.st_mtime).isoformat(),
                )
            except (FileNotFoundError, PermissionError):
                continue
        self.logger.log_system_event("TRIPWIRE_BASELINE", "Baseline created", "INFO")

    def watch(self) -> None:
        self.logger.log_system_event("TRIPWIRE_MONITOR", "File monitoring loop started", "INFO")
        while not self.stop_event.is_set():
            for path in self._walk_paths():
                try:
                    stat = path.stat()
                    current_hash = hash_file(path)
                    record = self.logger.fetch_file_baseline(str(path))
                    if record:
                        baseline_hash, last_hash = record
                        if current_hash != baseline_hash and current_hash != last_hash:
                            self.logger.log_system_event(
                                "FILE_MODIFIED",
                                f"{path} hash drift detected",
                                "CRITICAL",
                            )
                            self.logger.update_file_hash(
                                str(path),
                                current_hash,
                                stat.st_size,
                                oct(stat.st_mode & 0o777),
                                datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            )
                    else:
                        self.logger.create_file_record(
                            str(path),
                            current_hash,
                            stat.st_size,
                            oct(stat.st_mode & 0o777),
                            datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        )
                except (FileNotFoundError, PermissionError):
                    continue
            time.sleep(max(self.config.scan_interval_seconds, 10))

    def start_in_thread(self) -> threading.Thread:
        thread = threading.Thread(target=self.watch, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self.stop_event.set()
