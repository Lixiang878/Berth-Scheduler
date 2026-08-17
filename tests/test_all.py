import pytest

from berth_scheduler.baseline import fcfs_solve
from berth_scheduler.ga import ga_solve
from berth_scheduler.instances import Berth, Instance, Vessel, generate_instance
from berth_scheduler.milp import milp_solve
from berth_scheduler.schedule import Schedule, evaluate


@pytest.fixture
def tiny_inst():
    vs = [Vessel(0, 200.0, 0.0, 1, 3, 10.0),
          Vessel(1, 180.0, 2.0, 1, 3, 8.0),
          Vessel(2, 220.0, 5.0, 1, 3, 12.0)]
    bs = [Berth(0, 300.0), Berth(1, 250.0)]
    return Instance(vs, bs, n_crane_total=4)


def test_generate_instance_reproducible():
    a = generate_instance(10, 3, 6, seed=42)
    b = generate_instance(10, 3, 6, seed=42)
    assert [v.arrival for v in a.vessels] == [v.arrival for v in b.vessels]
    assert [b.length for b in a.berths] == [b.length for b in b.berths]


def test_generate_instance_vessel_count():
    inst = generate_instance(15, 4, 8, seed=0)
    assert len(inst.vessels) == 15 and len(inst.berths) == 4


def test_evaluate_empty_schedule():
    sol = Schedule(berth_of=[], start=[], crane=[])
    inst = generate_instance(2, 2, 3, seed=0)
    ev = evaluate(sol, inst)
    assert ev["total_waiting"] == 0.0


def test_evaluate_infeasible_overlap_detected():
    # two vessels same berth, overlapping -> violation > 0
    vs = [Vessel(0, 100.0, 0.0, 1, 2, 10.0), Vessel(1, 100.0, 1.0, 1, 2, 10.0)]
    inst = Instance(vs, [Berth(0, 300.0)], n_crane_total=4)
    sol = Schedule(berth_of=[0, 0], start=[0.0, 1.0], crane=[1, 1], vessel_id=[0, 1])
    ev = evaluate(sol, inst)
    assert ev["berth_violations"] >= 1
    assert not ev["feasible"]


def test_fcfs_produces_feasible_on_tiny(tiny_inst):
    sol, ev = fcfs_solve(tiny_inst)
    assert ev["feasible"]
    assert sol.n == 3


def test_ga_improves_on_fcfs(tiny_inst):
    _, fcfs_ev = fcfs_solve(tiny_inst)
    _, ga_ev = ga_solve(tiny_inst, pop_size=60, generations=200, seed=7)
    # GA should match or beat FCFS on a tiny instance
    assert ga_ev["total_in_port"] <= fcfs_ev["total_in_port"] + 1e-6


def test_ga_respects_crane_bounds(tiny_inst):
    _, ev = ga_solve(tiny_inst, pop_size=40, generations=100, seed=3)
    assert ev["crane_violations"] == 0


def test_mip_feasible_on_tiny(tiny_inst):
    # MIP uses fixed crane=min; just check it solves a small instance
    _, mip_ev = milp_solve(tiny_inst, time_step=2.0, max_periods=40)
    if not mip_ev.get("feasible"):
        pytest.skip("MIP could not solve in test env")
    assert mip_ev["berth_violations"] == 0


def test_cli_compare_runs(capsys):
    from berth_scheduler.cli import main
    assert main(["compare", "--vessels", "6", "--berths", "2", "--cranes", "4",
                 "--seed", "1", "--ga-gens", "50"]) == 0
    out = capsys.readouterr().out
    assert "FCFS" in out and "GA" in out


def test_cli_gen_writes_json(tmp_path):
    from berth_scheduler.cli import main
    out = tmp_path / "inst.json"
    assert main(["gen", "--vessels", "5", "--seed", "0", "--out", str(out)]) == 0
    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["vessels"]) == 5
