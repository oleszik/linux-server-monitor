"""CLI argument parsing and exit-code tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server_monitor import cli
from server_monitor.models import (
    CpuInfo,
    DiskInfo,
    MemoryInfo,
    ProcessInfo,
    ServiceStatus,
    SystemInfo,
)


@pytest.fixture(autouse=True)
def _stub_collectors(monkeypatch):
    """Replace all real collectors with deterministic fakes for CLI tests."""
    monkeypatch.setattr(
        cli,
        "collect_system_info",
        lambda: SystemInfo("host", "Linux", "Ubuntu", "6.8.0", "x86_64", 100.0),
    )
    monkeypatch.setattr(cli, "collect_cpu_info", lambda: CpuInfo(4, 10.0, 1.0, 1.0, 1.0))
    monkeypatch.setattr(
        cli, "collect_memory_info", lambda: MemoryInfo(1000, 400, 600, 40.0, 100, 10, 10.0)
    )
    monkeypatch.setattr(
        cli,
        "collect_disk_info",
        lambda: [DiskInfo("/", "/dev/sda1", "ext4", 100, 40, 60, 40.0)],
    )
    monkeypatch.setattr(cli, "collect_network_info", lambda: [])
    monkeypatch.setattr(
        cli,
        "collect_top_processes",
        lambda sort_by, limit: [ProcessInfo(1, "proc", 5.0, 5.0)][:limit],
    )
    monkeypatch.setattr(
        cli,
        "check_services",
        lambda names: [ServiceStatus(n, "active", "enabled") for n in names],
    )
    yield


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    assert exc_info.value.code == 0


def test_status_returns_ok(capsys):
    code = cli.main(["status"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "System" in out
    assert "CPU" in out


def test_health_ok(capsys):
    code = cli.main(["health"])
    assert code == cli.EXIT_OK


def test_health_warning_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_cpu_info", lambda: CpuInfo(4, 85.0, 1.0, 1.0, 1.0))
    code = cli.main(["health"])
    assert code == cli.EXIT_WARNING


def test_health_critical_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_cpu_info", lambda: CpuInfo(4, 99.0, 1.0, 1.0, 1.0))
    code = cli.main(["health"])
    assert code == cli.EXIT_CRITICAL


def test_processes_respects_limit(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "collect_top_processes",
        lambda sort_by, limit: [ProcessInfo(i, f"p{i}", 1.0, 1.0) for i in range(limit)],
    )
    code = cli.main(["processes", "--limit", "3"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "top 3" in out


def test_processes_rejects_non_positive_limit():
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["processes", "--limit", "0"])
    assert exc_info.value.code == 2


def test_services_with_names(capsys):
    code = cli.main(["services", "ssh", "docker"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "ssh" in out
    assert "docker" in out


def test_services_no_names_no_config(capsys):
    code = cli.main(["services"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "No services requested" in out


def test_services_query_error_returns_operational_error(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "check_services",
        lambda names: [ServiceStatus(names[0], "unknown", "unknown", error="not found")],
    )
    code = cli.main(["services", "missing"])
    assert code == cli.EXIT_ERROR


def test_report_json_is_valid(capsys):
    code = cli.main(["report", "--format", "json"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["system"]["hostname"] == "host"


def test_report_text_format(capsys):
    code = cli.main(["report", "--format", "text"])
    assert code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "System" in out
    assert "Health" in out


def test_malformed_config_exits_with_error(tmp_path: Path, capsys):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("thresholds:\n  cpu:\n    warning: 99\n    critical: 10\n")
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--config", str(config_file), "status"])
    assert exc_info.value.code == cli.EXIT_ERROR


def test_missing_command_exits_nonzero():
    with pytest.raises(SystemExit) as exc_info:
        cli.main([])
    assert exc_info.value.code != 0
