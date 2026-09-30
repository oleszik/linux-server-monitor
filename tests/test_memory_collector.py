"""Memory collector tests (system-independent via psutil mocking)."""

from __future__ import annotations

from collections import namedtuple

import psutil

from server_monitor.collectors.memory import collect_memory_info

VirtualMem = namedtuple("VirtualMem", ["total", "used", "available", "percent"])
SwapMem = namedtuple("SwapMem", ["total", "used", "percent"])


def test_collect_memory_info_with_swap(monkeypatch):
    virtual_mem = VirtualMem(total=1000, used=400, available=600, percent=40.0)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: virtual_mem)
    monkeypatch.setattr(psutil, "swap_memory", lambda: SwapMem(total=200, used=50, percent=25.0))

    info = collect_memory_info()

    assert info.total_bytes == 1000
    assert info.used_bytes == 400
    assert info.available_bytes == 600
    assert info.usage_percent == 40.0
    assert info.swap_total_bytes == 200
    assert info.swap_used_bytes == 50
    assert info.swap_usage_percent == 25.0


def test_collect_memory_info_swap_unavailable(monkeypatch):
    virtual_mem = VirtualMem(total=1000, used=400, available=600, percent=40.0)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: virtual_mem)

    def _raise():
        raise OSError("no swap")

    monkeypatch.setattr(psutil, "swap_memory", lambda: _raise())

    info = collect_memory_info()

    assert info.swap_total_bytes is None
    assert info.swap_used_bytes is None
    assert info.swap_usage_percent is None
