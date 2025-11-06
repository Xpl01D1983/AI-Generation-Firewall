"""Configuration models for Quantum Defense Matrix."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DatastoreConfig(BaseModel):
    path: str = Field(default="/var/lib/quantum-defense/quantum_intel.db")


class FirewallConfig(BaseModel):
    enabled: bool = True
    adapter: str = Field(default="iptables")
    block_ports: List[int] = Field(default_factory=lambda: [4444, 5555, 6666, 1337, 31337, 12345, 54321])
    drop_score_threshold: int = Field(default=70)


class TripwireConfig(BaseModel):
    enabled: bool = True
    paths: List[str] = Field(
        default_factory=lambda: [
            "/bin",
            "/sbin",
            "/usr/bin",
            "/usr/sbin",
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "/root",
        ]
    )
    scan_interval_seconds: int = Field(default=60)


class HoneypotPort(BaseModel):
    port: int
    protocol: str = Field(default="tcp")
    handler: str = Field(default="ssh")


class HoneypotConfig(BaseModel):
    enabled: bool = True
    listeners: List[HoneypotPort] = Field(
        default_factory=lambda: [
            HoneypotPort(port=2222, handler="ssh"),
            HoneypotPort(port=8080, handler="http"),
        ]
    )


class ThreatFeedConfig(BaseModel):
    urls: List[str] = Field(
        default_factory=lambda: [
            "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
            "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
        ]
    )
    update_interval_seconds: int = Field(default=3600)


class AutoUpdateConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=24 * 3600)


class MonitoringConfig(BaseModel):
    enabled: bool = True
    poll_interval_seconds: int = Field(default=30)


class ModuleConfig(BaseModel):
    firewall: FirewallConfig = Field(default_factory=FirewallConfig)
    tripwire: TripwireConfig = Field(default_factory=TripwireConfig)
    honeypot: HoneypotConfig = Field(default_factory=HoneypotConfig)
    threat_intel: ThreatFeedConfig = Field(default_factory=ThreatFeedConfig)
    auto_update: AutoUpdateConfig = Field(default_factory=AutoUpdateConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


class QuantumDefenseConfig(BaseModel):
    defense_mode: str = Field(default="QUANTUM_REAL_TIME")
    ai_intelligence: str = Field(default="ADAPTIVE_NEURAL")
    datastore: DatastoreConfig = Field(default_factory=DatastoreConfig)
    modules: ModuleConfig = Field(default_factory=ModuleConfig)
    log_path: Optional[str] = Field(default=None)


def load_config(path: str) -> QuantumDefenseConfig:
    """Load configuration from a YAML file."""

    import yaml

    with open(path, "r", encoding="utf-8") as handler:
        data = yaml.safe_load(handler) or {}
    return QuantumDefenseConfig.model_validate(data)
