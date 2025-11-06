# Quantum Defense Matrix

> **Status:** Proof-of-concept research project. Do not rely on this code as the sole layer of defense for production infrastructure.

Quantum Defense Matrix is an experimental, Python-based security orchestration service that bundles together a handful of defensive building blocks:

- A lightweight threat-intelligence cache backed by SQLite
- A tripwire-style file integrity monitor
- Honeypot listeners for SSH and HTTP ports
- A periodic update loop to refresh threat feeds
- A pluggable command runner used to apply local firewall policies

The project is inspired by the “Quantum Defense Matrix” installation script that accompanies this repository. Instead of baking all logic into a monolithic bash file, the codebase reorganizes the functionality into testable Python modules, adds structured configuration, and exposes a typed command-line interface (CLI).

⚠️ **Ethical & operational notice**

- Running honeypots and automated firewall tooling requires explicit authorization on the network where it is deployed.
- The included firewall automation assumes an `iptables`-compatible environment. Improper rules can lock you out of remote hosts—test carefully.
- Threat feeds shipped with this repository are public blocklists suitable for experimentation. Verify licensing and operational fit before production use.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Launch the defense supervisor with the default config
quantum-defense run --config config/example.yml
```

The `run` command starts all enabled modules (firewall synchronizer, tripwire monitor, honeypots, threat-intel refresher) inside the foreground process. Press `Ctrl+C` to terminate.

## Repository layout

- `quantum_defense/`
  - `config.py` – Pydantic models that describe configuration.
  - `core.py` – High-level orchestrator that wires all modules together.
  - `firewall.py` – Firewall synchronization logic built around shell command adapters.
  - `honeypot.py` – Simple TCP honeypots for SSH and HTTP.
  - `integrity.py` – Tripwire-like file integrity monitoring utilities.
  - `intelligence.py` – Threat feed downloader and persistence helpers.
  - `logging.py` – SQLite-backed event logging facade.
  - `cli.py` – Typer CLI that exposes management commands.
- `config/example.yml` – Sample configuration toggling modules on/off.
- `scripts/install.sh` – Idempotent installation helper tailored for Amazon Linux 2023.
- `scripts/systemd/` – Example systemd units for long-lived deployments.

## Feature summary

- **Declarative modules** – Toggle defense components from YAML; run only what is required.
- **SQLite intelligence cache** – Single-file database storing threat indicators, file baselines, and attack events.
- **Pluggable firewall adapter** – Supports `iptables` out of the box and can be extended for other firewalls.
- **File integrity monitoring** – Automatically baselines configured paths and alerts on hash drift.
- **Honeypot listeners** – Low-interaction TCP listeners on configurable ports.
- **Update loop** – Periodically refreshes threat intelligence feeds and pushes events into the database.

## Configuration

All runtime settings live in YAML. See `config/example.yml` for a fully annotated reference. Highlights:

- `datastore.path` – Filesystem path to the SQLite database.
- `modules.firewall.enabled` – Toggle firewall synchronization.
- `modules.tripwire.paths` – Entries to baseline and monitor.
- `modules.honeypot.ports` – Ports to listen on for honeypot traps.
- `threat_feeds.urls` – Public blocklists or internal feeds to ingest.

Environment variables can override select values (see `quantum_defense/config.py`).

## Systemd integration

Example service and timer units live under `scripts/systemd/`. Copy them to `/etc/systemd/system/`, adjust paths, run `systemctl daemon-reload`, then enable and start as needed:

```bash
sudo cp scripts/systemd/quantum-defense.service /etc/systemd/system/
sudo cp scripts/systemd/quantum-defense-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now quantum-defense.service quantum-defense-update.timer
```

The update timer executes `quantum-defense update-feeds` on a daily cadence by default.

## Development

Install development requirements and run the test suite:

```bash
pip install -e .[dev]
pytest
```

Code style enforcement uses `ruff` and `black`. Invoke `ruff check` and `black` to keep contributions consistent.

## Roadmap

- Expand firewall adapters beyond `iptables` (e.g., `nftables`, `pf`).
- Emit structured JSON logs for SIEM ingestion.
- Support authenticated honeypot emulation via `paramiko`.
- Add unit tests for the threat intelligence ingestion pipeline.

## Contributing

Contributions are welcome. Please open issues or pull requests to discuss proposed changes. See `SECURITY.md` for the coordinated disclosure policy.

## License

Released under the MIT License. See `LICENSE` for details.
