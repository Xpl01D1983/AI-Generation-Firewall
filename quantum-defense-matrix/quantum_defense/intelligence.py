"""Threat intelligence ingestion."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from threading import Event, Thread
from typing import Iterable

import requests

from .config import ThreatFeedConfig
from .logging import QuantumLogger


@dataclass
class ThreatIntelEngine:
    config: ThreatFeedConfig
    logger: QuantumLogger
    stop_event: Event = Event()

    def fetch_feeds(self) -> Iterable[tuple[str, str, int]]:
        for url in self.config.urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                for line in response.text.splitlines():
                    ip = line.strip()
                    if ip and not ip.startswith("#"):
                        threat_type = "feed"
                        risk_score = random.randint(60, 95)
                        yield ip, threat_type, risk_score
            except requests.RequestException:
                self.logger.log_system_event("THREAT_FEED_ERROR", f"Failed to fetch {url}", "WARNING")

    def update_once(self) -> int:
        count = 0
        for ip, threat_type, risk in self.fetch_feeds():
            self.logger.upsert_threat_indicator(ip, threat_type, risk)
            count += 1
        self.logger.log_system_event("THREAT_UPDATE", f"Ingested {count} indicators", "INFO")
        return count

    def run_forever(self) -> None:
        self.logger.log_system_event("THREAT_LOOP", "Threat intel loop started", "INFO")
        while not self.stop_event.is_set():
            self.update_once()
            time.sleep(max(self.config.update_interval_seconds, 300))

    def start_in_thread(self) -> Thread:
        thread = Thread(target=self.run_forever, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self.stop_event.set()
