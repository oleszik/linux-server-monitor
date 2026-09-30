# Linux Server Monitor

A read-only, dependency-light command-line tool for monitoring the health of a Linux server: CPU, memory, disk, network, processes, and systemd services — with configurable warning/critical thresholds and both human-readable and JSON output.

Built as a practical demonstration of Python automation, Linux administration, and DevOps/troubleshooting skills for freelance and portfolio purposes. It is designed to be genuinely useful on a real machine (VPS, home server, Docker host, Raspberry Pi), not just a simulated demo.

**[Portfolio demo and real sanitized output →](examples/showcase/README.md)**

| Capability | Client value |
|---|---|
| Read-only collection | Inspect a server without changing it or requiring root |
| Threshold-based health checks | Turn raw CPU, memory, and disk metrics into actionable states |
| Process and systemd inspection | Find resource-heavy processes and verify important services |
| Text and JSON reports | Support operators at a terminal and downstream automation |
| Defensive, tested Python | Handle malformed configuration and changing system state safely |

## Quick demo

```bash
python -m server_monitor status
python -m server_monitor health
python -m server_monitor processes --sort memory --limit 5
python -m server_monitor report --format json
```

See the [portfolio showcase](examples/showcase/README.md) for captured output, normal/WARNING/CRITICAL examples, a complete JSON report, and screenshot guidance.

## Use cases

- Quick health check of a VPS or home server (`status` / `health`)
- Spotting resource-heavy processes during a slowdown (`processes`)
- Confirming critical services (ssh, docker, nginx, ...) are running (`services`)
- Generating a machine-readable report for scripting, cron jobs, or later dashboards (`report --format json`)
- A starting point for lightweight, agent-less server monitoring without a full observability stack

## Features (implemented)

- **System info**: hostname, OS/distribution, kernel version, architecture, uptime
- **CPU**: logical core count, overall usage percentage, load averages (1/5/15 min, where supported by the OS)
- **Memory**: total/used/available RAM and usage percentage, swap total/used/percentage
- **Disk**: per-mount usage (total/used/free/percentage) for real filesystems; pseudo filesystems (tmpfs, proc, overlay, etc.) are excluded by default
- **Network**: per-interface IPv4 address and cumulative bytes sent/received (no external requests are ever made — no public-IP lookups)
- **Processes**: top-N processes by CPU or memory usage, resilient to processes disappearing mid-scan
- **Services**: systemd unit active/enabled status via `systemctl show` (read-only, no root required); clear "unsupported" result on non-systemd systems
- **Health thresholds**: configurable warning/critical thresholds for CPU, memory, and disk, evaluated independently of presentation
- **JSON reporting**: a single structured report combining all of the above, valid JSON with no `NaN`/`Infinity`
- **YAML configuration**: thresholds and a default service list, validated with clear errors on malformed input

## Not implemented (out of scope for this MVP)

No web dashboard, GUI, database, Prometheus/Grafana integration, Docker container monitoring, remote/SSH monitoring, email/Telegram/Slack alerting, cloud integration, or automatic remediation. This tool is **read-only** — it never modifies the monitored system (no service restarts, no configuration changes).

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/oleszik/linux-server-monitor.git
cd linux-server-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
python -m server_monitor --help

python -m server_monitor status
python -m server_monitor health
python -m server_monitor processes --sort memory --limit 10
python -m server_monitor services ssh docker nginx
python -m server_monitor report --format json
python -m server_monitor --config config.yaml health
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Healthy / command succeeded |
| 1 | Tool/operational error (bad config, missing dependency, unknown health state) |
| 2 | Health state is WARNING |
| 3 | Health state is CRITICAL |

`status` and `processes` always return 0 on success; `health` and `report` return the health-based exit code above.

## Example output

The [portfolio showcase](examples/showcase/README.md) contains concise, privacy-reviewed output captured from the real application, including all health states and a complete JSON report.

## Configuration

Configuration is optional; sensible defaults apply if no file is given. See [config.example.yaml](config.example.yaml):

```yaml
thresholds:
  cpu:
    warning: 80
    critical: 95
  memory:
    warning: 80
    critical: 95
  disk:
    warning: 80
    critical: 90

services:
  - ssh
  - docker
```

Malformed configuration (e.g. `warning` greater than `critical`, non-numeric thresholds, unknown metrics) produces a readable error and a non-zero exit code instead of a traceback.

## JSON reporting

`python -m server_monitor report --format json` emits a single structured document containing a generation timestamp, system info, CPU, memory, disks, network, health findings, and (if configured) requested service results. See the [showcase report](examples/showcase/output/server-report.json) for a full sanitized capture.

## Architecture

```
src/server_monitor/
  __main__.py          entry point (python -m server_monitor)
  cli.py                argparse-based CLI, command dispatch, exit codes
  models.py             shared dataclasses (SystemInfo, CpuInfo, DiskInfo, ...)
  config.py             YAML config loading + validation (ConfigError)
  health.py             threshold evaluation, independent of presentation
  reporting.py          human-readable rendering + JSON serialization
  collectors/
    system.py           hostname, OS, kernel, uptime
    cpu.py               CPU usage + load averages
    memory.py            RAM + swap
    disk.py              per-mount disk usage, pseudo-fs filtering
    network.py           per-interface IPv4 + byte counters
    processes.py         top-N process scan
    services.py          systemd unit status via systemctl
```

Collection, health evaluation, and presentation are deliberately separated so that new output formats (e.g. HTML) could be added later without touching the collectors.

## Testing

```bash
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

The test suite (80 tests) mocks all system-dependent interfaces (`psutil`, `subprocess`, `socket`, `platform`) so it does not depend on the developer's machine state, does not require root, and never modifies the system.

## Limitations

- Developed and tested on Ubuntu 24.04 (x86_64); other distributions/architectures should work via `psutil` but have not been verified
- Load averages are only available on platforms that expose `os.getloadavg()` (not Windows)
- Service checks require `systemd`; on non-systemd systems, checks report a clear "unsupported" result rather than failing
- Per-process CPU percentage on the first sample within a run is approximate (a short internal priming step reduces but does not eliminate this)
- No persistence, history, or trend tracking — every run is a point-in-time snapshot

## Supported environment assumptions

- Linux (tested on Ubuntu 24.04), Python 3.11+
- `systemctl` present for service checks (optional feature; degrades gracefully if absent)
- Runs as a normal, non-root user

## Roadmap (future iterations, not implemented yet)

- HTML report output (reusing the existing JSON data model)
- Optional metric history/trend tracking
- Docker container-aware monitoring
- Packaging as a standalone binary

## License

[MIT](LICENSE)
