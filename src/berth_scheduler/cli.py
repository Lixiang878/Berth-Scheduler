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

    if args.cmd == "compare":
        from .baseline import fcfs_solve
        from .ga import ga_solve
        from .instances import generate_instance
        from .milp import milp_solve
        inst = generate_instance(args.vessels, args.berths, args.cranes, seed=args.seed)
        print(inst.summary())

        _, fcfs_ev = fcfs_solve(inst)
        _, ga_ev = ga_solve(inst, generations=args.ga_gens, seed=args.seed)

        rows = {
            "FCFS": fcfs_ev,
            "GA": ga_ev,
        }
        if args.vessels <= 10:
            _, mip_ev = milp_solve(inst)
            if mip_ev.get("feasible"):
                rows["MIP"] = mip_ev

        print(f"{'method':<8} {'avg_wait':>10} {'avg_port':>10} {'makespan':>10} {'feasible':>9}")
        for name, ev in rows.items():
            print(f"{name:<8} {ev['avg_waiting']:>10.2f} {ev['avg_in_port']:>10.2f} "
                  f"{ev['makespan']:>10.2f} {ev['feasible']!s:>9}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
