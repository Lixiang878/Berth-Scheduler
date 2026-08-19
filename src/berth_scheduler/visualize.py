"""Gantt chart visualisation for berth schedules."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .schedule import Schedule

__all__ = ["plot_gantt"]


def plot_gantt(sol: Schedule, inst, title: str = "Berth schedule", ax=None):
    """Render a Gantt chart: vessels as coloured bars along berths."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    n_berths = max(inst.berths, key=lambda b: b.id).id + 1 if inst.berths else 1
    cmap = plt.cm.get_cmap("tab20", max(sol.n, 1))
    vmap = {v.id: v for v in inst.vessels}
    for i in range(sol.n):
        v = vmap[sol.vessel_id[i]]
        dur = v.base_handling / sol.crane[i]
        ax.barh(sol.berth_of[i], dur, left=sol.start[i], height=0.6,
                color=cmap(i), edgecolor="white", linewidth=0.5)
        if dur > 2:
            ax.text(sol.start[i] + dur / 2, sol.berth_of[i], f"v{v.id}",
                    ha="center", va="center", fontsize=7, color="white")
    ax.set_yticks(range(n_berths))
    ax.set_yticklabels([f"Berth {b.id}" for b in inst.berths])
    ax.set_xlabel("time (h)")
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()
    return ax
