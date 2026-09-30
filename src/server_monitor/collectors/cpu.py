"""CPU usage and load-average collection."""

from __future__ import annotations

import os

import psutil

from server_monitor.models import CpuInfo


def collect_cpu_info(interval: float = 0.1) -> CpuInfo:
    """Collect CPU core count, overall usage percentage, and load averages.

    ``interval`` controls how long psutil samples CPU usage; a short
    blocking sample gives a much more accurate instantaneous reading than
    a zero interval.
    """
    logical_cores = psutil.cpu_count(logical=True) or 1
    try:
        usage_percent: float | None = psutil.cpu_percent(interval=interval)
    except (OSError, psutil.Error):
        usage_percent = None

    load_1m = load_5m = load_15m = None
    getloadavg = getattr(os, "getloadavg", None)
    if getloadavg is not None:
        try:
            load_1m, load_5m, load_15m = getloadavg()
        except OSError:
            load_1m = load_5m = load_15m = None

    return CpuInfo(
        logical_cores=logical_cores,
        usage_percent=usage_percent,
        load_average_1m=load_1m,
        load_average_5m=load_5m,
        load_average_15m=load_15m,
    )
