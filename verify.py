"""Verify the headline numbers of this repository from raw data, on any machine.

  python3 verify.py                 # recompute all tables, re-run both selection rules, replay the official test episodes
  python3 verify.py --full          # replay all 10,000 test episodes of both headline agents (slower)
  python3 verify.py --fresh 200     # also test both agents on 200 brand-new random episodes per agent

Data: results/stage10_episodes.csv.gz holds every validation and test episode of Stage 10 (11 candidates x 5 agents:
validation 90000-91999, official test 100000-100099, extended test 100100-101999). results/decision.json is the
selection that was frozen BEFORE any test episode was run (rules: docs/selection_rules.md, "v8").
results/stage8_episodes.csv.gz holds Stage 8, an earlier and independent validation + test (7200-9199, 60000-61999),
used here for the long-run crash count.
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import json  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

import common  # noqa: E402
from evaluate import load_for_eval  # noqa: E402

R = common.ROOT
fails = []
SPLITS10 = [("val9", common.VAL9_SEEDS), ("test8", common.TEST8_SEEDS), ("test8x", common.TEST8X_SEEDS)]
SPLITS8 = [("val7", common.VAL7_SEEDS), ("test6", common.TEST6_SEEDS), ("test6x", common.TEST6X_SEEDS)]


def check(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        fails.append(name)


def ci95(x):
    x = np.asarray(x, dtype=float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def summary(df):
    seed_means = df.groupby("run").score.mean()
    return dict(mean=seed_means.mean(), ci=ci95(seed_means), crashes=int((df.outcome == "crash").sum()),
                below200=int((df.score < 200).sum()), n=len(df), best=df.score.max(), worst=df.score.min())


def rank(eps, cands):
    """Pre-registered order (v8): every agent's validation mean >= 280 first, then fewest crashes, then fewest
    episodes below 200, then the highest mean."""
    rows = []
    for c in cands:
        v = eps[(eps.group == c) & (eps.split == "val9")]
        per = v.groupby("run").score.mean()
        rows.append((c, bool((per >= 280).all()), int((v.outcome == "crash").sum()), int((v.score < 200).sum()), per.mean()))
    return sorted(rows, key=lambda r: (0 if r[1] else 1, r[2], r[3], -r[4]))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--full", action="store_true", help="replay all 10,000 test episodes of both headline agents")
    p.add_argument("--fresh", type=int, default=0, help="new random episodes per agent for both headline agents")
    a = p.parse_args()

    eps = pd.read_csv(R / "results" / "stage10_episodes.csv.gz")
    old = pd.read_csv(R / "results" / "stage8_episodes.csv.gz")
    dec = json.load(open(R / "results" / "decision.json", encoding="utf-8"))
    main_group = dec["main"]
    cands = list(dict.fromkeys(eps.group))

    print("1) Data integrity")
    for c in cands:
        ok = all(list(eps[(eps.group == c) & (eps.split == s) & (eps.run == k)].episode_seed) == seeds
                 for s, seeds in SPLITS10 for k in range(5))
        check(f"{c:20s} Stage 10: 5 agents x (2,000 validation + 2,000 test) episodes, expected seeds", ok)
    for c in dict.fromkeys(old.group):
        ok = all(list(old[(old.group == c) & (old.split == s) & (old.run == k)].episode_seed) == seeds
                 for s, seeds in SPLITS8 for k in range(5))
        check(f"{c:20s} Stage 8:  5 agents x (2,000 validation + 2,000 test) episodes, expected seeds", ok)
    sets = [set(seeds) for _, seeds in SPLITS10 + SPLITS8]
    check("all six validation/test seed sets are disjoint", sum(len(s) for s in sets) == len(set().union(*sets)))

    print("\n2) Both selection rules re-run on Stage 10 validation data only (90000-91999)")
    rows = rank(eps, cands)
    for c, ok, cr, b, m in rows:
        print(f"     {c:20s} eligible={ok!s:5s} crashes {cr:2d}/10,000  below-200 {b:4d}  mean {m:.2f}")
    check("rule 2 (all 11 candidates, safety first) picks the frozen headline agent", rows[0][0] == main_group,
          f"recomputed {rows[0][0]}, frozen {main_group}")
    rows1 = rank(eps, [c for c in cands if c.startswith("sac/v10")])
    check("rule 1 (best SAC with the braking penalty) picks the frozen Stage 10 SAC", rows1[0][0] == dec["stage10_pick"],
          f"recomputed {rows1[0][0]}, frozen {dec['stage10_pick']}")

    print("\n3) Test results recomputed from per-episode logs")
    print(f"     {'candidate':20s} | official test (5x100)        | extended test (5x2,000)")
    ext_means = {}
    for c in cands:
        o = summary(eps[(eps.group == c) & (eps.split == "test8")])
        x = summary(eps[(eps.group == c) & eps.split.isin(["test8", "test8x"])])
        ext_means[c] = x["mean"]
        print(f"     {c:20s} | {o['mean']:6.1f} ± {o['ci']:.1f}, crashes {o['crashes']}/500 | "
              f"{x['mean']:6.1f} ± {x['ci']:.1f}, crashes {x['crashes']:2d}/10,000, below 200: {x['below200']:4d}, "
              f"worst {x['worst']:.1f}")
    top = max(ext_means, key=ext_means.get)
    print(f"     top score on the test: {top} | pre-registered pick (fewest crashes on validation): {main_group}")

    print("\n4) Every logged independent validation + test episode (Stage 8 and Stage 10)")
    for label, grp in [("pre-registered pick", main_group), ("top scorer", top)]:
        allx = pd.concat([old[old.group == grp], eps[eps.group == grp]])
        n, k = len(allx), int((allx.outcome == "crash").sum())
        ub = 100 * stats.beta.ppf(0.95, k + 1, n - k)
        print(f"     {label:20s} {grp:20s} crashes {k}/{n:,} (95 % upper bound on the crash rate: {ub:.4f} %)")
        if grp == main_group:
            check("the pre-registered pick never crashed in these episodes", k == 0 and n == 40000, f"{k}/{n:,}")

    env = common.make_env()
    split_seeds = common.TEST8_SEEDS + (common.TEST8X_SEEDS if a.full else [])
    for label, grp in [("pre-registered pick", main_group), ("top scorer", top)]:
        g, _, suf = grp.partition("@")
        algo, tag = g.split("/")
        print(f"\n5) Replaying the {label} ({grp}) on {len(split_seeds) * 5:,} logged test episodes")
        maxdiff, n = 0.0, 0
        for k in range(5):
            act = common.policy_act_fn(load_for_eval(R / "runs" / algo / tag / f"seed{k}", algo, f"best_{suf}"))
            logged = eps[(eps.group == grp) & (eps.run == k) & eps.split.isin(["test8", "test8x"])].set_index("episode_seed")
            for s in split_seeds:
                r = common.run_episode(env, act, s)
                maxdiff = max(maxdiff, abs(r["ret"] - logged.loc[s, "score"]))
                n += 1
        check(f"replayed scores match the logs ({n:,} episodes)", maxdiff < 1e-6, f"max difference {maxdiff:.1e}")

    if a.fresh:
        for label, grp in [("pre-registered pick", main_group), ("top scorer", top)]:
            g, _, suf = grp.partition("@")
            algo, tag = g.split("/")
            print(f"\n6) The {label} ({grp}) on {a.fresh} brand-new random episodes per agent")
            rng = np.random.default_rng()
            rows = []
            for k in range(5):
                act = common.policy_act_fn(load_for_eval(R / "runs" / algo / tag / f"seed{k}", algo, f"best_{suf}"))
                for s in rng.integers(1_000_000, 2_000_000, size=a.fresh):
                    r = common.run_episode(env, act, int(s))
                    rows.append(dict(run=k, score=r["ret"], outcome=r["outcome"]))
            f = summary(pd.DataFrame(rows))
            print(f"     mean {f['mean']:.1f} ± {f['ci']:.1f} | crashes {f['crashes']}/{f['n']} | below 200: "
                  f"{f['below200']} | best {f['best']:.1f} | worst {f['worst']:.1f}")

    print("\nRESULT:", "ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILED: {fails}")


if __name__ == "__main__":
    main()
