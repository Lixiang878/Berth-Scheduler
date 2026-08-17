"""Data structures and random instance generation for berth scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["Berth", "Instance", "Vessel", "generate_instance"]


@dataclass
class Vessel:
    id: int
    length: float  # m
    arrival: float  # h, time of arrival at the terminal
    n_crane_min: int  # minimum quay cranes required
    n_crane_max: int  # maximum quay cranes assignable
    base_handling: float  # h, handling time with 1 crane; scales inversely


@dataclass
class Berth:
    id: int
    length: float  # m


@dataclass
class Instance:
    vessels: list[Vessel]
    berths: list[Berth]
    n_crane_total: int
    id: str = ""
    extra: dict = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"Instance({len(self.vessels)} vessels, {len(self.berths)} berths, "
            f"{self.n_crane_total} QC)"
        )


def generate_instance(
    n_vessels: int = 20,
    n_berths: int = 3,
    n_crane_total: int = 6,
    length_mean: float = 250.0,
    length_std: float = 60.0,
    arrival_span: float = 48.0,
    handling_mean: float = 12.0,
    handling_std: float = 4.0,
    seed: int | None = None,
) -> Instance:
    """Generate a random berth-allocation instance with realistic spread.

    Vessel arrivals are spread uniformly over `arrival_span`. Handling time
    scales inversely with assigned cranes: actual = base / n_crane, clamped
    at [n_crane_min, n_crane_max] per vessel. Berth lengths are drawn once
    per instance and shared.
    """
    rng = np.random.default_rng(seed)
    vessels = []
    for i in range(n_vessels):
        length = max(80.0, rng.normal(length_mean, length_std))
        arrival = rng.uniform(0.0, arrival_span)
        base_h = max(2.0, rng.normal(handling_mean, handling_std))
        nmax = int(rng.integers(2, max(3, n_crane_total // 2 + 1)))
        nmax = max(nmax, 2)
        nmin = int(rng.integers(1, nmax))
        vessels.append(Vessel(i, float(length), float(arrival), nmin, nmax, float(base_h)))
    berths = [Berth(i, float(max(200.0, rng.normal(300.0, 50.0)))) for i in range(n_berths)]
    return Instance(vessels=vessels, berths=berths, n_crane_total=n_crane_total,
                    id=f"rand_v{n_vessels}_b{n_berths}_c{n_crane_total}_s{seed}")
