"""Disk collector tests (pseudo-fs filtering, permission errors)."""

from __future__ import annotations

from collections import namedtuple

import psutil

from server_monitor.collectors.disk import collect_disk_info

Partition = namedtuple("Partition", ["device", "mountpoint", "fstype", "opts"])
DiskUsage = namedtuple("DiskUsage", ["total", "used", "free", "percent"])


def test_collect_disk_info_filters_pseudo_filesystems(monkeypatch):
    partitions = [
        Partition("/dev/sda1", "/", "ext4", "rw"),
        Partition("tmpfs", "/run", "tmpfs", "rw"),
        Partition("overlay", "/var/lib/docker/overlay2/x", "overlay", "rw"),
    ]
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: partitions)
    monkeypatch.setattr(psutil, "disk_usage", lambda path: DiskUsage(100, 40, 60, 40.0))

    disks = collect_disk_info()

    assert len(disks) == 1
    assert disks[0].mount_point == "/"
    assert disks[0].usage_percent == 40.0


def test_collect_disk_info_includes_pseudo_when_requested(monkeypatch):
    partitions = [Partition("tmpfs", "/run", "tmpfs", "rw")]
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: partitions)
    monkeypatch.setattr(psutil, "disk_usage", lambda path: DiskUsage(100, 10, 90, 10.0))

    disks = collect_disk_info(include_pseudo=True)

    assert len(disks) == 1
    assert disks[0].mount_point == "/run"


def test_collect_disk_info_handles_permission_error(monkeypatch):
    partitions = [Partition("/dev/sdb1", "/mnt/locked", "ext4", "rw")]
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: partitions)

    def _raise_permission_error(path):
        raise PermissionError("denied")

    monkeypatch.setattr(psutil, "disk_usage", _raise_permission_error)

    disks = collect_disk_info()

    assert len(disks) == 1
    assert disks[0].error is not None
    assert disks[0].mount_point == "/mnt/locked"


def test_collect_disk_info_empty_when_no_partitions(monkeypatch):
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: [])

    assert collect_disk_info() == []
