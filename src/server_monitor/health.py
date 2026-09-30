"""Threshold-based health evaluation, decoupled from collection and presentation."""

from __future__ import annotations

from server_monitor.config import MetricThresholds, Thresholds
from server_monitor.models import (
    DiskInfo,
    Finding,
    HealthReport,
    HealthState,
)

_STATE_SEVERITY = {
    HealthState.UNKNOWN: 0,
    HealthState.OK: 1,
    HealthState.WARNING: 2,
    HealthState.CRITICAL: 3,
}


def evaluate_metric(metric: str, value: float | None, thresholds: MetricThresholds) -> Finding:
    """Evaluate a single numeric metric (e.g. usage percentage) against thresholds."""
    if value is None:
        return Finding(
            metric=metric,
            state=HealthState.UNKNOWN,
            value=None,
            warning_threshold=thresholds.warning,
            critical_threshold=thresholds.critical,
            message=f"{metric}: value unavailable",
        )

    if value >= thresholds.critical:
        state = HealthState.CRITICAL
    elif value >= thresholds.warning:
        state = HealthState.WARNING
    else:
        state = HealthState.OK

    return Finding(
        metric=metric,
        state=state,
        value=value,
        warning_threshold=thresholds.warning,
        critical_threshold=thresholds.critical,
        message=f"{metric}: {value:.1f}% (warning >= {thresholds.warning}%, "
        f"critical >= {thresholds.critical}%)",
    )


def evaluate_disks(disks: list[DiskInfo], thresholds: MetricThresholds) -> list[Finding]:
    """Evaluate each mounted filesystem's usage percentage independently."""
    findings = []
    for disk in disks:
        metric = f"disk:{disk.mount_point}"
        if disk.error:
            findings.append(
                Finding(
                    metric=metric,
                    state=HealthState.UNKNOWN,
                    value=None,
                    warning_threshold=thresholds.warning,
                    critical_threshold=thresholds.critical,
                    message=f"{metric}: unavailable ({disk.error})",
                )
            )
            continue
        findings.append(evaluate_metric(metric, disk.usage_percent, thresholds))
    return findings


def overall_state(findings: list[Finding]) -> HealthState:
    """Return the most severe state across all findings (CRITICAL > WARNING > OK > UNKNOWN)."""
    if not findings:
        return HealthState.UNKNOWN

    worst = max(findings, key=lambda f: _STATE_SEVERITY[f.state])
    if worst.state == HealthState.UNKNOWN:
        # UNKNOWN only wins outright if nothing else reported a real state.
        non_unknown = [f for f in findings if f.state != HealthState.UNKNOWN]
        if non_unknown:
            worst = max(non_unknown, key=lambda f: _STATE_SEVERITY[f.state])
    return worst.state


def build_health_report(
    cpu_usage_percent: float | None,
    memory_usage_percent: float | None,
    disks: list[DiskInfo],
    thresholds: Thresholds,
) -> HealthReport:
    """Evaluate CPU, memory, and disk metrics into a combined health report."""
    findings = [
        evaluate_metric("cpu", cpu_usage_percent, thresholds.cpu),
        evaluate_metric("memory", memory_usage_percent, thresholds.memory),
        *evaluate_disks(disks, thresholds.disk),
    ]
    return HealthReport(overall_state=overall_state(findings), findings=findings)
