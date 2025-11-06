"""Typer CLI for Quantum Defense Matrix."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from .config import QuantumDefenseConfig, load_config
from .core import QuantumDefenseService
from .logging import QuantumLogger
from .intelligence import ThreatIntelEngine


app = typer.Typer(add_completion=False, help="Manage the Quantum Defense Matrix service")


def _load_config(path: Path | None) -> QuantumDefenseConfig:
    if path is None:
        raise typer.BadParameter("Configuration file path required")
    return load_config(str(path))


@app.command("run")
def run(config: Path = typer.Option(..., exists=True, readable=True, help="Path to config YAML")) -> None:
    """Run the defense service in the foreground."""

    cfg = _load_config(config)
    service = QuantumDefenseService(cfg)
    service.run_forever()


@app.command("update-feeds")
def update_feeds(
    config: Path = typer.Option(..., exists=True, readable=True, help="Path to config YAML"),
) -> None:
    """Perform a single threat intelligence refresh."""

    cfg = _load_config(config)
    logger = QuantumLogger(Path(cfg.datastore.path))
    engine = ThreatIntelEngine(cfg.modules.threat_intel, logger)
    count = engine.update_once()
    print(f"[green]Ingested {count} indicators[/green]")


@app.command("status")
def status(
    config: Path = typer.Option(..., exists=True, readable=True, help="Path to config YAML"),
) -> None:
    """Display a summary of stored indicators and recent events."""

    cfg = _load_config(config)
    logger = QuantumLogger(Path(cfg.datastore.path))
    with logger._connect() as conn:  # type: ignore[attr-defined]
        threats = conn.execute("SELECT COUNT(*) FROM threat_intel").fetchone()[0]
        attacks = conn.execute("SELECT COUNT(*) FROM attack_events").fetchone()[0]
        criticals = conn.execute(
            "SELECT COUNT(*) FROM system_events WHERE severity='CRITICAL'"
        ).fetchone()[0]
        print("[bold cyan]Quantum Defense Matrix[/bold cyan]")
        print(f"Threat indicators: [yellow]{threats}[/yellow]")
        print(f"Recorded attacks: [red]{attacks}[/red]")
        print(f"Critical events: [magenta]{criticals}[/magenta]")
