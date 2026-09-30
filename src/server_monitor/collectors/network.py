"""Network interface collection (no external requests are ever made)."""

from __future__ import annotations

import socket

import psutil

from server_monitor.models import NetworkInterfaceInfo


def collect_network_info() -> list[NetworkInterfaceInfo]:
    """Collect per-interface IPv4 address and cumulative byte counters."""
    try:
        addrs_by_iface = psutil.net_if_addrs()
    except (OSError, psutil.Error):
        addrs_by_iface = {}

    try:
        counters_by_iface = psutil.net_io_counters(pernic=True)
    except (OSError, psutil.Error):
        counters_by_iface = {}

    interfaces: list[NetworkInterfaceInfo] = []
    for name, addrs in addrs_by_iface.items():
        ipv4_address = None
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ipv4_address = addr.address
                break

        counters = counters_by_iface.get(name)
        bytes_sent = counters.bytes_sent if counters else 0
        bytes_received = counters.bytes_recv if counters else 0

        interfaces.append(
            NetworkInterfaceInfo(
                name=name,
                ipv4_address=ipv4_address,
                bytes_sent=bytes_sent,
                bytes_received=bytes_received,
            )
        )

    return interfaces
