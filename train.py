"""Eğitim betiği (SAC / TD3 / PPO, SB3).

Örnekler:
  python3 train.py --algo sac --seed 0                       # zoo ayarları, runs/sac/zoo/seed0
  python3 train.py --algo sac --seed 0 --tag tuned --config configs/tuned_sac.json
  python3 train.py --algo td3 --seed 1 --set net=256,256 batch=128 --steps 200000
  python3 train.py --algo sac --seed 0 --resume              # yarıda kalan koşuya devam eder

Her koşu runs/<algo>/<tag>/seed<k>/ altına şunları yazar:
  config.json        kullanılan tam ayarlar
  val_curve.csv      deterministik politikanın doğrulama-tohumlarındaki öğrenme eğrisi
  monitor/part*/     eğitim sırasındaki (stokastik politika) bölüm getirileri
  ckpt/step_*.pt     her değerlendirmedeki politika ağırlıkları
  final.zip          eğitim sonundaki tam model
  best_policy.pt     doğrulama tohumlarıyla seçilmiş en iyi kontrol noktası (test tohumlarına BAKILMAZ)
  selection.json     seçimin ayrıntısı
  progress.json      canlı durum (DURUM.md buradan üretilir)
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

import common  # noqa: E402
import configs  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--algo", choices=["sac", "td3", "ppo"], required=True)
    p.add_argument("--seed", type=int, required=True, help="eğitim tohumu (nihai koşular için 0-4)")
    p.add_argument("--tag", default="zoo", help="koşu grubu adı (runs/<algo>/<tag>/seed<k>)")
    p.add_argument("--config", default=None, help="ayar üzerine yazan json dosyası")
    p.add_argument("--set", nargs="*", default=[], metavar="k=v", help="tek tek ayar üzerine yazma")
    p.add_argument("--steps", type=int, default=None, help="toplam ortam adımı (varsayılan: ayardan)")
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--device", default="cpu", help="cpu (varsayılan; küçük ağlarda genelde en hızlısı) | cuda | auto")
    p.add_argument("--eval-every", type=int, default=10_000)
    p.add_argument("--resume-every", type=int, default=25_000)
    p.add_argument("--run-dir", default=None)
    p.add_argument("--resume", action="store_true", help="resume/ varsa kaldığı yerden devam")
    p.add_argument("--overwrite", action="store_true", help="var olan koşu klasörünü sil ve baştan başla")
    p.add_argument("--no-select", action="store_true", help="bitişte en iyi kontrol noktası seçimini atla")
    return p.parse_args()


def make_callback(run_dir, algo, seed, tag, total_steps, eval_every, resume_every, cfg):
    from stable_baselines3.common.callbacks import BaseCallback

    class _CB(BaseCallback):
        def __init__(self):
            super().__init__(verbose=0)
            self.run_dir = Path(run_dir)
            self.eval_env = common.make_env()
            self.t0 = time.time()
            self.n0 = 0
            self.last_prog = 0.0
            self.last_val = None
            self.best_val = -1e9
            self.has_buffer = algo in ("sac", "td3")
            (self.run_dir / "ckpt").mkdir(exist_ok=True)
            (self.run_dir / "resume").mkdir(exist_ok=True)

        def _on_training_start(self):
            self.t0 = time.time()
            self.n0 = self.num_timesteps
            self.next_eval = (self.num_timesteps // eval_every + 1) * eval_every
            self.next_resume = (self.num_timesteps // resume_every + 1) * resume_every
            self._progress("running")

        def _progress(self, state, error=None):
            n = self.num_timesteps
            el = time.time() - self.t0 if self.t0 else 0.0
            sps = (n - self.n0) / el if el > 1 else 0.0
            common.write_json_atomic(self.run_dir / "progress.json", dict(
                algo=algo, tag=tag, seed=seed, state=state, step=int(n), total=int(total_steps),
                sps=round(sps, 1), elapsed_s=round(el), eta_s=round((total_steps - n) / sps) if sps > 0 else None,
                last_val_mean=self.last_val, best_val_mean=None if self.best_val < -1e8 else self.best_val,
                updated=common.now_iso(), updated_ts=time.time(), pid=os.getpid(), error=error))
            self.last_prog = time.time()

        def _do_eval(self):
            n = self.num_timesteps
            ckpt = self.run_dir / "ckpt" / f"step_{n:08d}.pt"
            self.model.policy.save(str(ckpt))
            t = time.time()
            rows = common.evaluate_episodes(common.policy_act_fn(self.model.policy), common.VAL_CURVE_SEEDS,
                                            env=self.eval_env)
            s = common.summarize(rows)
            self.last_val = round(s["mean"], 2)
            self.best_val = max(self.best_val, s["mean"])
            common.append_csv(self.run_dir / "val_curve.csv", dict(
                step=int(n), wall_s=round(time.time() - self.t0), val_mean=round(s["mean"], 3),
                val_std=round(s["std"], 3), val_median=round(s["median"], 3), val_min=round(s["min"], 3),
                val_success=s["success"], val_crash=s["crash"], val_timeout=s["timeout"],
                eval_seconds=round(time.time() - t, 1), ckpt=ckpt.name))

        def _save_resume(self):
            d = self.run_dir / "resume"
            self.model.save(str(d / "model_tmp.zip"))
            if self.has_buffer:
                self.model.save_replay_buffer(str(d / "buffer_tmp.pkl"))
                os.replace(d / "buffer_tmp.pkl", d / "buffer.pkl")
            os.replace(d / "model_tmp.zip", d / "model.zip")

        def _on_step(self):
            n = self.num_timesteps
            if n >= self.next_eval:
                self._do_eval()
                self.next_eval += eval_every
                self._progress("running")
            if n >= self.next_resume:
                self._save_resume()
                self.next_resume += resume_every
            if time.time() - self.last_prog > 30:
                self._progress("running")
            return True

        def finish(self, state="done", error=None):
            self._progress(state, error)

    return _CB()


def select_best(run_dir, algo, topk=3):
    """Doğrulama tohumlarıyla (5000-5099) en iyi kontrol noktasını seç. TEST TOHUMLARINA BAKMAZ."""
    import csv
    run_dir = Path(run_dir)
    with open(run_dir / "val_curve.csv", encoding="utf-8") as f:
        curve = list(csv.DictReader(f))
    curve.sort(key=lambda r: (float(r["val_mean"]), int(r["step"])), reverse=True)
    cands = [r for r in curve[:topk] if (run_dir / "ckpt" / r["ckpt"]).exists()]
    env = common.make_env()
    results = []
    for r in cands:
        pol = common.load_policy(algo, run_dir / "ckpt" / r["ckpt"])
        rows = common.evaluate_episodes(common.policy_act_fn(pol), common.VAL_SEEDS, env=env)
        s = common.summarize(rows)
        results.append(dict(ckpt=r["ckpt"], step=int(r["step"]), val20_mean=float(r["val_mean"]), val100=s))
    results.sort(key=lambda x: (x["val100"]["mean"], x["step"]), reverse=True)
    best = results[0]
    shutil.copyfile(run_dir / "ckpt" / best["ckpt"], run_dir / "best_policy.pt")
    common.write_json_atomic(run_dir / "selection.json", dict(
        rule="en iyi 3 kontrol noktası (20 doğrulama bölümü) -> 100 doğrulama bölümüyle yeniden ölçüm -> ortalama getiri",
        val_seeds=[common.VAL_SEEDS[0], common.VAL_SEEDS[-1]], chosen=best, candidates=results))
    return best


def main():
    args = parse_args()
    import torch
    torch.set_num_threads(args.threads)

    cfg = configs.get_config(args.algo, config_file=args.config, overrides=configs.parse_overrides(args.set))
    if args.steps:
        cfg["steps"] = args.steps
    total_steps = int(cfg["steps"])

    run_dir = Path(args.run_dir) if args.run_dir else common.run_dir_for(args.algo, args.tag, args.seed)
    if (run_dir / "DONE").exists() and not args.overwrite:
        print(f"[atla] {run_dir} zaten tamamlanmış (yeniden için --overwrite)")
        return
    can_resume = args.resume and (run_dir / "resume" / "model.zip").exists()
    if run_dir.exists() and not can_resume:
        if any(run_dir.iterdir()) and not args.overwrite:
            sys.exit(f"{run_dir} dolu. Devam için --resume, baştan başlamak için --overwrite kullanın.")
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    import gymnasium
    import stable_baselines3
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.vec_env import DummyVecEnv

    cfg_path = run_dir / "config.json"
    meta = dict(algo=args.algo, tag=args.tag, seed=args.seed, cfg=cfg, resumed_at=[] if not cfg_path.exists() else None,
                env_id=common.ENV_ID, continuous=True, device=args.device, threads=args.threads,
                eval_every=args.eval_every, val_curve_seeds=[common.VAL_CURVE_SEEDS[0], common.VAL_CURVE_SEEDS[-1]],
                val_seeds=[common.VAL_SEEDS[0], common.VAL_SEEDS[-1]],
                versions=dict(python=platform.python_version(), torch=torch.__version__,
                              sb3=stable_baselines3.__version__, gymnasium=gymnasium.__version__),
                started=common.now_iso(), argv=sys.argv[1:])
    if cfg_path.exists():  # devam: orijinal config'i koru, devam zamanını ekle
        import json
        old = json.load(open(cfg_path, encoding="utf-8"))
        old.setdefault("resumed_at", []).append(common.now_iso())
        meta = old
    common.write_json_atomic(cfg_path, meta)

    n_envs = configs.n_envs_for(args.algo, cfg)
    part = len(list((run_dir / "monitor").glob("part*"))) if (run_dir / "monitor").exists() else 0
    # train_fuel_k > 0: YALNIZCA eğitimde yakıt cezası (1+k) katı (pilot deney); train_touchdown_k > 0: YALNIZCA eğitimde
    # sert iniş cezası (Aşama 8). Doğrulama/test hep orijinal ödül.
    env = make_vec_env(common.make_env, n_envs=n_envs, seed=args.seed, vec_env_cls=DummyVecEnv,
                       env_kwargs=dict(fuel_k=float(cfg.get("train_fuel_k", 0.0)),
                                       touchdown_k=float(cfg.get("train_touchdown_k", 0.0)),
                                       touchdown_v0=float(cfg.get("train_touchdown_v0", 0.25))),
                       monitor_dir=str(run_dir / "monitor" / f"part{part}"))
    (run_dir / "monitor" / f"part{part}").mkdir(parents=True, exist_ok=True)

    if can_resume:
        cls = configs.algo_class(args.algo)
        model = cls.load(str(run_dir / "resume" / "model.zip"), env=env, device=args.device)
        if args.algo in ("sac", "td3"):
            model.load_replay_buffer(str(run_dir / "resume" / "buffer.pkl"))
        print(f"[devam] {run_dir} adım {model.num_timesteps}'den")
        # devam noktasından sonra yazılmış (yeniden üretilecek) doğrulama satırlarını at: yinelenen adım olmasın
        vc = run_dir / "val_curve.csv"
        if vc.exists():
            import csv
            import io
            # ani kapanmada dosya sonuna NUL baytları / yarım satır düşebiliyor (2026-10-27): onları atla
            text = vc.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
            rows = []
            for r in csv.DictReader(io.StringIO(text)):
                try:
                    if None not in r and None not in r.values() and int(r["step"]) <= model.num_timesteps:
                        rows.append(r)
                except ValueError:
                    pass
            if rows:
                common.write_rows_csv(vc, rows)
            else:
                vc.unlink()
    else:
        model = configs.build_model(args.algo, cfg, env, args.seed, args.device)

    cb = make_callback(run_dir, args.algo, args.seed, args.tag, total_steps, args.eval_every,
                       args.resume_every, cfg)
    remaining = total_steps - model.num_timesteps
    t0 = time.time()
    try:
        if remaining > 0:
            model.learn(total_timesteps=remaining, callback=cb, reset_num_timesteps=not can_resume,
                        progress_bar=False)
            # son kontrol noktası + değerlendirme (adım eval aralığına denk gelmese de)
            if model.num_timesteps % args.eval_every != 0:
                cb.num_timesteps = model.num_timesteps
                cb._do_eval()
        model.save(str(run_dir / "final.zip"))
        if not args.no_select:
            best = select_best(run_dir, args.algo)
            print(f"[seçim] en iyi kontrol noktası {best['ckpt']} doğrulama(100) ort. {best['val100']['mean']:.1f}")
        cb.finish("done")
        (run_dir / "DONE").write_text(common.now_iso())
        print(f"[bitti] {run_dir} ({(time.time() - t0) / 60:.1f} dk)")
    except BaseException as exc:  # noqa: BLE001
        cb.finish("failed", error=f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
