"""Çakılmaya duyarlı kontrol noktası seçimi (v2). YALNIZCA doğrulama tohumları 5100-5599 kullanılır.

Neden: v1 seçimi (ilk 100 doğrulama bölümünde en yüksek ortalama) ~%2 çakılma bırakıyordu. Çakılmaların çoğu
iniş SONRASI devrilmeydi ve eğitimin farklı anlarında bu davranış değişiyor. Burada amaç: çakılmayan anı bulmak.

Yöntem:
  adaylar : eğitimin son %50'sindeki kontrol noktaları; eğitim sırasındaki 20 bölümlük doğrulama ölçümünde
            (5000-5019) çakılmamış olanlar (3'ten azsa hepsi), en yüksek ortalamalı en fazla 12 tanesi
  aşama 1 : her aday 100 bölüm (5100-5199)  -> (çakılma sayısı az, ortalama yüksek) sırasıyla en iyi 4
  aşama 2 : bu 4'e 400 bölüm daha (5200-5599) -> toplam 500 bölümde en az çakılan; eşitlikte başarı, sonra ortalama
Çıktı: best_policy_v2.pt, selection_v2.json, val2_episodes.csv (seçilenin 500 bölümü)
  --suffix 800k --min-step 400000 --max-step 800000 -> best_policy_800k.pt, selection_800k.json, val2_800k_episodes.csv
  (Aşama 6: aynı 1,6 milyonluk koşudan 800 bin ve 1,6 milyon anları ayrı ayrı seçilir)

  python3 reselect.py --run-dir runs/td3/tuned/seed0
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

import pandas as pd  # noqa: E402

import common  # noqa: E402


def score(rows):
    s = common.summarize(rows)
    n_crash = sum(r["outcome"] == "crash" for r in rows)
    return s, (n_crash, -s["success"], -s["mean"])  # küçük olan iyi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--min-frac", type=float, default=0.5)
    p.add_argument("--min-step", type=int, default=None, help="aday aralığının başı (varsayılan: son %%50)")
    p.add_argument("--max-step", type=int, default=None, help="aday aralığının sonu (varsayılan: eğitimin sonu)")
    p.add_argument("--suffix", default="v2", help="çıktı adı eki: best_policy_<ek>.pt")
    p.add_argument("--max-cands", type=int, default=12)
    p.add_argument("--top", type=int, default=4)
    a = p.parse_args()

    run_dir = Path(a.run_dir)
    cfg = json.load(open(run_dir / "config.json", encoding="utf-8"))
    algo, total = cfg["algo"], int(cfg["cfg"]["steps"])
    curve = pd.read_csv(run_dir / "val_curve.csv").drop_duplicates("step", keep="last")
    lo = a.min_step if a.min_step is not None else a.min_frac * total
    hi = a.max_step if a.max_step is not None else float("inf")
    late = curve[(curve.step >= lo) & (curve.step <= hi)]
    cands = late[late.val_crash == 0]
    if len(cands) < 3:
        cands = late
    cands = cands.sort_values(["val_mean", "step"], ascending=False).head(a.max_cands)
    cands = [r for r in cands.itertuples() if (run_dir / "ckpt" / r.ckpt).exists()]

    env = common.make_env()
    s1, s2 = common.VAL2_SEEDS[:100], common.VAL2_SEEDS[100:500]
    stage1 = []
    for r in cands:
        pol = common.load_policy(algo, run_dir / "ckpt" / r.ckpt)
        rows = common.evaluate_episodes(common.policy_act_fn(pol), s1, env=env)
        summ, k = score(rows)
        stage1.append(dict(ckpt=r.ckpt, step=int(r.step), rows=rows, key=k, s100=summ))
    stage1.sort(key=lambda x: (x["key"], -x["step"]))
    final = []
    for c in stage1[: a.top]:
        pol = common.load_policy(algo, run_dir / "ckpt" / c["ckpt"])
        rows = c["rows"] + common.evaluate_episodes(common.policy_act_fn(pol), s2, env=env)
        summ, k = score(rows)
        final.append(dict(ckpt=c["ckpt"], step=c["step"], rows=rows, key=k, s500=summ))
    final.sort(key=lambda x: (x["key"], -x["step"]))
    best = final[0]
    sx = a.suffix
    shutil.copyfile(run_dir / "ckpt" / best["ckpt"], run_dir / f"best_policy_{sx}.pt")
    common.write_rows_csv(run_dir / ("val2_episodes.csv" if sx == "v2" else f"val2_{sx}_episodes.csv"), best["rows"])
    common.write_json_atomic(run_dir / f"selection_{sx}.json", dict(window=[lo, None if hi == float("inf") else hi],
        rule=__doc__.split("Yöntem:")[1].split("Çıktı:")[0].strip(), val_seeds=[5100, 5599],
        chosen=dict(ckpt=best["ckpt"], step=best["step"], val500=best["s500"]),
        stage2=[dict(ckpt=f["ckpt"], step=f["step"], val500=f["s500"]) for f in final],
        stage1=[dict(ckpt=c["ckpt"], step=c["step"], val100=c["s100"]) for c in stage1]))
    s = best["s500"]
    print(f"{run_dir}: seçilen {best['ckpt']} | 500 bölüm: ort {s['mean']:.1f} başarı {100 * s['success']:.1f}% "
          f"çakılma {100 * s['crash']:.1f}% ({int(round(s['crash'] * 500))} bölüm) | aday {len(cands)}")


if __name__ == "__main__":
    main()
