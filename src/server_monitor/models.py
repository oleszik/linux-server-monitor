"""Data models shared across collectors, health evaluation, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class HealthState(StrEnum):
    """Overall health classification for a metric or the whole system."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class SystemInfo:
    hostname: str
    os_name: str
    os_version: str
    kernel_version: str
    architecture: str
    uptime_seconds: float | None


@dataclass
class CpuInfo:
    logical_cores: int
    usage_percent: float | None
    load_average_1m: float | None = None
    load_average_5m: float | None = None
    load_average_15m: float | None = None


@dataclass
class MemoryInfo:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    usage_percent: float
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None
    swap_usage_percent: float | None = None


@dataclass
class DiskInfo:
    mount_point: str
    device: str | None
    filesystem_type: str | None
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    error: str | None = None


@dataclass
class NetworkInterfaceInfo:
    name: str
    ipv4_address: str | None
    bytes_sent: int
    bytes_received: int


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


@dataclass
class ServiceStatus:
    name: str
    active_state: str  # active, inactive, failed, unknown
    enabled_state: str  # enabled, disabled, static, unknown
    supported: bool = True
    error: str | None = None


@dataclass
class Finding:
    """A single threshold evaluation result for one metric."""

    metric: str
    state: HealthState
    value: float | None
    warning_threshold: float | None
    critical_threshold: float | None
    message: str


@dataclass
class HealthReport:
    overall_state: HealthState
    findings: list[Finding] = field(default_factory=list)
