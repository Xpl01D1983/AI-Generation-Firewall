"""Firewall synchronization utilities."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Iterable, List

from .config import FirewallConfig
from .logging import QuantumLogger


@dataclass
class FirewallAdapter:
    command: str = "iptables"

    def reset_chain(self, chain: str) -> None:
        for cmd in (
            [self.command, "-F", chain],
            [self.command, "-X", chain],
            [self.command, "-N", chain],
        ):
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def attach_chain(self, chain: str) -> None:
        for table in ("INPUT", "FORWARD"):
            subprocess.run(
                [self.command, "-C", table, "-j", chain],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            subprocess.run(
                [self.command, "-I", table, "1", "-j", chain],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    def allow_established(self, chain: str) -> None:
        subprocess.run(
            [self.command, "-A", chain, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            [self.command, "-A", chain, "-i", "lo", "-j", "ACCEPT"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def block_port(self, chain: str, port: int) -> None:
        for proto in ("tcp", "udp"):
            subprocess.run(
                [self.command, "-A", chain, "-p", proto, "--dport", str(port), "-j", "DROP"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    def block_ip(self, chain: str, ip_address: str) -> None:
        subprocess.run(
            [self.command, "-A", chain, "-s", ip_address, "-j", "DROP"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


@dataclass
class FirewallEngine:
    config: FirewallConfig
    logger: QuantumLogger
    adapter: FirewallAdapter = FirewallAdapter()
    chain_name: str = "QUANTUM_FW"

    def bootstrap(self) -> None:
        self.logger.log_system_event("FIREWALL_INIT", "Bootstrapping firewall chain")
        self.adapter.reset_chain(self.chain_name)
        self.adapter.attach_chain(self.chain_name)
        self.adapter.allow_established(self.chain_name)
        for port in self.config.block_ports:
            self.adapter.block_port(self.chain_name, port)
        self.logger.log_system_event("FIREWALL_READY", "Default rules applied")

    def sync_threats(self, ips: Iterable[str]) -> None:
        for ip in ips:
            self.adapter.block_ip(self.chain_name, ip)
        self.logger.log_system_event("FIREWALL_SYNC", f"Applied {len(list(ips))} threat IPs")
