"""Command-line interface for server-monitor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from server_monitor import reporting
from server_monitor.collectors.cpu import collect_cpu_info
from server_monitor.collectors.disk import collect_disk_info
from server_monitor.collectors.memory import collect_memory_info
from server_monitor.collectors.network import collect_network_info
from server_monitor.collectors.processes import collect_top_processes
from server_monitor.collectors.services import check_services
from server_monitor.collectors.system import collect_system_info
from server_monitor.config import Config, ConfigError, load_config
from server_monitor.health import build_health_report
from server_monitor.models import HealthState

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_WARNING = 2
EXIT_CRITICAL = 3

_HEALTH_EXIT_CODES = {
    HealthState.OK: EXIT_OK,
    HealthState.WARNING: EXIT_WARNING,
    HealthState.CRITICAL: EXIT_CRITICAL,
    HealthState.UNKNOWN: EXIT_ERROR,
}


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="server_monitor",
        description="Read-only Linux server monitoring CLI: system, CPU, memory, disk, "
        "network, process, and systemd service checks with configurable health thresholds.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="path to a YAML configuration file with thresholds/services",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="show a human-readable system status report")

    subparsers.add_parser("health", help="evaluate metrics against configured thresholds")

    processes_parser = subparsers.add_parser("processes", help="show top resource-heavy processes")
    processes_parser.add_argument(
        "--sort", choices=["cpu", "memory"], default="cpu", help="metric to sort by (default: cpu)"
    )
    processes_parser.add_argument(
        "--limit",
        type=_positive_int,
        default=10,
        help="maximum number of processes to show (default: 10)",
    )

    services_parser = subparsers.add_parser("services", help="check systemd service status")
    services_parser.add_argument(
        "names", nargs="*", help="service names to check (falls back to config file 'services')"
    )

    report_parser = subparsers.add_parser("report", help="generate a combined report")
    report_parser.add_argument(
        "--format", choices=["text", "json"], default="json", help="output format (default: json)"
    )

    return parser


def _load_config_or_exit(config_path: Path | None) -> Config:
    try:
        return load_config(config_path)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR) from exc


def _cmd_status(args: argparse.Namespace, config: Config) -> int:
    system = collect_system_info()
    cpu = collect_cpu_info()
    memory = collect_memory_info()
    disks = collect_disk_info()
    network = collect_network_info()

    sections = [
        reporting.render_system_section(system),
        reporting.render_cpu_section(cpu),
        reporting.render_memory_section(memory),
        reporting.render_disk_section(disks),
        reporting.render_network_section(network),
    ]
    print("\n\n".join(sections))
    return EXIT_OK


def _cmd_health(args: argparse.Namespace, config: Config) -> int:
    cpu = collect_cpu_info()
    memory = collect_memory_info()
    disks = collect_disk_info()

    health = build_health_report(
        cpu_usage_percent=cpu.usage_percent,
        memory_usage_percent=memory.usage_percent,
        disks=disks,
        thresholds=config.thresholds,
    )
    print(reporting.render_health_section(health))
    return _HEALTH_EXIT_CODES[health.overall_state]


def _cmd_processes(args: argparse.Namespace, config: Config) -> int:
    processes = collect_top_processes(sort_by=args.sort, limit=args.limit)
    print(reporting.render_processes_section(processes, sort_by=args.sort))
    return EXIT_OK


def _cmd_services(args: argparse.Namespace, config: Config) -> int:
    names = args.names or config.services
    if not names:
        print("No services requested (pass names or configure 'services' in the config file).")
        return EXIT_OK
    services = check_services(names)
    print(reporting.render_services_section(services))
    if any(service.error for service in services):
        return EXIT_ERROR
    return EXIT_OK


def _cmd_report(args: argparse.Namespace, config: Config) -> int:
    system = collect_system_info()
    cpu = collect_cpu_info()
    memory = collect_memory_info()
    disks = collect_disk_info()
    network = collect_network_info()
    services = check_services(config.services) if config.services else []

    health = build_health_report(
        cpu_usage_percent=cpu.usage_percent,
        memory_usage_percent=memory.usage_percent,
        disks=disks,
        thresholds=config.thresholds,
    )

    if args.format == "json":
        report = reporting.build_json_report(system, cpu, memory, disks, network, health, services)
        print(reporting.to_json(report))
    else:
        sections = [
            reporting.render_system_section(system),
            reporting.render_cpu_section(cpu),
            reporting.render_memory_section(memory),
            reporting.render_disk_section(disks),
            reporting.render_network_section(network),
            reporting.render_health_section(health),
            reporting.render_services_section(services),
        ]
        print("\n\n".join(sections))

    return _HEALTH_EXIT_CODES[health.overall_state]


_COMMANDS = {
    "status": _cmd_status,
    "health": _cmd_health,
    "processes": _cmd_processes,
    "services": _cmd_services,
    "report": _cmd_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = _load_config_or_exit(args.config)

    return _COMMANDS[args.command](args, config)


if __name__ == "__main__":
    raise SystemExit(main())
