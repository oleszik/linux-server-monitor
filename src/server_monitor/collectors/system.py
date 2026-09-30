"""System-level information collection (hostname, OS, kernel, uptime)."""

from __future__ import annotations

import platform
import socket
import time

import psutil

from server_monitor.models import SystemInfo


def _read_os_release() -> str:
    """Return a human-readable distro name from /etc/os-release, if available."""
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            data = {}
            for line in fh:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                data[key] = value.strip('"')
        return data.get("PRETTY_NAME", platform.system())
    except OSError:
        return platform.system()


def collect_system_info() -> SystemInfo:
    """Collect basic system identification and uptime information."""
    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = "unknown"

    uptime_seconds: float | None
    try:
        uptime_seconds = time.time() - psutil.boot_time()
    except (OSError, psutil.Error):
        uptime_seconds = None

    return SystemInfo(
        hostname=hostname,
        os_name=platform.system(),
        os_version=_read_os_release(),
        kernel_version=platform.release(),
        architecture=platform.machine(),
        uptime_seconds=uptime_seconds,
    )
