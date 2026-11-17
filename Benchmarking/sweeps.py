"""Two follow-up experiments. Run run_all.py first (it builds the C++ binaries).

  python sweeps.py crossover   # finer cancel ratios (0-10%), 100 prices, 50k ops
  python sweeps.py depth       # 12.5k-200k ops, 100 prices, 10% cancels

Writes results_<name>.csv and fig_<name>.png, and prints a table of medians.
Edit EXPERIMENTS below to change the grid.
"""
import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from gen_workload import generate

ROOT = Path(__file__).resolve().parent
IMPLS = ["py_heap", "py_pricelevel", "cpp_orig", "cpp_fixed", "cpp_pricelevel"]
STYLE = {"py_heap": ("tab:blue", "--"), "py_pricelevel": ("tab:blue", "-"),
         "cpp_orig": ("tab:red", ":"), "cpp_fixed": ("tab:red", "--"),
         "cpp_pricelevel": ("tab:red", "-")}

# each entry: (distinct prices per side, cancel percent, number of operations)
EXPERIMENTS = {
    "crossover": [(100, pct, 50000) for pct in [0, 0.5, 1, 2, 3, 5, 10]],
    "depth": [(100, 10, n) for n in [12500, 25000, 50000, 100000, 200000]],
}
X_INDEX = {"crossover": 1, "depth": 2}      # which tuple field is the x axis
X_LABEL = {"crossover": "cancel ratio (%)", "depth": "number of operations"}


def wl_name(p, pct, n):
    return f"p{p}_c{pct:g}_n{n}".replace(".", "_")


def parse(name):
    m = re.fullmatch(r"p(\d+)_c([\d_]+)_n(\d+)", name)
    return int(m[1]), float(m[2].replace("_", ".")), int(m[3])


def run(exp, runs):
    exe = ".exe" if os.name == "nt" else ""
    csv_path = ROOT / f"results_{exp}.csv"
    csv_path.write_text("impl,workload,run,ns,ops,fills,traded,cancel_hits,best_bid,best_ask\n")
    (ROOT / "workloads").mkdir(exist_ok=True)
    for p, pct, n in EXPERIMENTS[exp]:
        wl = ROOT / "workloads" / (wl_name(p, pct, n) + ".txt")
        generate(wl, ops=n, prices=p, cancel=pct / 100)
        print(f"\n== {wl.name} ==", flush=True)
        subprocess.run([sys.executable, "bench.py", str(wl), "--runs", str(runs),
                        "--csv", str(csv_path)], cwd=ROOT, check=True)
        for impl in IMPLS[2:]:
            binary = ROOT / "build" / f"bench_{impl}{exe}"
            if not binary.exists():
                sys.exit(f"{binary} not found. Run run_all.py first to build the C++ binaries.")
            subprocess.run([str(binary), str(wl), str(runs), str(csv_path)], cwd=ROOT, check=True)


def plot(exp):
    times, checks = defaultdict(list), defaultdict(set)
    with open(ROOT / f"results_{exp}.csv") as f:
        for r in csv.DictReader(f):
            p, pct, n = parse(r["workload"])
            x = (p, pct, n)[X_INDEX[exp]]
            times[(r["impl"], x)].append(int(r["ns"]) / 1e9)
            checks[r["workload"]].add((r["impl"], tuple(r[k] for k in
                   ("ops", "fills", "traded", "cancel_hits", "best_bid", "best_ask"))))
    bad = False
    for wl, rows in sorted(checks.items()):
        if len({c for _, c in rows}) > 1:
            bad = True
            print(f"MISMATCH in {wl}: {sorted(rows)}")
    print("Checksums: all implementations agree." if not bad else "FIX MISMATCHES FIRST.")

    xs = sorted({k[1] for k in times})
    fig, ax = plt.subplots(figsize=(7, 5))
    print(f"\nMedian seconds by {X_LABEL[exp]}")
    print("impl".ljust(16) + "".join(f"{x:>10g}" for x in xs))
    for impl in IMPLS:
        med = [statistics.median(times[(impl, x)]) for x in xs]
        lo = [min(times[(impl, x)]) for x in xs]
        hi = [max(times[(impl, x)]) for x in xs]
        col, ls = STYLE[impl]
        ax.plot(xs, med, color=col, ls=ls, marker="o", label=impl)
        ax.fill_between(xs, lo, hi, color=col, alpha=0.12)
        print(impl.ljust(16) + "".join(f"{m:>10.4f}" for m in med))
    ax.set_yscale("log")
    if exp == "depth":
        ax.set_xscale("log")
    ax.set_xlabel(X_LABEL[exp])
    ax.set_ylabel("replay time (s, log), median with min-max band")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / f"fig_{exp}.png", dpi=150)

    if exp == "depth":      # growth exponent: time ~ ops^k  (k=1 linear, k=2 quadratic)
        print("\nGrowth exponent k (time ~ ops^k, log-log fit over the sweep):")
        import math
        for impl in IMPLS:
            lx = [math.log(x) for x in xs]
            ly = [math.log(statistics.median(times[(impl, x)])) for x in xs]
            k = statistics.linear_regression(lx, ly).slope
            print(f"  {impl:16s} k = {k:.2f}")
    print(f"\nSaved fig_{exp}.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", choices=list(EXPERIMENTS))
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    run(a.experiment, a.runs)
    plot(a.experiment)