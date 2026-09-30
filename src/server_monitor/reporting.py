"""Human-readable and JSON presentation, kept separate from data collection."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from server_monitor.models import (
    CpuInfo,
    DiskInfo,
    HealthReport,
    MemoryInfo,
    NetworkInterfaceInfo,
    ProcessInfo,
    ServiceStatus,
    SystemInfo,
)


def format_bytes(num_bytes: int | float) -> str:
    """Render a byte count as a human-readable string (e.g. '1.5 GB')."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} EB"


def format_uptime(seconds: float | None) -> str:
    """Render an uptime duration in seconds as 'Xd Yh Zm'."""
    if seconds is None:
        return "unknown"
    total_seconds = int(seconds)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def render_system_section(system: SystemInfo) -> str:
    lines = [
        "System",
        f"  Hostname:     {system.hostname}",
        f"  OS:           {system.os_version}",
        f"  Kernel:       {system.kernel_version}",
        f"  Architecture: {system.architecture}",
        f"  Uptime:       {format_uptime(system.uptime_seconds)}",
    ]
    return "\n".join(lines)


def render_cpu_section(cpu: CpuInfo) -> str:
    usage = f"{cpu.usage_percent:.1f}%" if cpu.usage_percent is not None else "unavailable"
    lines = [
        "CPU",
        f"  Logical cores: {cpu.logical_cores}",
        f"  Usage:         {usage}",
    ]
    if cpu.load_average_1m is not None:
        lines.append(
            f"  Load average:  {cpu.load_average_1m:.2f}, "
            f"{cpu.load_average_5m:.2f}, {cpu.load_average_15m:.2f} (1m, 5m, 15m)"
        )
    else:
        lines.append("  Load average:  unavailable")
    return "\n".join(lines)


def render_memory_section(memory: MemoryInfo) -> str:
    lines = [
        "Memory",
        f"  Total:     {format_bytes(memory.total_bytes)}",
        f"  Used:      {format_bytes(memory.used_bytes)} ({memory.usage_percent:.1f}%)",
        f"  Available: {format_bytes(memory.available_bytes)}",
    ]
    if memory.swap_total_bytes:
        lines.append(
            f"  Swap:      {format_bytes(memory.swap_used_bytes or 0)} / "
            f"{format_bytes(memory.swap_total_bytes)} "
            f"({memory.swap_usage_percent:.1f}%)"
        )
    else:
        lines.append("  Swap:      none configured")
    return "\n".join(lines)


def render_disk_section(disks: list[DiskInfo]) -> str:
    lines = ["Disk"]
    if not disks:
        lines.append("  No mounted filesystems found.")
        return "\n".join(lines)
    for disk in disks:
        if disk.error:
            lines.append(f"  {disk.mount_point}: unavailable ({disk.error})")
            continue
        device = disk.device or "?"
        lines.append(
            f"  {disk.mount_point} ({device}, {disk.filesystem_type or 'unknown'}): "
            f"{format_bytes(disk.used_bytes)} / {format_bytes(disk.total_bytes)} "
            f"({disk.usage_percent:.1f}%)"
        )
    return "\n".join(lines)


def render_network_section(interfaces: list[NetworkInterfaceInfo]) -> str:
    lines = ["Network"]
    if not interfaces:
        lines.append("  No network interfaces found.")
        return "\n".join(lines)
    for iface in interfaces:
        address = iface.ipv4_address or "no IPv4 address"
        lines.append(
            f"  {iface.name}: {address}, sent {format_bytes(iface.bytes_sent)}, "
            f"received {format_bytes(iface.bytes_received)}"
        )
    return "\n".join(lines)


def render_health_section(health: HealthReport) -> str:
    lines = [f"Health: {health.overall_state.value}"]
    for finding in health.findings:
        lines.append(f"  [{finding.state.value}] {finding.message}")
    return "\n".join(lines)


def render_processes_section(processes: list[ProcessInfo], sort_by: str) -> str:
    lines = [f"Processes (top {len(processes)} by {sort_by})"]
    if not processes:
        lines.append("  No process data available.")
        return "\n".join(lines)
    lines.append(f"  {'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  NAME")
    for proc in processes:
        lines.append(
            f"  {proc.pid:>7}  {proc.cpu_percent:>6.1f}  {proc.memory_percent:>6.1f}  {proc.name}"
        )
    return "\n".join(lines)


def render_services_section(services: list[ServiceStatus]) -> str:
    lines = ["Services"]
    if not services:
        lines.append("  No services requested.")
        return "\n".join(lines)
    for service in services:
        if not service.supported:
            lines.append(f"  {service.name}: unsupported ({service.error})")
            continue
        if service.error:
            lines.append(f"  {service.name}: unknown ({service.error})")
            continue
        lines.append(f"  {service.name}: {service.active_state} (enabled: {service.enabled_state})")
    return "\n".join(lines)


def _asdict_system(system: SystemInfo) -> dict[str, Any]:
    return {
        "hostname": system.hostname,
        "os_name": system.os_name,
        "os_version": system.os_version,
        "kernel_version": system.kernel_version,
        "architecture": system.architecture,
        "uptime_seconds": system.uptime_seconds,
    }


def _asdict_cpu(cpu: CpuInfo) -> dict[str, Any]:
    return {
        "logical_cores": cpu.logical_cores,
        "usage_percent": cpu.usage_percent,
        "load_average_1m": cpu.load_average_1m,
        "load_average_5m": cpu.load_average_5m,
        "load_average_15m": cpu.load_average_15m,
    }


def _asdict_memory(memory: MemoryInfo) -> dict[str, Any]:
    return {
        "total_bytes": memory.total_bytes,
        "used_bytes": memory.used_bytes,
        "available_bytes": memory.available_bytes,
        "usage_percent": memory.usage_percent,
        "swap_total_bytes": memory.swap_total_bytes,
        "swap_used_bytes": memory.swap_used_bytes,
        "swap_usage_percent": memory.swap_usage_percent,
    }


def _asdict_disk(disk: DiskInfo) -> dict[str, Any]:
    return {
        "mount_point": disk.mount_point,
        "device": disk.device,
        "filesystem_type": disk.filesystem_type,
        "total_bytes": disk.total_bytes,
        "used_bytes": disk.used_bytes,
        "free_bytes": disk.free_bytes,
        "usage_percent": disk.usage_percent,
        "error": disk.error,
    }


def _asdict_network(iface: NetworkInterfaceInfo) -> dict[str, Any]:
    return {
        "name": iface.name,
        "ipv4_address": iface.ipv4_address,
        "bytes_sent": iface.bytes_sent,
        "bytes_received": iface.bytes_received,
    }


def _asdict_process(proc: ProcessInfo) -> dict[str, Any]:
    return {
        "pid": proc.pid,
        "name": proc.name,
        "cpu_percent": proc.cpu_percent,
        "memory_percent": proc.memory_percent,
    }


def _asdict_service(service: ServiceStatus) -> dict[str, Any]:
    return {
        "name": service.name,
        "active_state": service.active_state,
        "enabled_state": service.enabled_state,
        "supported": service.supported,
        "error": service.error,
    }


def _asdict_health(health: HealthReport) -> dict[str, Any]:
    return {
        "overall_state": health.overall_state.value,
        "findings": [
            {
                "metric": f.metric,
                "state": f.state.value,
                "value": f.value,
                "warning_threshold": f.warning_threshold,
                "critical_threshold": f.critical_threshold,
                "message": f.message,
            }
            for f in health.findings
        ],
    }


def build_json_report(
    system: SystemInfo,
    cpu: CpuInfo,
    memory: MemoryInfo,
    disks: list[DiskInfo],
    network: list[NetworkInterfaceInfo],
    health: HealthReport,
    services: list[ServiceStatus] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable report combining all collected data."""
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "system": _asdict_system(system),
        "cpu": _asdict_cpu(cpu),
        "memory": _asdict_memory(memory),
        "disks": [_asdict_disk(d) for d in disks],
        "network": [_asdict_network(n) for n in network],
        "health": _asdict_health(health),
        "services": [_asdict_service(s) for s in (services or [])],
    }


def to_json(report: dict[str, Any]) -> str:
    """Serialize a report dict to standards-compliant JSON (no NaN/Infinity)."""
    return json.dumps(report, indent=2, allow_nan=False)
