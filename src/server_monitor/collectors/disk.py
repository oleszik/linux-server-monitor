"""Disk usage collection for real (non-pseudo) mounted filesystems."""

from __future__ import annotations

import psutil

from server_monitor.models import DiskInfo

# Pseudo/virtual filesystem types that don't represent real storage and
# would otherwise clutter a disk usage report.
_PSEUDO_FS_TYPES = {
    "autofs",
    "binfmt_misc",
    "bpf",
    "cgroup",
    "cgroup2",
    "configfs",
    "debugfs",
    "devpts",
    "devtmpfs",
    "efivarfs",
    "fuse.gvfsd-fuse",
    "fusectl",
    "hugetlbfs",
    "mqueue",
    "nsfs",
    "overlay",
    "proc",
    "pstore",
    "ramfs",
    "rpc_pipefs",
    "securityfs",
    "squashfs",
    "sysfs",
    "tmpfs",
    "tracefs",
}


def collect_disk_info(include_pseudo: bool = False) -> list[DiskInfo]:
    """Collect usage information for mounted filesystems.

    By default, pseudo/virtual filesystems (tmpfs, proc, sysfs, overlay
    used by containers, etc.) are excluded so the report stays focused on
    real storage. Individual mounts that fail to report usage (e.g. due to
    permissions or a stale network mount) are still included with an error
    message rather than aborting the whole collection.
    """
    disks: list[DiskInfo] = []
    try:
        partitions = psutil.disk_partitions(all=include_pseudo)
    except (OSError, psutil.Error):
        partitions = []

    for partition in partitions:
        if not include_pseudo and partition.fstype in _PSEUDO_FS_TYPES:
            continue

        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (PermissionError, OSError) as exc:
            disks.append(
                DiskInfo(
                    mount_point=partition.mountpoint,
                    device=partition.device or None,
                    filesystem_type=partition.fstype or None,
                    total_bytes=0,
                    used_bytes=0,
                    free_bytes=0,
                    usage_percent=0.0,
                    error=str(exc),
                )
            )
            continue

        disks.append(
            DiskInfo(
                mount_point=partition.mountpoint,
                device=partition.device or None,
                filesystem_type=partition.fstype or None,
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
                usage_percent=usage.percent,
            )
        )

    return disks
