"""Threshold-based health evaluation tests."""

from __future__ import annotations

from server_monitor.config import MetricThresholds, Thresholds
from server_monitor.health import build_health_report, evaluate_metric, overall_state
from server_monitor.models import DiskInfo, HealthState

THRESHOLDS = MetricThresholds(warning=80.0, critical=95.0)


def test_evaluate_metric_ok_below_warning():
    finding = evaluate_metric("cpu", 50.0, THRESHOLDS)
    assert finding.state == HealthState.OK


def test_evaluate_metric_warning_boundary():
    finding = evaluate_metric("cpu", 80.0, THRESHOLDS)
    assert finding.state == HealthState.WARNING


def test_evaluate_metric_just_below_warning_is_ok():
    finding = evaluate_metric("cpu", 79.9, THRESHOLDS)
    assert finding.state == HealthState.OK


def test_evaluate_metric_critical_boundary():
    finding = evaluate_metric("cpu", 95.0, THRESHOLDS)
    assert finding.state == HealthState.CRITICAL


def test_evaluate_metric_just_below_critical_is_warning():
    finding = evaluate_metric("cpu", 94.9, THRESHOLDS)
    assert finding.state == HealthState.WARNING


def test_evaluate_metric_unknown_when_value_missing():
    finding = evaluate_metric("cpu", None, THRESHOLDS)
    assert finding.state == HealthState.UNKNOWN
    assert finding.value is None


def test_overall_state_picks_most_severe():
    findings = [
        evaluate_metric("cpu", 10.0, THRESHOLDS),
        evaluate_metric("memory", 96.0, THRESHOLDS),
        evaluate_metric("disk", 85.0, THRESHOLDS),
    ]
    assert overall_state(findings) == HealthState.CRITICAL


def test_overall_state_ignores_unknown_when_other_states_present():
    findings = [
        evaluate_metric("cpu", None, THRESHOLDS),
        evaluate_metric("memory", 50.0, THRESHOLDS),
    ]
    assert overall_state(findings) == HealthState.OK


def test_overall_state_unknown_when_all_unknown():
    findings = [evaluate_metric("cpu", None, THRESHOLDS)]
    assert overall_state(findings) == HealthState.UNKNOWN


def test_overall_state_empty_is_unknown():
    assert overall_state([]) == HealthState.UNKNOWN


def test_build_health_report_includes_disk_findings():
    disks = [
        DiskInfo(
            mount_point="/",
            device="/dev/sda1",
            filesystem_type="ext4",
            total_bytes=100,
            used_bytes=96,
            free_bytes=4,
            usage_percent=96.0,
        )
    ]
    thresholds = Thresholds()
    report = build_health_report(
        cpu_usage_percent=10.0, memory_usage_percent=20.0, disks=disks, thresholds=thresholds
    )
    assert report.overall_state == HealthState.CRITICAL
    disk_finding = next(f for f in report.findings if f.metric == "disk:/")
    assert disk_finding.state == HealthState.CRITICAL


def test_build_health_report_disk_error_is_unknown():
    disks = [
        DiskInfo(
            mount_point="/mnt/broken",
            device=None,
            filesystem_type=None,
            total_bytes=0,
            used_bytes=0,
            free_bytes=0,
            usage_percent=0.0,
            error="permission denied",
        )
    ]
    thresholds = Thresholds()
    report = build_health_report(
        cpu_usage_percent=10.0, memory_usage_percent=20.0, disks=disks, thresholds=thresholds
    )
    disk_finding = next(f for f in report.findings if f.metric == "disk:/mnt/broken")
    assert disk_finding.state == HealthState.UNKNOWN
