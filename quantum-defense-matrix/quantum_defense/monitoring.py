"""System monitoring utilities."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import psutil

from .config import MonitoringConfig
from .logging import QuantumLogger


@dataclass
class MonitoringEngine:
    config: MonitoringConfig
    logger: QuantumLogger
    stop_event: threading.Event = field(default_factory=threading.Event)

    def poll(self) -> None:
        while not self.stop_event.is_set():
            self.monitor_network()
            self.monitor_processes()
            self.monitor_resources()
            time.sleep(max(self.config.poll_interval_seconds, 10))

    def monitor_network(self) -> None:
        suspicious_ports = {4444, 5555, 6666, 1337}
        for conn in psutil.net_connections(kind="inet"):
            try:
                if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                    if conn.raddr.port in suspicious_ports:
                        ip = conn.raddr.ip
                        self.logger.log_attack_event(
                            ip,
                            "network",
                            "monitor",
                            f"Suspicious connection to port {conn.raddr.port}",
                            70,
                        )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    def monitor_processes(self) -> None:
        indicators = ["bash -i", "nc -e", "/bin/sh", "socket.socket"]
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if any(indicator in cmdline for indicator in indicators):
                    self.logger.log_system_event(
                        "REVERSE_SHELL",
                        f"Process {proc.info['pid']} suspicious command: {cmdline}",
                        "CRITICAL",
                    )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    def monitor_resources(self) -> None:
        cpu = psutil.cpu_percent(interval=None)
        if cpu > 90:
            self.logger.log_system_event("HIGH_CPU", f"CPU usage at {cpu}%", "WARNING")
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            self.logger.log_system_event("HIGH_MEMORY", f"Memory usage at {memory.percent}%", "WARNING")

    def start_in_thread(self) -> threading.Thread:
        thread = threading.Thread(target=self.poll, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self.stop_event.set()
