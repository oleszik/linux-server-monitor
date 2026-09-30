"""Network collector tests."""

from __future__ import annotations

import socket
from collections import namedtuple

import psutil

from server_monitor.collectors.network import collect_network_info

Addr = namedtuple("Addr", ["family", "address", "netmask", "broadcast", "ptp"])
IOCounters = namedtuple("IOCounters", ["bytes_sent", "bytes_recv"])


def test_collect_network_info_with_ipv4_and_counters(monkeypatch):
    addrs = {
        "eth0": [Addr(socket.AF_INET, "10.0.0.5", "255.255.255.0", None, None)],
    }
    counters = {"eth0": IOCounters(bytes_sent=1000, bytes_recv=2000)}
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: addrs)
    monkeypatch.setattr(psutil, "net_io_counters", lambda pernic=False: counters)

    interfaces = collect_network_info()

    assert len(interfaces) == 1
    assert interfaces[0].name == "eth0"
    assert interfaces[0].ipv4_address == "10.0.0.5"
    assert interfaces[0].bytes_sent == 1000
    assert interfaces[0].bytes_received == 2000


def test_collect_network_info_no_ipv4_address(monkeypatch):
    addrs = {"eth1": [Addr(socket.AF_INET6, "::1", None, None, None)]}
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: addrs)
    monkeypatch.setattr(psutil, "net_io_counters", lambda pernic=False: {})

    interfaces = collect_network_info()

    assert interfaces[0].ipv4_address is None
    assert interfaces[0].bytes_sent == 0
    assert interfaces[0].bytes_received == 0


def test_collect_network_info_empty_when_unavailable(monkeypatch):
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: {})
    monkeypatch.setattr(psutil, "net_io_counters", lambda pernic=False: {})

    assert collect_network_info() == []
