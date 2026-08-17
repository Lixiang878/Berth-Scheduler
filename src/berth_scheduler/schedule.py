"""Solution representation and evaluation for berth scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field

from .instances import Instance

__all__ = ["Schedule", "evaluate"]


@dataclass
class Schedule:
    """A schedule assigns each vessel a berth, start time, and crane count.

    `berth_of[i]`, `start[i]`, `crane[i]` give the assignment. The
    corresponding departure time is start + handling / crane (rounded).
    """
    berth_of: list[int]
    start: list[float]
    crane: list[int]
    vessel_id: list[int] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.berth_of)


def _departure(v, start: float, crane: int) -> float:
    return start + v.base_handling / crane


def evaluate(sol: Schedule, inst: Instance) -> dict:
    """Evaluate a schedule: total/avg waiting, makespan, utilisation.

    Checks berth-overlap and crane-total constraints; reports violations
    but still returns metrics so solvers can compare infeasible probes.
    """
    vmap = {v.id: v for v in inst.vessels}
    departures = []
    total_waiting = 0.0
    total_in_port = 0.0
    for i in range(sol.n):
        v = vmap[sol.vessel_id[i]]
        dep = _departure(v, sol.start[i], sol.crane[i])
        departures.append(dep)
        total_waiting += max(0.0, sol.start[i] - v.arrival)
        total_in_port += dep - v.arrival

    # constraint checks
    berth_viol = 0
    for a in range(sol.n):
        for b in range(a + 1, sol.n):
            if sol.berth_of[a] != sol.berth_of[b]:
                continue
            sa, sb = sol.start[a], sol.start[b]
            da, db = departures[a], departures[b]
            if sa < db and sb < da:  # overlap
                berth_viol += 1

    # crane-total violation: aggregate cranes in use over time events
    events = []
    for i in range(sol.n):
        events.append((sol.start[i], sol.crane[i]))
        events.append((departures[i], -sol.crane[i]))
    events.sort()
    crane_viol = 0
    cranes_in_use = 0
    for _, delta in events:
        cranes_in_use += delta
        if cranes_in_use > inst.n_crane_total:
            crane_viol += 1

    return {
        "total_waiting": total_waiting,
        "avg_waiting": total_waiting / max(sol.n, 1),
        "total_in_port": total_in_port,
        "avg_in_port": total_in_port / max(sol.n, 1),
        "makespan": float(max(departures)) if departures else 0.0,
        "berth_violations": berth_viol,
        "crane_violations": crane_viol,
        "feasible": berth_viol == 0 and crane_viol == 0,
    }
