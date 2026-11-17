"""Generate a seeded order stream.

Line format:  A <id> <B|S> <price> <qty>   (add limit order)
              C <id>                        (cancel)

Usage: python gen_workload.py out.txt --ops 50000 --prices 100 --cancel 0.3
"""
import argparse
import random


def generate(path, seed=42, ops=50000, prices=100, cancel=0.0, cross=0.1, mid=1000):
    """prices = distinct price levels per side; cancel = chance an op is a cancel;
    cross = chance an add is aggressive (priced to cross the spread)."""
    rng = random.Random(seed)
    live = []          # ids issued and not yet cancelled (cancel targets)
    next_id = 1
    out = []
    for _ in range(ops):
        if live and rng.random() < cancel:
            i = rng.randrange(len(live))
            live[i], live[-1] = live[-1], live[i]
            out.append(f"C {live.pop()}")
        else:
            oid, next_id = next_id, next_id + 1
            side = rng.choice("BS")
            aggressive = rng.random() < cross
            off = rng.randint(1, prices)
            # passive buy / aggressive sell sit below mid; passive sell / aggressive buy above
            price = mid - off if (side == "B") != aggressive else mid + off
            out.append(f"A {oid} {side} {price} {rng.randint(1, 10)}")
            live.append(oid)
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ops", type=int, default=50000)
    ap.add_argument("--prices", type=int, default=100)
    ap.add_argument("--cancel", type=float, default=0.0)
    ap.add_argument("--cross", type=float, default=0.1)
    a = ap.parse_args()
    generate(a.path, a.seed, a.ops, a.prices, a.cancel, a.cross)