"""Process collector tests: sorting, limiting, and resilience to vanished processes."""

from __future__ import annotations

import psutil

from server_monitor.collectors.processes import collect_top_processes


class FakeProcess:
    def __init__(self, pid, name, cpu, memory, raise_on_access=False):
        self.pid = pid
        self._name = name
        self._cpu = cpu
        self._memory = memory
        self._raise_on_access = raise_on_access

    def cpu_percent(self, interval=None):
        if self._raise_on_access:
            raise psutil.NoSuchProcess(self.pid)
        return self._cpu

    def memory_percent(self):
        if self._raise_on_access:
            raise psutil.NoSuchProcess(self.pid)
        return self._memory

    def name(self):
        if self._raise_on_access:
            raise psutil.NoSuchProcess(self.pid)
        return self._name


def test_collect_top_processes_sorts_by_cpu(monkeypatch):
    procs = [
        FakeProcess(1, "low-cpu", cpu=5.0, memory=10.0),
        FakeProcess(2, "high-cpu", cpu=90.0, memory=5.0),
        FakeProcess(3, "mid-cpu", cpu=40.0, memory=20.0),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda *a, **k: iter(procs))

    result = collect_top_processes(sort_by="cpu", limit=10)

    assert [p.pid for p in result] == [2, 3, 1]


def test_collect_top_processes_sorts_by_memory(monkeypatch):
    procs = [
        FakeProcess(1, "a", cpu=5.0, memory=10.0),
        FakeProcess(2, "b", cpu=90.0, memory=5.0),
        FakeProcess(3, "c", cpu=40.0, memory=20.0),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda *a, **k: iter(procs))

    result = collect_top_processes(sort_by="memory", limit=10)

    assert [p.pid for p in result] == [3, 1, 2]


def test_collect_top_processes_respects_limit(monkeypatch):
    procs = [FakeProcess(i, f"proc{i}", cpu=float(i), memory=float(i)) for i in range(5)]
    monkeypatch.setattr(psutil, "process_iter", lambda *a, **k: iter(procs))

    result = collect_top_processes(sort_by="cpu", limit=2)

    assert len(result) == 2
    assert result[0].pid == 4


def test_collect_top_processes_skips_vanished_processes(monkeypatch):
    procs = [
        FakeProcess(1, "alive", cpu=10.0, memory=10.0),
        FakeProcess(2, "vanished", cpu=0.0, memory=0.0, raise_on_access=True),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda *a, **k: iter(procs))

    result = collect_top_processes(sort_by="cpu", limit=10)

    assert len(result) == 1
    assert result[0].pid == 1


def test_collect_top_processes_empty_when_no_processes(monkeypatch):
    monkeypatch.setattr(psutil, "process_iter", lambda *a, **k: iter([]))

    assert collect_top_processes() == []
