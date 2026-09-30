"""Process monitoring: identify top resource-consuming processes."""

from __future__ import annotations

from typing import Literal

import psutil

from server_monitor.models import ProcessInfo

SortKey = Literal["cpu", "memory"]


def collect_top_processes(sort_by: SortKey = "cpu", limit: int = 10) -> list[ProcessInfo]:
    """Return the top ``limit`` processes sorted by CPU or memory usage.

    Processes that disappear or become inaccessible mid-scan (common on a
    busy system) are silently skipped rather than raising.
    """
    processes: list[ProcessInfo] = []

    # A first cpu_percent() call primes psutil's internal sampling; without
    # this, the very first reading for every process is always 0.0.
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            cpu_percent = proc.cpu_percent(interval=None)
            memory_percent = proc.memory_percent()
            name = proc.name()
            pid = proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        processes.append(
            ProcessInfo(
                pid=pid,
                name=name,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
            )
        )

    key = (lambda p: p.cpu_percent) if sort_by == "cpu" else (lambda p: p.memory_percent)
    processes.sort(key=key, reverse=True)
    return processes[:limit]
