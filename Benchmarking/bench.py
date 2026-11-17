"""Python harness. Replays a workload file through each Python book.

Usage: python bench.py workloads/p100_c30.txt --runs 5 --csv results.csv
Needs Python 3.10+ (Orderbook.py uses match).
CSV row: impl,workload,run,ns,ops,fills,traded,cancel_hits,best_bid,best_ask
GC is disabled during each timed run.
"""
import argparse
import csv
import gc
import time
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from Versions.Orderbook import OrderBook
from Versions.PriceLevelBook import PriceLevelBook

IMPLS = {"py_heap": OrderBook, "py_pricelevel": PriceLevelBook}


def load(path):
    ops = []
    with open(path) as f:
        for line in f:
            p = line.split()
            if p[0] == "A":
                ops.append((0, int(p[1]), p[2], int(p[3]), int(p[4])))
            else:
                ops.append((1, int(p[1]), "", 0, 0))
    return ops


def run(cls, ops):
    book = cls()
    add, cancel = book.add_limit, book.cancel
    fills = traded = hits = 0
    gc.collect()
    gc.disable()
    t0 = time.perf_counter_ns()
    for kind, oid, side, price, qty in ops:
        if kind == 0:
            f = add(oid, side, price, qty)
            fills += len(f)
            for x in f:
                traded += x[3]
        elif cancel(oid):
            hits += 1
    ns = time.perf_counter_ns() - t0
    gc.enable()
    try:
        bb = book.best_bid()
    except IndexError:
        bb = -1
    try:
        ba = book.best_ask()
    except IndexError:
        ba = -1
    return ns, fills, traded, hits, bb, ba


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("workload")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--csv", default="results.csv")
    a = ap.parse_args()

    ops = load(a.workload)
    name = Path(a.workload).stem
    with open(a.csv, "a", newline="") as out:
        w = csv.writer(out)
        for impl, cls in IMPLS.items():
            run(cls, ops[:10000])                      # warm-up
            for r in range(a.runs):
                ns, fills, traded, hits, bb, ba = run(cls, ops)
                w.writerow([impl, name, r, ns, len(ops), fills, traded, hits, bb, ba])
                out.flush()
            print(f"{impl:14s} {name}: last run {ns / 1e9:.3f}s")