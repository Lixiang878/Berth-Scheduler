"""MIP exact solver for berth allocation (discrete-time BAP, crane=min).

Small-scale ground truth for validating the GA: assigns each vessel to
one berth and one start period, crane count fixed at the vessel minimum.
Practical up to ~8 vessels. Beyond that the GA is the right tool.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .instances import Instance
from .schedule import Schedule, evaluate

__all__ = ["milp_solve"]


def milp_solve(inst: Instance, time_step: float = 2.0, max_periods: int = 60):
    vessels = inst.vessels
    berths = inst.berths
    n = len(vessels)
    B = len(berths)
    horizon = max(v.arrival for v in vessels) + max(v.base_handling for v in vessels) * 2 + 24
    T = min(max_periods, int(np.ceil(horizon / time_step)))

    # x[i,b,s] binary: vessel i starts at berth b, period s
    nvar = n * B * T

    # minimise total in-port time
    c_obj = np.zeros(nvar)
    for i, v in enumerate(vessels):
        c = v.n_crane_min
        handling = v.base_handling / c
        for b in range(B):
            for s in range(T):
                t_start = s * time_step
                c_obj[i * B * T + b * T + s] = t_start + handling - v.arrival

    constraints = []
    # each vessel: exactly one (berth, start)
    A = np.zeros((n, nvar))
    for i in range(n):
        for b in range(B):
            for s in range(T):
                A[i, i * B * T + b * T + s] = 1.0
    constraints.append(LinearConstraint(A, 1, 1))

    # berth non-overlap: at each (berth, period), sum of vessels occupying it <= 1
    rows = []
    for b in range(B):
        for t in range(T):
            row = np.zeros(nvar)
            for i, v in enumerate(vessels):
                c = v.n_crane_min
                handling = v.base_handling / c
                h_periods = max(1, int(np.ceil(handling / time_step)))
                for s in range(max(0, t - h_periods + 1), min(T, t + 1)):
                    row[i * B * T + b * T + s] = 1.0
            if row.sum() > 0:
                rows.append(row)
    if rows:
        A2 = np.vstack(rows)
        constraints.append(LinearConstraint(A2, 0, 1))

    # berth length compatibility
    lb = np.zeros(nvar)
    ub = np.ones(nvar)
    for i, v in enumerate(vessels):
        for b, berth in enumerate(berths):
            if berth.length < v.length:
                for s in range(T):
                    ub[i * B * T + b * T + s] = 0.0
        # start no earlier than arrival: forbid periods that begin before arrival
        min_period = int(np.ceil(v.arrival / time_step))
        for b in range(B):
            for s in range(min_period):
                ub[i * B * T + b * T + s] = 0.0

    res = milp(c=c_obj, constraints=constraints, integrality=np.ones(nvar, dtype=int),
               bounds=Bounds(lb, ub))
    if res.status != 0:
        return None, {"status": res.message, "feasible": False}

    x = res.x.reshape(n, B, T)
    berth_of, start, crane, vid = [], [], [], []
    for i, v in enumerate(vessels):
        pos = np.argwhere(x[i] > 0.5)
        if len(pos) == 0:
            continue
        b, s = int(pos[0][0]), int(pos[0][1])
        berth_of.append(b); start.append(s * time_step); crane.append(v.n_crane_min); vid.append(v.id)

    sol = Schedule(berth_of=berth_of, start=start, crane=crane, vessel_id=vid)
    ev = evaluate(sol, inst)
    ev["milp_obj"] = float(res.fun)
    ev["milp_status"] = res.message
    return sol, ev
