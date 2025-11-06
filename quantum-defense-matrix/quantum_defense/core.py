"""Core orchestrator for Quantum Defense Matrix."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from .config import QuantumDefenseConfig
from .firewall import FirewallEngine
from .honeypot import HoneypotListener
from .intelligence import ThreatIntelEngine
from .logging import QuantumLogger
from .monitoring import MonitoringEngine
from .integrity import IntegrityMonitor


console = Console()


@dataclass
class QuantumDefenseService:
    config: QuantumDefenseConfig
    logger: QuantumLogger | None = None
    threads: list[threading.Thread] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.logger:
            db_path = Path(self.config.datastore.path)
            self.logger = QuantumLogger(db_path=db_path)
        console.print("[bold magenta]Quantum Defense Matrix initializing...[/bold magenta]")

    def start(self) -> None:
        console.print("[cyan]Launching modules...[/cyan]")
        self.logger.log_system_event("SYSTEM_START", "Quantum Defense Matrix starting")

        if self.config.modules.firewall.enabled:
            firewall = FirewallEngine(config=self.config.modules.firewall, logger=self.logger)
            firewall.bootstrap()
            ips = self.logger.fetch_high_risk_ips(
                self.config.modules.firewall.drop_score_threshold
            )
            firewall.sync_threats(ips)

        if self.config.modules.tripwire.enabled:
            monitor = IntegrityMonitor(config=self.config.modules.tripwire, logger=self.logger)
            monitor.baseline()
            self.threads.append(monitor.start_in_thread())

        if self.config.modules.honeypot.enabled:
            honeypot = HoneypotListener(config=self.config.modules.honeypot, logger=self.logger)
            honeypot.start()

        if self.config.modules.threat_intel.update_interval_seconds > 0:
            intel = ThreatIntelEngine(config=self.config.modules.threat_intel, logger=self.logger)
            self.threads.append(intel.start_in_thread())

        if self.config.modules.monitoring.enabled:
            monitoring = MonitoringEngine(config=self.config.modules.monitoring, logger=self.logger)
            self.threads.append(monitoring.start_in_thread())

        if self.config.modules.auto_update.enabled:
            thread = threading.Thread(target=self._auto_update_loop, daemon=True)
            thread.start()
            self.threads.append(thread)

        console.print("[green]Quantum Defense Matrix operational.[/green]")

    def _auto_update_loop(self) -> None:
        self.logger.log_system_event("AUT0_UPDATE", "Auto-update loop initialized", "INFO")
        while True:
            time.sleep(max(self.config.modules.auto_update.interval_seconds, 3600))
            self.logger.log_system_event("UPDATE_CHECK", "Auto-update triggered", "INFO")

    def run_forever(self) -> None:
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]\nShutting down Quantum Defense Matrix...[/yellow]")
