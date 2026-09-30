"""Configuration loading and validation for thresholds and monitored services."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration is malformed or contradictory."""


@dataclass
class MetricThresholds:
    warning: float
    critical: float


@dataclass
class Thresholds:
    cpu: MetricThresholds = field(default_factory=lambda: MetricThresholds(80.0, 95.0))
    memory: MetricThresholds = field(default_factory=lambda: MetricThresholds(80.0, 95.0))
    disk: MetricThresholds = field(default_factory=lambda: MetricThresholds(80.0, 90.0))


@dataclass
class Config:
    thresholds: Thresholds = field(default_factory=Thresholds)
    services: list[str] = field(default_factory=list)


_DEFAULT_METRIC_THRESHOLDS = {
    "cpu": (80.0, 95.0),
    "memory": (80.0, 95.0),
    "disk": (80.0, 90.0),
}


def _parse_metric_thresholds(metric: str, raw: Any) -> MetricThresholds:
    default_warning, default_critical = _DEFAULT_METRIC_THRESHOLDS[metric]
    if raw is None:
        return MetricThresholds(default_warning, default_critical)
    if not isinstance(raw, dict):
        raise ConfigError(f"thresholds.{metric} must be a mapping with 'warning'/'critical' keys")

    unknown_keys = set(raw) - {"warning", "critical"}
    if unknown_keys:
        raise ConfigError(f"unknown thresholds.{metric} key(s): {', '.join(sorted(unknown_keys))}")

    warning = raw.get("warning", default_warning)
    critical = raw.get("critical", default_critical)

    for key, value in (("warning", warning), ("critical", critical)):
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise ConfigError(f"thresholds.{metric}.{key} must be a number")

    warning = float(warning)
    critical = float(critical)

    if not math.isfinite(warning) or not math.isfinite(critical):
        raise ConfigError(f"thresholds.{metric}: thresholds must be finite numbers")
    if warning > critical:
        raise ConfigError(
            f"thresholds.{metric}: warning ({warning}) must not be greater than "
            f"critical ({critical})"
        )
    if warning < 0 or critical > 100:
        raise ConfigError(f"thresholds.{metric}: thresholds must be between 0 and 100")

    return MetricThresholds(warning, critical)


def parse_config(raw: dict[str, Any]) -> Config:
    """Validate a parsed configuration mapping and build a `Config`."""
    if not isinstance(raw, dict):
        raise ConfigError("configuration must be a mapping at the top level")

    unknown_keys = set(raw) - {"thresholds", "services"}
    if unknown_keys:
        raise ConfigError(f"unknown configuration key(s): {', '.join(sorted(unknown_keys))}")

    raw_thresholds = raw.get("thresholds", {}) or {}
    if not isinstance(raw_thresholds, dict):
        raise ConfigError("'thresholds' must be a mapping")

    unknown_metrics = set(raw_thresholds) - set(_DEFAULT_METRIC_THRESHOLDS)
    if unknown_metrics:
        raise ConfigError(f"unknown threshold metric(s): {', '.join(sorted(unknown_metrics))}")

    thresholds = Thresholds(
        cpu=_parse_metric_thresholds("cpu", raw_thresholds.get("cpu")),
        memory=_parse_metric_thresholds("memory", raw_thresholds.get("memory")),
        disk=_parse_metric_thresholds("disk", raw_thresholds.get("disk")),
    )

    services = raw.get("services", []) or []
    if not isinstance(services, list) or not all(
        isinstance(service, str) and service.strip() for service in services
    ):
        raise ConfigError("'services' must be a list of non-empty service names")

    return Config(thresholds=thresholds, services=[service.strip() for service in services])


def load_config(path: Path | None) -> Config:
    """Load configuration from a YAML file, or return defaults if ``path`` is None."""
    if path is None:
        return Config()

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"could not read configuration file '{path}': {exc}") from exc

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in configuration file '{path}': {exc}") from exc

    if raw is None:
        raw = {}

    return parse_config(raw)
