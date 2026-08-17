"""Adaptive genetic algorithm for berth allocation + crane assignment.

Chromosome = permutation of vessel ids (processing order) + per-vessel
crane count. Decoded by a greedy earliest-fit scheduler that respects the
permutation. Crossover/mutation rates adapt from population diversity.
"""

from __future__ import annotations

import numpy as np

from .instances import Instance
from .schedule import Schedule, evaluate

__all__ = ["ga_solve"]


def ga_solve(
    inst: Instance,
    pop_size: int = 80,
    generations: int = 300,
    elite: int = 4,
    seed: int | None = None,
    target: str = "total_in_port",
) -> tuple[Schedule, dict]:
    rng = np.random.default_rng(seed)
    n = len(inst.vessels)
    vessels = inst.vessels

    def _random_chr():
        perm = rng.permutation(n)
        crs = [int(rng.integers(v.n_crane_min, v.n_crane_max + 1)) for v in vessels]
        return perm, crs

    def decode(perm, crs):
        berth_free = [0.0] * len(inst.berths)
        b_of, st, cr, vid = [], [], [], []
        for idx in perm:
            v = vessels[idx]
            c = max(v.n_crane_min, min(v.n_crane_max, int(crs[idx])))
            best = None
            for bi, b in enumerate(inst.berths):
                if b.length < v.length:
                    continue
                earliest = max(v.arrival, berth_free[bi])
                depart = earliest + v.base_handling / c
                if best is None or earliest < best[1]:
                    best = (bi, earliest, depart)
            if best is None:
                bi = 0
                for i, b in enumerate(inst.berths):
                    if b.length >= v.length:
                        bi = i
                        break
                earliest = max(v.arrival, berth_free[bi])
                depart = earliest + v.base_handling / c
                best = (bi, earliest, depart)
            bi, s, d = best
            b_of.append(bi); st.append(s); cr.append(c); vid.append(v.id)
            berth_free[bi] = d
        sol = Schedule(berth_of=b_of, start=st, crane=cr, vessel_id=vid)
        return sol, evaluate(sol, inst)

    def fitness(perm, crs):
        _, ev = decode(perm, crs)
        penalty = (ev["berth_violations"] + ev["crane_violations"]) * 1e4
        return ev[target] + penalty

    pop = [_random_chr() for _ in range(pop_size)]
    scores = np.array([fitness(p, c) for p, c in pop])
    best_idx = int(np.argmin(scores))
    best = pop[best_idx]
    best_score = float(scores[best_idx])
    history = [best_score]

    for _ in range(generations):
        div = float(scores.std() / max(abs(scores.mean()), 1e-9))
        pc = min(0.95, 0.6 + 0.35 * np.tanh(div))
        pm = max(0.02, 0.5 - 0.45 * np.tanh(div))

        new_pop = [pop[best_idx] for _ in range(min(elite, pop_size))]
        while len(new_pop) < pop_size:
            p1 = _tournament(pop, scores, rng)
            p2 = _tournament(pop, scores, rng)
            c1 = _crossover(p1, p2, pc, pm, vessels, rng)
            c2 = _crossover(p2, p1, pc, pm, vessels, rng)
            new_pop.append(c1)
            if len(new_pop) < pop_size:
                new_pop.append(c2)
        pop = new_pop[:pop_size]
        scores = np.array([fitness(p, c) for p, c in pop])
        gen_best = int(np.argmin(scores))
        if scores[gen_best] < best_score:
            best_score = float(scores[gen_best])
            best = pop[gen_best]
        history.append(float(best_score))

    sol, ev = decode(best[0], best[1])
    ev["ga_history"] = history
    ev["generations"] = generations
    return sol, ev


def _tournament(pop, scores, rng, k=3):
    idxs = rng.choice(len(pop), size=k, replace=False)
    best = idxs[int(np.argmin(scores[idxs]))]
    return pop[best]


def _crossover(a, b, pc, pm, vessels, rng):
    pa, ca = a
    pb, cb = b
    n = len(pa)
    if rng.random() < pc:
        # order crossover on permutation + uniform on cranes
        cut1, cut2 = sorted(rng.choice(n, 2, replace=False).tolist())
        child_p = np.full(n, -1, dtype=int)
        child_p[cut1:cut2 + 1] = pa[cut1:cut2 + 1]
        used = set(child_p[cut1:cut2 + 1].tolist())
        fill = [g for g in pb if g not in used]
        j = 0
        for i in range(n):
            if child_p[i] == -1:
                child_p[i] = fill[j]
                j += 1
        child_c = [ca[i] if rng.random() < 0.5 else cb[i] for i in range(n)]
    else:
        child_p = pa.copy()
        child_c = list(ca)
    # mutation: swap two vessels + jitter one crane
    if rng.random() < pm:
        i, j = rng.choice(n, 2, replace=False)
        child_p[i], child_p[j] = child_p[j], child_p[i]
    if rng.random() < pm:
        k = int(rng.integers(0, n))
        v = vessels[child_p[k]]
        child_c[k] = int(rng.integers(v.n_crane_min, v.n_crane_max + 1))
    return child_p, child_c
