"""FCFS (first-come-first-served) baseline: greedy earliest-fit assignment."""

from __future__ import annotations

from .instances import Instance
from .schedule import Schedule, evaluate

__all__ = ["fcfs_solve"]


def fcfs_solve(inst: Instance) -> tuple[Schedule, dict]:
    """Greedy: sort by arrival, assign each vessel to the earliest berth
    and crane count that fits. Crane assignment prefers the minimum
    required (spares cranes for later vessels).
    """
    order = sorted(inst.vessels, key=lambda v: v.arrival)
    berth_free = [0.0] * len(inst.berths)  # next free time per berth
    crane_timeline: list[tuple[float, int]] = []  # (time, cranes_released)

    berth_of, start, crane, vid = [], [], [], []
    for v in order:
        best = None
        for bi, b in enumerate(inst.berths):
            if b.length < v.length:
                continue
            # earliest start on this berth respecting prior occupancy
            earliest = max(v.arrival, berth_free[bi])
            # pick a crane count that respects the total-QC budget at that time
            for c in range(v.n_crane_min, v.n_crane_max + 1):
                depart = earliest + v.base_handling / c
                if _crane_available(earliest, depart, c, inst.n_crane_total, crane_timeline) \
                        and (best is None or earliest < best[1]):
                    best = (bi, earliest, c, depart)
        if best is None:
            # fallback: assign to first feasible berth with min cranes, accept overlap
            bi = 0
            for i, b in enumerate(inst.berths):
                if b.length >= v.length:
                    bi = i
                    break
            c = v.n_crane_min
            earliest = max(v.arrival, berth_free[bi])
            depart = earliest + v.base_handling / c
            best = (bi, earliest, c, depart)
        bi, st, c, dep = best
        berth_of.append(bi)
        start.append(st)
        crane.append(c)
        vid.append(v.id)
        berth_free[bi] = dep
        crane_timeline.append((st, c))
        crane_timeline.append((dep, -c))

    sol = Schedule(berth_of=berth_of, start=start, crane=crane, vessel_id=vid)
    return sol, evaluate(sol, inst)


def _crane_available(t0: float, t1: float, need: int, total: int,
                     timeline: list[tuple[float, int]]) -> bool:
    """Check if `need` extra cranes can be granted over [t0, t1)."""
    usage = 0
    for t, delta in timeline:
        if t < t0 or t0 <= t < t1:
            usage += delta
    return usage + need <= total
