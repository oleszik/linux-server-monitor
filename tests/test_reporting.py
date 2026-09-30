"""Reporting tests: formatting helpers and JSON serialization."""

from __future__ import annotations

import json
import math

import pytest

from server_monitor import reporting
from server_monitor.config import Thresholds
from server_monitor.health import build_health_report
from server_monitor.models import (
    CpuInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInterfaceInfo,
    ServiceStatus,
    SystemInfo,
)


def test_format_bytes_scales_units():
    assert reporting.format_bytes(500) == "500.0 B"
    assert reporting.format_bytes(1024) == "1.0 KB"
    assert reporting.format_bytes(1024 * 1024 * 3) == "3.0 MB"


def test_format_uptime_none_is_unknown():
    assert reporting.format_uptime(None) == "unknown"


def test_format_uptime_formats_days_hours_minutes():
    seconds = 2 * 86400 + 3 * 3600 + 5 * 60
    assert reporting.format_uptime(seconds) == "2d 3h 5m"


def test_format_uptime_minutes_only():
    assert reporting.format_uptime(90) == "1m"


def _sample_report_dict():
    system = SystemInfo("host", "Linux", "Ubuntu 24.04", "6.8.0", "x86_64", 3600.0)
    cpu = CpuInfo(logical_cores=4, usage_percent=10.0, load_average_1m=1.0)
    memory = MemoryInfo(total_bytes=1000, used_bytes=400, available_bytes=600, usage_percent=40.0)
    disks = [
        DiskInfo(
            mount_point="/",
            device="/dev/sda1",
            filesystem_type="ext4",
            total_bytes=100,
            used_bytes=40,
            free_bytes=60,
            usage_percent=40.0,
        )
    ]
    network = [NetworkInterfaceInfo("eth0", "10.0.0.1", 100, 200)]
    health = build_health_report(10.0, 40.0, disks, Thresholds())
    services = [ServiceStatus("ssh", "active", "enabled")]
    return reporting.build_json_report(system, cpu, memory, disks, network, health, services)


def test_build_json_report_has_expected_keys():
    report = _sample_report_dict()
    assert set(report.keys()) == {
        "generated_at",
        "system",
        "cpu",
        "memory",
        "disks",
        "network",
        "health",
        "services",
    }
    assert report["system"]["hostname"] == "host"
    assert report["health"]["overall_state"] == "OK"
    assert report["services"][0]["name"] == "ssh"


def test_to_json_produces_valid_parseable_json():
    report = _sample_report_dict()
    text = reporting.to_json(report)
    parsed = json.loads(text)
    assert parsed["system"]["hostname"] == "host"


def test_to_json_rejects_nan_and_infinity():
    report = _sample_report_dict()
    report["cpu"]["usage_percent"] = math.nan
    with pytest.raises(ValueError):
        reporting.to_json(report)


def test_render_health_section_lists_findings():
    disks = []
    health = build_health_report(90.0, 10.0, disks, Thresholds())
    text = reporting.render_health_section(health)
    assert "Health: WARNING" in text
    assert "cpu" in text
