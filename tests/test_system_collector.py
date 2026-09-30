"""System info collector tests."""

from __future__ import annotations

import psutil

from server_monitor.collectors import system as system_module
from server_monitor.collectors.system import collect_system_info


def test_collect_system_info_happy_path(monkeypatch):
    monkeypatch.setattr(system_module.socket, "gethostname", lambda: "myhost")
    monkeypatch.setattr(system_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system_module.platform, "release", lambda: "6.8.0-generic")
    monkeypatch.setattr(system_module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system_module, "_read_os_release", lambda: "Ubuntu 24.04 LTS")
    monkeypatch.setattr(psutil, "boot_time", lambda: 1000.0)
    monkeypatch.setattr(system_module.time, "time", lambda: 1500.0)

    info = collect_system_info()

    assert info.hostname == "myhost"
    assert info.os_name == "Linux"
    assert info.os_version == "Ubuntu 24.04 LTS"
    assert info.kernel_version == "6.8.0-generic"
    assert info.architecture == "x86_64"
    assert info.uptime_seconds == 500.0


def test_collect_system_info_hostname_failure_falls_back(monkeypatch):
    def _raise():
        raise OSError("no hostname")

    monkeypatch.setattr(system_module.socket, "gethostname", _raise)
    monkeypatch.setattr(system_module, "_read_os_release", lambda: "Linux")

    info = collect_system_info()

    assert info.hostname == "unknown"


def test_collect_system_info_uptime_unavailable(monkeypatch):
    monkeypatch.setattr(system_module.socket, "gethostname", lambda: "myhost")
    monkeypatch.setattr(system_module, "_read_os_release", lambda: "Linux")

    def _raise():
        raise OSError("boot time unavailable")

    monkeypatch.setattr(psutil, "boot_time", _raise)

    info = collect_system_info()

    assert info.uptime_seconds is None


def test_read_os_release_parses_pretty_name(tmp_path, monkeypatch):
    os_release = tmp_path / "os-release"
    os_release.write_text('NAME="Ubuntu"\nPRETTY_NAME="Ubuntu 24.04.5 LTS"\n')
    real_open = open

    def _fake_open(path, *args, **kwargs):
        if path == "/etc/os-release":
            return real_open(os_release, *args, **kwargs)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _fake_open)

    assert system_module._read_os_release() == "Ubuntu 24.04.5 LTS"


def test_read_os_release_missing_file_falls_back(monkeypatch):
    def _raise(*args, **kwargs):
        raise OSError("not found")

    monkeypatch.setattr("builtins.open", _raise)
    monkeypatch.setattr(system_module.platform, "system", lambda: "Linux")

    assert system_module._read_os_release() == "Linux"
