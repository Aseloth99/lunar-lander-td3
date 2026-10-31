"""Deterministik değerlendirme (stokastik politika ASLA kullanılmaz).

Örnekler:
  python3 evaluate.py --run-dir runs/sac/zoo/seed0 --split val              # doğrulama tohumları (5000-5099)
  python3 evaluate.py --run-dir runs/sac/zoo/seed0 --split val --ckpt final
  python3 evaluate.py --run-dir runs/sac/zoo/seed0 --split test             # TEST: yalnızca en sonda, bir kez

Test koruması: (1) <proje_klasörü>/FROZEN dosyası yoksa test reddedilir (tüm ayarlar donmadan test yok),
(2) bir koşunun test sonucu varsa ikinci kez yazılmaz.
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import common  # noqa: E402


def load_for_eval(run_dir, algo, ckpt):
    run_dir = Path(run_dir)
    if ckpt == "best":
        return common.load_policy(algo, run_dir / "best_policy.pt")
    if ckpt.startswith("best_"):  # reselect.py seçimleri: best_v2, best_800k, best_1600k -> best_policy_<ek>.pt
        return common.load_policy(algo, run_dir / f"best_policy_{ckpt[5:]}.pt")
    if ckpt == "final":
        from configs import algo_class
        return algo_class(algo).load(str(run_dir / "final.zip"), device="cpu").policy
    return common.load_policy(algo, ckpt)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--split", choices=["val", "val3", "val4", "val5", "val6", "test", "test2", "test2x", "test3", "test3x", "test4", "test4x",
                                       "test5", "test5x", "val7", "test6", "test6x", "val8", "test7", "test7x", "val9", "test8", "test8x"],
                   default="val",
                   help="val: 5000-5099 | val3: 5600-5999 (bağımsız sıralama) | test: 10000-10099 (KULLANILDI) | "
                        "test2: 20000-20099 (yeni resmi) | test2x: 20100-20999 (ek) | Aşama 7: val6 6800-7199, "
                        "test5 50000-50099, test5x 50100-50999")
    p.add_argument("--ckpt", default="best", help="best | best_v2 | best_800k | best_1600k | final | .pt dosya yolu")
    p.add_argument("--episodes", type=int, default=None, help="varsayılan: kümenin tamamı")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    cfg = json.load(open(run_dir / "config.json", encoding="utf-8"))
    algo = cfg["algo"]
    seeds = dict(val=common.VAL_SEEDS, val3=common.VAL3_SEEDS, val4=common.VAL4_SEEDS, test=common.TEST_SEEDS,
                 test2=common.TEST2_SEEDS, test2x=common.TEST2X_SEEDS, test3=common.TEST3_SEEDS,
                 test3x=common.TEST3X_SEEDS, val5=common.VAL5_SEEDS, test4=common.TEST4_SEEDS,
                 test4x=common.TEST4X_SEEDS, val6=common.VAL6_SEEDS, test5=common.TEST5_SEEDS,
                 test5x=common.TEST5X_SEEDS, val7=common.VAL7_SEEDS, test6=common.TEST6_SEEDS,
                 test6x=common.TEST6X_SEEDS, val8=common.VAL8_SEEDS, test7=common.TEST7_SEEDS,
                 test7x=common.TEST7X_SEEDS, val9=common.VAL9_SEEDS, test8=common.TEST8_SEEDS,
                 test8x=common.TEST8X_SEEDS)[args.split]
    if args.episodes:
        seeds = seeds[: args.episodes]

    is_test = args.split.startswith("test")
    # Aşama 6'dan itibaren aynı koşu birden çok kontrol noktasıyla test edilir: test4 dosya adına ckpt da girer
    prefix = args.split if (is_test and args.split[:5] in ("test", "test2", "test3")) else f"{args.split}_{args.ckpt}"
    if is_test:
        frozen = {"test": common.FROZEN_FILE, "test2": common.FROZEN2_FILE, "test2x": common.FROZEN2_FILE,
                  "test3": common.FROZEN3_FILE, "test3x": common.FROZEN3_FILE, "test4": common.FROZEN4_FILE,
                  "test4x": common.FROZEN4_FILE, "test5": common.FROZEN5_FILE, "test5x": common.FROZEN5_FILE,
                  "test6": common.FROZEN6_FILE, "test6x": common.FROZEN6_FILE,
                  "test7": common.FROZEN7_FILE, "test7x": common.FROZEN7_FILE,
                  "test8": common.FROZEN8_FILE, "test8x": common.FROZEN8_FILE}[args.split]
        if not frozen.exists():
            sys.exit(f"REDDEDİLDİ: {frozen.name} dosyası yok. Test tohumlarına yalnızca tüm ayarlar donduktan sonra, "
                     "en sonda ve bir kez bakılır.")
        if (run_dir / f"{prefix}_summary.json").exists():
            sys.exit(f"REDDEDİLDİ: {run_dir} için {args.split} sonucu zaten var (ikinci kez bakılmaz).")

    policy = load_for_eval(run_dir, algo, args.ckpt)
    rows = common.evaluate_episodes(common.policy_act_fn(policy), seeds)
    summ = common.summarize(rows)
    summ.update(split=args.split, ckpt=args.ckpt, algo=algo, seed=cfg["seed"], tag=cfg["tag"])

    common.write_rows_csv(run_dir / f"{prefix}_episodes.csv", rows)
    common.write_json_atomic(run_dir / f"{prefix}_summary.json", summ)
    print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
