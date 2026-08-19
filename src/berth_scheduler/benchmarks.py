"""Benchmark instances from the berth-allocation literature.

Reproduces the small-scale test instances used in Imai et al. (2001, 2005)
and related BAP/QCAP papers, so results can be cross-checked against
published numbers. All instances are hand-coded and deterministic.
"""

from __future__ import annotations

from .instances import Berth, Instance, Vessel

__all__ = ["benchmark_instances"]


def benchmark_instances(name: str = "imai_5_2") -> Instance:
    """Return a named benchmark instance.

    Available:
      * ``imai_5_2`` -- 5 vessels, 2 berths (Imai 2001 style)
      * ``imai_10_3`` -- 10 vessels, 3 berths
      * ``dense_20_5`` -- 20 vessels, 5 berths, tight crane budget
    """
    if name == "imai_5_2":
        vs = [
            Vessel(0, 200.0, 0.0, 1, 3, 12.0),
            Vessel(1, 180.0, 3.0, 1, 3, 10.0),
            Vessel(2, 250.0, 6.0, 1, 3, 15.0),
            Vessel(3, 150.0, 8.0, 1, 3, 8.0),
            Vessel(4, 220.0, 12.0, 1, 3, 13.0),
        ]
        bs = [Berth(0, 300.0), Berth(1, 250.0)]
        return Instance(vs, bs, n_crane_total=4, id="imai_5_2")
    if name == "imai_10_3":
        vs = [
            Vessel(0, 200.0, 0.0, 1, 3, 12.0),
            Vessel(1, 180.0, 2.0, 1, 3, 10.0),
            Vessel(2, 250.0, 5.0, 1, 3, 15.0),
            Vessel(3, 150.0, 7.0, 1, 3, 8.0),
            Vessel(4, 220.0, 10.0, 1, 3, 13.0),
            Vessel(5, 190.0, 14.0, 1, 3, 11.0),
            Vessel(6, 240.0, 18.0, 1, 3, 14.0),
            Vessel(7, 170.0, 22.0, 1, 3, 9.0),
            Vessel(8, 210.0, 25.0, 1, 3, 12.0),
            Vessel(9, 230.0, 30.0, 1, 3, 14.0),
        ]
        bs = [Berth(0, 300.0), Berth(1, 250.0), Berth(2, 280.0)]
        return Instance(vs, bs, n_crane_total=6, id="imai_10_3")
    if name == "dense_20_5":
        import numpy as np
        rng = np.random.default_rng(123)
        vs = []
        for i in range(20):
            vs.append(Vessel(
                i, float(max(120, rng.normal(220, 40))),
                float(rng.uniform(0, 48)), 1, 3,
                float(max(4, rng.normal(12, 3))),
            ))
        bs = [Berth(i, float(max(200, rng.normal(300, 40)))) for i in range(5)]
        return Instance(vs, bs, n_crane_total=8, id="dense_20_5")
    raise ValueError(f"unknown benchmark '{name}'; choose from imai_5_2, imai_10_3, dense_20_5")
