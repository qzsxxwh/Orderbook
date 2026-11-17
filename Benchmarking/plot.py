"""Read results.csv, check all implementations agree, print medians, save two figures."""
import csv
import re
import statistics
from collections import defaultdict

import matplotlib.pyplot as plt

ORDER = ["py_heap", "py_pricelevel", "cpp_orig", "cpp_fixed", "cpp_pricelevel"]
STYLE = {"py_heap": ("tab:blue", "--"), "py_pricelevel": ("tab:blue", "-"),
         "cpp_orig": ("tab:red", ":"), "cpp_fixed": ("tab:red", "--"),
         "cpp_pricelevel": ("tab:red", "-")}

times = defaultdict(list)      # (impl, prices, cancel) -> [seconds]
checks = defaultdict(set)      # workload -> {(impl, checksum)}
with open("results.csv") as f:
    for r in csv.DictReader(f):
        m = re.fullmatch(r"p(\d+)_c(\d+)", r["workload"])
        key = (r["impl"], int(m[1]), int(m[2]))
        times[key].append(int(r["ns"]) / 1e9)
        checks[r["workload"]].add((r["impl"], tuple(r[k] for k in
               ("ops", "fills", "traded", "cancel_hits", "best_bid", "best_ask"))))

# differential check: every implementation must produce the same checksum per workload
bad = False
for wl, rows in sorted(checks.items()):
    if len({c for _, c in rows}) > 1:
        bad = True
        print(f"MISMATCH in {wl}:")
        for impl, c in sorted(rows):
            print("   ", impl, c)
print("Checksums: all implementations agree." if not bad else "FIX MISMATCHES BEFORE TRUSTING TIMES.")

prices = sorted({k[1] for k in times})
cancels = sorted({k[2] for k in times})
impls = [i for i in ORDER if any(k[0] == i for k in times)]


def stat(impl, p, c):
    v = times[(impl, p, c)]
    return statistics.median(v), min(v), max(v)


print("\nMedian seconds")
for p in prices:
    for c in cancels:
        print(f"prices={p:<5} cancel={c:>2}%  " +
              "  ".join(f"{i}={stat(i, p, c)[0]:.3f}" for i in impls))


def figure(xs, xlabel, panels, panel_label, key, fname):
    fig, axes = plt.subplots(1, len(panels), figsize=(5 * len(panels), 4), sharey=True)
    for ax, pv in zip(axes, panels):
        for i in impls:
            pts = [stat(i, *key(pv, x)) for x in xs]
            col, ls = STYLE[i]
            ax.plot(xs, [t[0] for t in pts], color=col, ls=ls, marker="o", label=i)
            ax.fill_between(xs, [t[1] for t in pts], [t[2] for t in pts], color=col, alpha=0.12)
        ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_title(panel_label(pv))
        if xlabel.startswith("distinct"):
            ax.set_xscale("log")
    axes[0].set_ylabel("replay time (s, log), median with min-max band")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fname, dpi=150)


figure(cancels, "cancel ratio (%)", prices, lambda p: f"{p} distinct prices per side",
       lambda p, c: (p, c), "fig_time_vs_cancel.png")
# for the second figure the lookup key is (impl, prices, cancel) with x = prices
figure(prices, "distinct prices per side", cancels, lambda c: f"{c}% cancels",
       lambda c, p: (p, c), "fig_time_vs_prices.png")
print("\nSaved fig_time_vs_cancel.png and fig_time_vs_prices.png")