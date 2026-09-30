# Linux Server Monitoring Demo

This demo shows how a Linux administrator can get a quick, read-only view of server health and important services without deploying a monitoring stack. It uses the real CLI, real system measurements, and configurable thresholds.

> **Portfolio snapshot:** The committed outputs were captured from the application on 30 September 2026. Identifying values were replaced with generic equivalents; measured resource values and health outcomes were not changed.

## What the tool checks

| Area | What is reported |
|---|---|
| System | OS, kernel, architecture, hostname, and uptime |
| CPU | Logical cores, utilization, and load averages |
| Memory | RAM and swap capacity and utilization |
| Disk | Usage for real filesystems; pseudo filesystems are filtered |
| Network | IPv4 address and byte counters by interface |
| Processes | Top processes by CPU or memory |
| Services | Read-only systemd active and enabled states |
| Health | Configurable CPU, memory, and disk thresholds |

## Example workflow

After installing the project with `pip install -e ".[dev]"`, run:

```bash
python -m server_monitor --config examples/showcase/config.yaml status
python -m server_monitor --config examples/showcase/config.yaml health
python -m server_monitor --config examples/showcase/config.yaml processes --sort memory --limit 5
python -m server_monitor --config examples/showcase/config.yaml services
python -m server_monitor --config examples/showcase/config.yaml report --format json
```

The main [config.yaml](config.yaml) uses practical default thresholds and checks `ssh` and `docker`. Service names and every threshold can be customized for the target server.

## Example results

The captured server was healthy under normal thresholds: CPU was 4.4%, memory was 54.9%, root disk usage was 19.3%, and both requested services were active and enabled. The full [JSON report](output/server-report.json) combines system, CPU, memory, disk, network, health, and service data in one machine-readable document.

The health engine reports:

- `OK`: the metric is below its warning threshold.
- `WARNING`: the metric reached the warning threshold; the CLI exits with code 2.
- `CRITICAL`: the metric reached the critical threshold; the CLI exits with code 3.
- `UNKNOWN`: the metric could not be evaluated; the CLI exits with code 1 when it is the overall state.

The [warning](output/health-warning-demo.txt) and [critical](output/health-critical-demo.txt) captures use deliberately low CPU thresholds from clearly labelled demo configurations. They prove the decision and exit-code paths without generating artificial load or implying that the host was in danger.

## Safety

The monitor is read-only and normally runs without root. It does not restart services, modify configuration, change firewall rules, delete files, or remediate findings. Service inspection uses read-only `systemctl show` calls, and network collection makes no external requests.

## Files in this showcase

| File | Purpose |
|---|---|
| [config.yaml](config.yaml) | Customizable normal monitoring configuration |
| [config-warning-demo.yaml](config-warning-demo.yaml) | Intentionally low threshold for the WARNING example |
| [config-critical-demo.yaml](config-critical-demo.yaml) | Intentionally low threshold for the CRITICAL example |
| [output/status.txt](output/status.txt) | Human-readable system status |
| [output/health-normal.txt](output/health-normal.txt) | Normal `OK` health evaluation |
| [output/health-warning-demo.txt](output/health-warning-demo.txt) | Deliberate WARNING threshold demonstration |
| [output/health-critical-demo.txt](output/health-critical-demo.txt) | Deliberate CRITICAL threshold demonstration |
| [output/processes.txt](output/processes.txt) | Top five processes by memory |
| [output/services.txt](output/services.txt) | Real systemd service-check result |
| [output/server-report.json](output/server-report.json) | Valid, structured combined report |
| [SCREENSHOTS.md](SCREENSHOTS.md) | Privacy-aware instructions for real portfolio screenshots |

## Sanitization notes

The hostname, local IP addresses, storage device names, interface/container identifiers, process IDs, and process labels were replaced. Documentation-only IPv4 ranges (`192.0.2.0/24`, `198.51.100.0/24`, and `203.0.113.0/24`) are used. No metric, threshold, health state, service state, or byte count was altered.
