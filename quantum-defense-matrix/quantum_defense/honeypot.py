"""Minimal honeypot listeners."""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass

from .config import HoneypotConfig, HoneypotPort
from .logging import QuantumLogger


@dataclass
class HoneypotListener:
    config: HoneypotConfig
    logger: QuantumLogger
    threads: list[threading.Thread] = None

    def __post_init__(self) -> None:
        self.threads = []

    def start(self) -> None:
        for listener in self.config.listeners:
            thread = threading.Thread(target=self._serve, args=(listener,), daemon=True)
            thread.start()
            self.threads.append(thread)
        self.logger.log_system_event(
            "HONEYPOT_START",
            f"Started {len(self.config.listeners)} honeypot listeners",
            "INFO",
        )

    def _serve(self, listener: HoneypotPort) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", listener.port))
            sock.listen(5)
        except OSError as exc:
            self.logger.log_system_event(
                "HONEYPOT_ERROR",
                f"Failed to bind {listener.port}: {exc}",
                "WARNING",
            )
            return

        while True:
            try:
                client, addr = sock.accept()
            except OSError:
                break
            thread = threading.Thread(
                target=self._handle_client, args=(client, addr, listener.handler), daemon=True
            )
            thread.start()

    def _handle_client(self, client: socket.socket, addr, handler: str) -> None:
        ip, _ = addr
        if handler == "ssh":
            banner = b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n"
            client.send(banner)
            data = client.recv(1024)
            text = data.decode("utf-8", errors="ignore") if data else ""
            self.logger.log_attack_event(ip, "ssh", "honeypot", text, 60)
            client.send(b"Permission denied, please try again.\r\n")
        elif handler == "http":
            request = client.recv(4096).decode("utf-8", errors="ignore")
            self.logger.log_attack_event(ip, "http", "honeypot", request[:200], 40)
            response = (
                "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                "<html><body><h1>Admin Portal</h1></body></html>"
            )
            client.send(response.encode())
        else:
            data = client.recv(1024)
            text = data.decode("utf-8", errors="ignore") if data else ""
            self.logger.log_attack_event(ip, handler, "honeypot", text, 30)

        client.close()
