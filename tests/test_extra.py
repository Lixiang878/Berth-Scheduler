"""Tests for visualisation and benchmarks."""

import matplotlib

matplotlib.use("Agg")

import pytest

from berth_scheduler.benchmarks import benchmark_instances
from berth_scheduler.ga import ga_solve
from berth_scheduler.visualize import plot_gantt


def test_benchmark_imai_5_2():
    inst = benchmark_instances("imai_5_2")
    assert len(inst.vessels) == 5 and len(inst.berths) == 2
    assert inst.n_crane_total == 4


def test_benchmark_imai_10_3():
    inst = benchmark_instances("imai_10_3")
    assert len(inst.vessels) == 10 and len(inst.berths) == 3


def test_benchmark_dense_20_5():
    inst = benchmark_instances("dense_20_5")
    assert len(inst.vessels) == 20 and len(inst.berths) == 5


def test_benchmark_unknown_raises():
    with pytest.raises(ValueError):
        benchmark_instances("nonexistent")


def test_plot_gantt_returns_ax():
    inst = benchmark_instances("imai_5_2")
    sol, _ = ga_solve(inst, generations=100, seed=0)
    ax = plot_gantt(sol, inst)
    assert ax is not None


def test_ga_on_benchmark_improves_fcfs():
    from berth_scheduler.baseline import fcfs_solve
    inst = benchmark_instances("imai_5_2")
    _, fcfs_ev = fcfs_solve(inst)
    _, ga_ev = ga_solve(inst, generations=200, seed=3)
    assert ga_ev["total_in_port"] <= fcfs_ev["total_in_port"] + 1e-6
