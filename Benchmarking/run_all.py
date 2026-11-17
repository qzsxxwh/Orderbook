"""Build, generate workloads, run every implementation, write results.csv.

Usage: python run_all.py [--ops 50000] [--runs 5]
Expects all book files and the scripts in the same folder.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

from gen_workload import generate

ROOT = Path(__file__).resolve().parent
PRICES = [10, 100, 1000]       # distinct price levels per side
CANCELS = [0.0, 0.1, 0.3]      # cancel ratio
CPP = {                        # name -> compile flag that selects the book in bench.cpp
    "cpp_orig": "-DUSE_ORIG",
    "cpp_fixed": "-DUSE_FIXED",
    "cpp_pricelevel": "-DUSE_PRICELEVEL",
}

ap = argparse.ArgumentParser()
ap.add_argument("--ops", type=int, default=50000)
ap.add_argument("--runs", type=int, default=5)
a = ap.parse_args()

exe = ".exe" if os.name == "nt" else ""
(ROOT / "build").mkdir(exist_ok=True)
(ROOT / "workloads").mkdir(exist_ok=True)

for name, flag in CPP.items():
    subprocess.run(["g++", "-O2", "-std=c++17", "-I", ".", flag, "bench.cpp",
                    "-o", f"build/bench_{name}{exe}"], cwd=ROOT, check=True)

csv_path = ROOT / "results.csv"
csv_path.write_text("impl,workload,run,ns,ops,fills,traded,cancel_hits,best_bid,best_ask\n")

for p in PRICES:
    for c in CANCELS:
        wl = ROOT / "workloads" / f"p{p}_c{int(c * 100)}.txt"
        generate(wl, ops=a.ops, prices=p, cancel=c)
        print(f"\n== {wl.name} ==", flush=True)
        subprocess.run([sys.executable, "bench.py", str(wl), "--runs", str(a.runs),
                        "--csv", str(csv_path)], cwd=ROOT, check=True)
        for name in CPP:
            subprocess.run([f"build/bench_{name}{exe}", str(wl), str(a.runs), str(csv_path)],
                           cwd=ROOT, check=True)

print("\nDone. Now run: python plot.py")