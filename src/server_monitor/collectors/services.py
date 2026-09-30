"""systemd service status checks via ``systemctl`` (read-only, no root needed)."""

from __future__ import annotations

import os
import shutil
import subprocess

from server_monitor.models import ServiceStatus

_UNSUPPORTED_MESSAGE = "systemd is not available on this system"


def systemd_available() -> bool:
    """Return True if this host appears to be running systemd."""
    if shutil.which("systemctl") is None:
        return False
    try:
        return os.path.isdir("/run/systemd/system")
    except OSError:
        return False


def _query_property(unit: str, prop: str) -> str | None:
    try:
        result = subprocess.run(
            ["systemctl", "show", "--property", prop, "--value", "--", unit],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def check_service(name: str) -> ServiceStatus:
    """Check a single systemd unit's active/enabled state.

    Does not require root. If the unit does not exist, ``active_state``
    is reported as ``unknown`` with an explanatory error rather than
    raising.
    """
    if not systemd_available():
        return ServiceStatus(
            name=name,
            active_state="unknown",
            enabled_state="unknown",
            supported=False,
            error=_UNSUPPORTED_MESSAGE,
        )

    load_state = _query_property(name, "LoadState")
    if load_state is None:
        return ServiceStatus(
            name=name,
            active_state="unknown",
            enabled_state="unknown",
            error=f"could not query unit '{name}'",
        )
    if load_state == "not-found":
        return ServiceStatus(
            name=name,
            active_state="unknown",
            enabled_state="unknown",
            error=f"unit '{name}' not found",
        )

    active_state = _query_property(name, "ActiveState") or "unknown"
    enabled_state = _query_property(name, "UnitFileState") or "unknown"

    return ServiceStatus(
        name=name,
        active_state=active_state,
        enabled_state=enabled_state,
    )


def check_services(names: list[str]) -> list[ServiceStatus]:
    """Check the requested list of systemd units."""
    return [check_service(name) for name in names]
