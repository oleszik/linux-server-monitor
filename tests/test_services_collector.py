"""systemd service collector tests: availability detection and status parsing."""

from __future__ import annotations

import subprocess

from server_monitor.collectors import services as services_module
from server_monitor.collectors.services import check_service, check_services, systemd_available


def test_systemd_available_true(monkeypatch):
    monkeypatch.setattr(services_module.shutil, "which", lambda name: "/usr/bin/systemctl")
    monkeypatch.setattr(services_module.os.path, "isdir", lambda path: True)

    assert systemd_available() is True


def test_systemd_available_false_when_no_systemctl(monkeypatch):
    monkeypatch.setattr(services_module.shutil, "which", lambda name: None)

    assert systemd_available() is False


def test_systemd_available_false_when_no_run_systemd_dir(monkeypatch):
    monkeypatch.setattr(services_module.shutil, "which", lambda name: "/usr/bin/systemctl")
    monkeypatch.setattr(services_module.os.path, "isdir", lambda path: False)

    assert systemd_available() is False


def test_check_service_unsupported_without_systemd(monkeypatch):
    monkeypatch.setattr(services_module, "systemd_available", lambda: False)

    status = check_service("ssh")

    assert status.supported is False
    assert status.active_state == "unknown"
    assert status.error is not None


def _fake_run_factory(property_values):
    def _fake_run(cmd, capture_output, text, timeout, check):
        prop = cmd[cmd.index("--property") + 1]
        value = property_values.get(prop)
        if value is None:
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=value + "\n", stderr="")

    return _fake_run


def test_check_service_active_and_enabled(monkeypatch):
    monkeypatch.setattr(services_module, "systemd_available", lambda: True)
    monkeypatch.setattr(
        services_module.subprocess,
        "run",
        _fake_run_factory(
            {"LoadState": "loaded", "ActiveState": "active", "UnitFileState": "enabled"}
        ),
    )

    status = check_service("ssh")

    assert status.active_state == "active"
    assert status.enabled_state == "enabled"
    assert status.error is None


def test_check_service_not_found(monkeypatch):
    monkeypatch.setattr(services_module, "systemd_available", lambda: True)
    monkeypatch.setattr(
        services_module.subprocess,
        "run",
        _fake_run_factory({"LoadState": "not-found"}),
    )

    status = check_service("does-not-exist")

    assert status.active_state == "unknown"
    assert status.error is not None


def test_check_service_query_failure_is_not_reported_as_not_found(monkeypatch):
    monkeypatch.setattr(services_module, "systemd_available", lambda: True)
    monkeypatch.setattr(
        services_module.subprocess,
        "run",
        _fake_run_factory({}),
    )

    status = check_service("ssh")

    assert status.active_state == "unknown"
    assert status.error == "could not query unit 'ssh'"


def test_check_services_multiple(monkeypatch):
    monkeypatch.setattr(services_module, "systemd_available", lambda: True)
    monkeypatch.setattr(
        services_module.subprocess,
        "run",
        _fake_run_factory(
            {"LoadState": "loaded", "ActiveState": "active", "UnitFileState": "enabled"}
        ),
    )

    results = check_services(["ssh", "docker"])

    assert [r.name for r in results] == ["ssh", "docker"]
    assert all(r.active_state == "active" for r in results)
