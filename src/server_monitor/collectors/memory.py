"""Memory and swap usage collection."""

from __future__ import annotations

import psutil

from server_monitor.models import MemoryInfo


def collect_memory_info() -> MemoryInfo:
    """Collect RAM and swap usage information."""
    virtual_mem = psutil.virtual_memory()

    swap_total = swap_used = swap_percent = None
    try:
        swap = psutil.swap_memory()
        swap_total = swap.total
        swap_used = swap.used
        swap_percent = swap.percent
    except (OSError, psutil.Error):
        pass

    return MemoryInfo(
        total_bytes=virtual_mem.total,
        used_bytes=virtual_mem.used,
        available_bytes=virtual_mem.available,
        usage_percent=virtual_mem.percent,
        swap_total_bytes=swap_total,
        swap_used_bytes=swap_used,
        swap_usage_percent=swap_percent,
    )
