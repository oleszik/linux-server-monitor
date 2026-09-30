"""Configuration parsing/validation tests."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from server_monitor.config import ConfigError, load_config, parse_config


def test_parse_config_defaults_when_empty():
    config = parse_config({})
    assert config.thresholds.cpu.warning == 80.0
    assert config.thresholds.cpu.critical == 95.0
    assert config.thresholds.memory.warning == 80.0
    assert config.thresholds.disk.critical == 90.0
    assert config.services == []


def test_parse_config_overrides_thresholds():
    raw = {
        "thresholds": {"cpu": {"warning": 50, "critical": 70}},
        "services": ["ssh", "docker"],
    }
    config = parse_config(raw)
    assert config.thresholds.cpu.warning == 50.0
    assert config.thresholds.cpu.critical == 70.0
    assert config.services == ["ssh", "docker"]


def test_parse_config_rejects_warning_greater_than_critical():
    raw = {"thresholds": {"cpu": {"warning": 99, "critical": 50}}}
    with pytest.raises(ConfigError, match="warning"):
        parse_config(raw)


def test_parse_config_rejects_negative_thresholds():
    raw = {"thresholds": {"memory": {"warning": -5, "critical": 50}}}
    with pytest.raises(ConfigError):
        parse_config(raw)


@pytest.mark.parametrize("value", [101, math.inf, math.nan])
def test_parse_config_rejects_out_of_range_or_non_finite_thresholds(value):
    raw = {"thresholds": {"memory": {"warning": 50, "critical": value}}}
    with pytest.raises(ConfigError):
        parse_config(raw)


def test_parse_config_rejects_non_numeric_threshold():
    raw = {"thresholds": {"cpu": {"warning": "high", "critical": 95}}}
    with pytest.raises(ConfigError):
        parse_config(raw)


def test_parse_config_rejects_unknown_metric():
    raw = {"thresholds": {"gpu": {"warning": 10, "critical": 20}}}
    with pytest.raises(ConfigError, match="unknown threshold metric"):
        parse_config(raw)


def test_parse_config_rejects_unknown_top_level_key():
    with pytest.raises(ConfigError, match="unknown configuration key"):
        parse_config({"service": ["ssh"]})


def test_parse_config_rejects_unknown_threshold_key():
    with pytest.raises(ConfigError, match="unknown thresholds.cpu key"):
        parse_config({"thresholds": {"cpu": {"warn": 80}}})


def test_parse_config_rejects_non_mapping_top_level():
    with pytest.raises(ConfigError):
        parse_config([])  # type: ignore[arg-type]


def test_parse_config_rejects_non_list_services():
    with pytest.raises(ConfigError):
        parse_config({"services": "ssh"})


def test_parse_config_rejects_non_string_service_items():
    with pytest.raises(ConfigError):
        parse_config({"services": ["ssh", 123]})


def test_parse_config_rejects_empty_service_name():
    with pytest.raises(ConfigError):
        parse_config({"services": ["ssh", "  "]})


def test_load_config_returns_defaults_for_none_path():
    config = load_config(None)
    assert config.thresholds.cpu.warning == 80.0


def test_load_config_reads_valid_yaml(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "thresholds:\n  cpu:\n    warning: 60\n    critical: 90\nservices:\n  - ssh\n"
    )
    config = load_config(config_file)
    assert config.thresholds.cpu.warning == 60.0
    assert config.services == ["ssh"]


def test_load_config_missing_file_raises_config_error(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "does-not-exist.yaml")


def test_load_config_malformed_yaml_raises_config_error(tmp_path: Path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("thresholds: [unbalanced\n")
    with pytest.raises(ConfigError):
        load_config(config_file)
