#!/usr/bin/env python3
"""Reference reader for the single-shift petrol replenishment instances.

Parses one instance file and prints a summary. The parser below is the format specification in
executable form: it consumes the whole token stream and asserts nothing is left over.

Usage: python3 read_instance.py seed_130.txt
"""
import sys


def read_instance(path):
    tok = open(path).read().split()
    pos = 0

    def nxt(cast=int):
        nonlocal pos
        v = cast(tok[pos])
        pos += 1
        return v

    inst = {}
    inst["num_stations"] = nxt()
    inst["H"] = nxt()                  # shift horizon, minutes
    inst["phi"] = nxt()                # minutes to move 1000 litres
    inst["num_trucks"] = nxt()
    inst["d_dual"] = nxt()             # optional side constraints, see README
    inst["d_next"] = nxt()
    inst["total_gen"] = nxt()          # solver parameters, not instance data
    inst["random_choice_prob"] = nxt(float)

    inst["trucks"] = []
    for _ in range(inst["num_trucks"]):
        n_comp = nxt()
        t = {"max_stations_per_route": nxt(), "neighbourhood": nxt(), "shift": nxt(),
             "num_hoses": nxt(), "pre_loaded": nxt() == 1, "cost": nxt()}
        t["capacities"] = [nxt() for _ in range(n_comp)]
        inst["trucks"].append(t)

    sectors = inst["H"] // 60
    inst["stations"] = []
    for _ in range(inst["num_stations"]):
        n_res = nxt()
        st = {"setup_time": nxt(), "depot_to_station": nxt(), "station_to_depot": nxt(),
              "reservoirs": []}
        for _ in range(n_res):
            r = {"initial": nxt(), "min_level": nxt(), "capacity": nxt(),
                 "demand_lower": nxt(), "demand_upper": nxt()}
            r["consumption"] = [nxt(float) for _ in range(sectors)]
            r["klass"] = "A" if r["demand_lower"] == 0 else "B"
            st["reservoirs"].append(r)
        inst["stations"].append(st)

    n = inst["num_stations"]
    inst["travel"] = [[nxt() for _ in range(n)] for _ in range(n)]
    inst["compatible"] = [[nxt() == 1 for _ in range(n)] for _ in range(inst["num_trucks"])]

    assert pos == len(tok), f"{len(tok) - pos} tokens left unread - format mismatch"
    return inst


def main():
    inst = read_instance(sys.argv[1])
    res = [r for st in inst["stations"] for r in st["reservoirs"]]
    n, H = inst["num_stations"], inst["H"]
    usable = sum(1 for a in range(n) for b in range(n) if a != b and inst["travel"][a][b] < H)
    print(f"{sys.argv[1]}: {n} stations, {len(res)} reservoirs "
          f"({sum(r['klass'] == 'B' for r in res)} class B, {sum(r['klass'] == 'A' for r in res)} class A), "
          f"{inst['num_trucks']} trucks, H={H} min, phi={inst['phi']}")
    print(f"  shifts {min(t['shift'] for t in inst['trucks'])}-{max(t['shift'] for t in inst['trucks'])} min, "
          f"compartments {sorted({len(t['capacities']) for t in inst['trucks']})}, "
          f"hoses {sorted({t['num_hoses'] for t in inst['trucks']})}, "
          f"truck capacity {min(sum(t['capacities']) for t in inst['trucks'])}-"
          f"{max(sum(t['capacities']) for t in inst['trucks'])} l")
    print(f"  usable station arcs (travel < H): {usable} of {n * (n - 1)} ({100 * usable / (n * n - n):.1f}%), "
          f"d_dual={inst['d_dual']}, d_next={inst['d_next']}")


if __name__ == "__main__":
    main()
