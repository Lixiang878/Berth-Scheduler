"""CLI: python -m berth_scheduler / berth-scheduler <subcommand>."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="berth-scheduler",
                                     description="Berth allocation + quay-crane scheduling")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("gen", help="generate a random instance")
    gen.add_argument("--vessels", type=int, default=20)
    gen.add_argument("--berths", type=int, default=3)
    gen.add_argument("--cranes", type=int, default=6)
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--out", default="instance.json")

    compare = sub.add_parser("compare", help="run FCFS, GA (and MIP if small) and compare")
    compare.add_argument("--vessels", type=int, default=12)
    compare.add_argument("--berths", type=int, default=3)
    compare.add_argument("--cranes", type=int, default=6)
    compare.add_argument("--seed", type=int, default=0)
    compare.add_argument("--ga-gens", type=int, default=300)

    bench = sub.add_parser("bench", help="run on a named benchmark instance")
    bench.add_argument("--name", default="imai_5_2",
                       choices=["imai_5_2", "imai_10_3", "dense_20_5"])
    bench.add_argument("--ga-gens", type=int, default=300)

    sens = sub.add_parser("sensitivity", help="sweep GA performance vs crane count")
    sens.add_argument("--vessels", type=int, default=12)
    sens.add_argument("--berths", type=int, default=3)
    sens.add_argument("--cranes-min", type=int, default=3)
    sens.add_argument("--cranes-max", type=int, default=10)
    sens.add_argument("--ga-gens", type=int, default=200)

    plot = sub.add_parser("plot", help="draw a Gantt chart for a benchmark schedule")
    plot.add_argument("--name", default="imai_5_2")
    plot.add_argument("--out", default="results/gantt.png")

    args = parser.parse_args(argv)

    if args.cmd == "gen":
        from .instances import generate_instance
        inst = generate_instance(args.vessels, args.berths, args.cranes, seed=args.seed)
        data = {
            "n_crane_total": inst.n_crane_total,
            "vessels": [{"id": v.id, "length": v.length, "arrival": v.arrival,
                         "crane_min": v.n_crane_min, "crane_max": v.n_crane_max,
                         "base_handling": v.base_handling} for v in inst.vessels],
            "berths": [{"id": b.id, "length": b.length} for b in inst.berths],
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(inst.summary(), "->", args.out)
        return 0

    if args.cmd in ("compare", "bench"):
        from .baseline import fcfs_solve
        from .benchmarks import benchmark_instances
        from .ga import ga_solve
        from .instances import generate_instance
        from .milp import milp_solve
        if args.cmd == "bench":
            inst = benchmark_instances(args.name)
        else:
            inst = generate_instance(args.vessels, args.berths, args.cranes, seed=args.seed)
        print(inst.summary())

        _, fcfs_ev = fcfs_solve(inst)
        _, ga_ev = ga_solve(inst, generations=args.ga_gens, seed=42)

        rows = {"FCFS": fcfs_ev, "GA": ga_ev}
        if len(inst.vessels) <= 10:
            _, mip_ev = milp_solve(inst)
            if mip_ev.get("feasible"):
                rows["MIP"] = mip_ev

        print(f"{'method':<8} {'avg_wait':>10} {'avg_port':>10} {'makespan':>10} {'feasible':>9}")
        for name, ev in rows.items():
            print(f"{name:<8} {ev['avg_waiting']:>10.2f} {ev['avg_in_port']:>10.2f} "
                  f"{ev['makespan']:>10.2f} {ev['feasible']!s:>9}")
        return 0

    if args.cmd == "sensitivity":
        from .baseline import fcfs_solve
        from .ga import ga_solve
        from .instances import generate_instance
        print(f"{'cranes':>7} {'FCFS_port':>11} {'GA_port':>11} {'improvement':>12}")
        for nc in range(args.cranes_min, args.cranes_max + 1):
            inst = generate_instance(args.vessels, args.berths, nc, seed=7)
            _, f_ev = fcfs_solve(inst)
            _, g_ev = ga_solve(inst, generations=args.ga_gens, seed=7)
            imp = (f_ev["total_in_port"] - g_ev["total_in_port"]) / max(f_ev["total_in_port"], 1e-9)
            print(f"{nc:>7} {f_ev['total_in_port']:>11.1f} {g_ev['total_in_port']:>11.1f} {imp:>11.1%}")
        return 0

    if args.cmd == "plot":
        import os

        import matplotlib

        from .benchmarks import benchmark_instances
        from .ga import ga_solve
        from .visualize import plot_gantt
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        inst = benchmark_instances(args.name)
        sol, _ = ga_solve(inst, generations=300, seed=42)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 4))
        plot_gantt(sol, inst, title=f"GA schedule -- {args.name}", ax=ax)
        fig.tight_layout()
        fig.savefig(args.out, dpi=150)
        plt.close(fig)
        print(f"saved -> {args.out}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
