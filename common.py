"""Ortak yardımcılar: ortam, tohum kümeleri, deterministik değerlendirme, dosya yazıcıları.

Tohum kümeleri BİRBİRİNDEN AYRIKTIR (dürüstlük kuralı):
  eğitim   : 0-4      (nihai koşular, her koşunun kendi tohumu)
  Optuna   : 100-199  (hiperparametre deneme koşuları)
  doğrulama: 5000-5099 (kontrol noktası / hiperparametre seçimi)
  test     : 10000-10099 (yalnızca en sonda, bir kez)
"""
import _deps  # noqa: F401

import csv
import json
import os
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
ENV_ID = "LunarLander-v3"

TRAIN_SEEDS = list(range(0, 5))
TUNE_SEED_START = 100
VAL_SEEDS = list(range(5000, 5100))
VAL_CURVE_SEEDS = VAL_SEEDS[:20]       # öğrenme eğrisi için hızlı (20 bölüm)
TEST_SEEDS = list(range(10000, 10100))
FROZEN_FILE = ROOT / "FROZEN"          # bu dosya yoksa test değerlendirmesi reddedilir

# Aşama 4 (çakılma %0 hedefi). Eski test 10000-10099 bir kez kullanıldı -> artık GELİŞTİRME verisi sayılır.
VAL2_SEEDS = list(range(5100, 5600))    # çakılmaya duyarlı kontrol noktası seçimi (yeni)
VAL3_SEEDS = list(range(5600, 6000))    # gruplar arası sıralama için BAĞIMSIZ doğrulama (seçimde kullanılmaz)
TEST2_SEEDS = list(range(20000, 20100))   # YENİ resmi test (100 bölüm), yalnızca en sonda, bir kez
TEST2X_SEEDS = list(range(20100, 21000))  # ek dayanıklılık testi (900 bölüm), resmi testle birlikte bir kez
FROZEN2_FILE = ROOT / "FROZEN2"

# Aşama 5 (290 denemesi). 20000-20999 bir kez kullanıldı -> yeni kümeler.
VAL4_SEEDS = list(range(6000, 6400))      # gruplar arası sıralama v3 (yeni, bağımsız)
TEST3_SEEDS = list(range(30000, 30100))   # YENİ resmi test v3 (100 bölüm)
TEST3X_SEEDS = list(range(30100, 31000))  # ek test v3 (900 bölüm)
FROZEN3_FILE = ROOT / "FROZEN3"

# Aşama 6 (sınırları zorlama). 30000-30999 bir kez kullanıldı -> yeni kümeler.
VAL5_SEEDS = list(range(6400, 6800))      # gruplar arası sıralama v4 (yeni, bağımsız)
TEST4_SEEDS = list(range(40000, 40100))   # YENİ resmi test v4 (100 bölüm)
TEST4X_SEEDS = list(range(40100, 41000))  # ek test v4 (900 bölüm)
FROZEN4_FILE = ROOT / "FROZEN4"

# Aşama 7 (290 + sıfır çakılma). 40000-40999 bir kez kullanıldı -> yeni kümeler.
VAL6_SEEDS = list(range(6800, 7200))      # gruplar arası sıralama v5 (yeni, bağımsız)
TEST5_SEEDS = list(range(50000, 50100))   # YENİ resmi test v5 (100 bölüm)
TEST5X_SEEDS = list(range(50100, 51000))  # ek test v5 (900 bölüm)
FROZEN5_FILE = ROOT / "FROZEN5"

# Aşama 8 ("erken fren", hedef: sıfır çakılma). 50000-50999 bir kez kullanıldı -> yeni kümeler. Çakılma çok nadir
# (~%0,02-0,08) olduğu için doğrulama ve test tohum başına 2000 bölüm (grup başına 10 000).
VAL7_SEEDS = list(range(7200, 9200))      # gruplar arası sıralama v6 (yeni, bağımsız, 2000 bölüm)
TEST6_SEEDS = list(range(60000, 60100))   # YENİ resmi test v6 (100 bölüm)
TEST6X_SEEDS = list(range(60100, 62000))  # ek test v6 (1900 bölüm)
FROZEN6_FILE = ROOT / "FROZEN6"

# Aşama 9 (SAC büyük ağ). 60000-61999 bir kez kullanıldı -> yeni kümeler (önceki hiçbir kümeyle çakışmaz).
VAL8_SEEDS = list(range(70000, 72000))    # gruplar arası sıralama v7 (yeni, bağımsız, 2000 bölüm)
TEST7_SEEDS = list(range(80000, 80100))   # YENİ resmi test v7 (100 bölüm)
TEST7X_SEEDS = list(range(80100, 82000))  # ek test v7 (1900 bölüm)
FROZEN7_FILE = ROOT / "FROZEN7"

# Aşama 10 (agresif + frenli SAC). 80000-81999 Aşama 9 testine ayrıldı -> yeni kümeler (önceki hiçbir kümeyle çakışmaz).
VAL9_SEEDS = list(range(90000, 92000))      # gruplar arası sıralama v8 (yeni, bağımsız, 2000 bölüm)
TEST8_SEEDS = list(range(100000, 100100))   # YENİ resmi test v8 (100 bölüm)
TEST8X_SEEDS = list(range(100100, 102000))  # ek test v8 (1900 bölüm)
FROZEN8_FILE = ROOT / "FROZEN8"

SOLVED = 200.0


def latest_main():
    """Ana sonuç: (grup, video tohumu, kontrol noktası) — results/decision.json (Aşama 10'un dondurulmuş kararı)."""
    d = json.load(open(ROOT / "results" / "decision.json", encoding="utf-8"))
    group, _, suf = d["main"].partition("@")
    return group, int(d["main_video_seed"]), f"best_{suf or 'v2'}"


def ckpt_for_group(run_dir, suffix=""):
    """'algo/etiket@ek' grubunun kontrol noktası: '@800k' -> best_800k; ek yoksa best_v2 (varsa) ya da best."""
    if suffix:
        return f"best_{suffix}"
    return "best_v2" if (Path(run_dir) / "best_policy_v2.pt").exists() else "best"


def require_ckpt(run_dir, ckpt):
    """Kontrol noktası dosyası yoksa, mevcut olanları listeleyip anlaşılır bir mesajla çıkar."""
    run_dir = Path(run_dir)
    if ckpt == "final":
        path = run_dir / "final.zip"
    elif ckpt == "best" or ckpt.startswith("best_"):
        path = run_dir / ("best_policy.pt" if ckpt == "best" else f"best_policy_{ckpt[5:]}.pt")
    else:
        path = Path(ckpt)
    if not path.exists():
        have = sorted("best" if f.stem == "best_policy" else "best_" + f.stem[len("best_policy_"):]
                      for f in run_dir.glob("best_policy*.pt"))
        raise SystemExit(f"Kontrol noktası bulunamadı: {path}\nBu koşuda olanlar: {', '.join(have + ['final'])}")


def make_env(fuel_k=0.0, touchdown_k=0.0, touchdown_v0=0.25):
    """Değerlendirmede HER ZAMAN değiştirilmemiş ortam (fuel_k=0, touchdown_k=0). fuel_k > 0 ve touchdown_k > 0
    yalnızca EĞİTİM ödülünü değiştirir (yakıt pilotu; Aşama 8 "erken fren")."""
    import gymnasium as gym
    env = gym.make(ENV_ID, continuous=True)
    if fuel_k and fuel_k > 0:
        env = ExtraFuelPenalty(env, fuel_k)
    if touchdown_k and touchdown_k > 0:
        env = TouchdownPenalty(env, touchdown_k, touchdown_v0)
    return env


def _touchdown_wrapper():
    import gymnasium as gym

    class TouchdownPenalty(gym.Wrapper):
        """YALNIZCA EĞİTİM (Aşama 8, "erken fren"): bir bacak bölümde İLK kez yere değdiğinde, temastan hemen önceki
        dikey düşüş hızı (gözlem vy) v0'ı aşıyorsa ek ceza: k * (|vy| - v0). Kalan çakılmaların tek ortak noktası
        sert inişti (scripts/crash_analysis_v5.py: çakılanlarda vy ortancası -0,49, normal inişlerde -0,23).
        Değerlendirme ve rapor ortamı bunu KULLANMAZ."""

        def __init__(self, env, k, v0):
            super().__init__(env)
            self.k, self.v0 = float(k), float(v0)
            self.prev, self.touched = None, False

        def reset(self, **kwargs):
            obs, info = self.env.reset(**kwargs)
            self.prev, self.touched = obs, False
            return obs, info

        def step(self, action):
            obs, r, term, trunc, info = self.env.step(action)
            if not self.touched and (obs[6] > 0 or obs[7] > 0):
                self.touched = True
                r = r - self.k * max(0.0, -float(self.prev[3]) - self.v0)
            self.prev = obs
            return obs, r, term, trunc, info

    return TouchdownPenalty


def TouchdownPenalty(env, k, v0):  # noqa: N802
    return _touchdown_wrapper()(env, k, v0)


def _fuel_cost(action):
    """Ortamın kendi yakıt cezası formülü (lunar_lander.py: ana 0.30*m_power, yan 0.03*s_power)."""
    a0, a1 = float(action[0]), float(action[1])
    m = (min(max(a0, 0.0), 1.0) + 1.0) * 0.5 if a0 > 0.0 else 0.0
    s = min(max(abs(a1), 0.5), 1.0) if abs(a1) > 0.5 else 0.0
    return 0.30 * m + 0.03 * s


def _extra_fuel_wrapper():
    import gymnasium as gym

    class ExtraFuelPenalty(gym.Wrapper):
        """YALNIZCA EĞİTİM PİLOTU: yakıt cezasını (1+k) katına çıkarır (ek ceza = k * ortamın yakıt cezası).
        Sonlanan adımda (iniş +100 / çakılma -100) ortam zaten yakıt saymaz; burada da eklenmez.
        Değerlendirme ve rapor ortamı bunu KULLANMAZ."""

        def __init__(self, env, k):
            super().__init__(env)
            self.k = float(k)

        def step(self, action):
            obs, r, term, trunc, info = self.env.step(action)
            if not term:
                r = r - self.k * _fuel_cost(action)
            return obs, r, term, trunc, info

    return ExtraFuelPenalty


def ExtraFuelPenalty(env, k):  # noqa: N802
    return _extra_fuel_wrapper()(env, k)


# ------------------------------------------------------------------ değerlendirme
def run_episode(env, act_fn, seed):
    """Tek bölüm (deterministik politika). Sonuç sınıfı:
    crash   : bölüm sonlandı ve son adım ödülü -100 (gövde çarpması VEYA ekran dışına çıkma)
    landed  : bölüm sonlandı ve son adım ödülü +100 (araç durup uyudu)
    timeout : 1000 adım sınırı
    """
    obs, _ = env.reset(seed=int(seed))
    total, steps, last_r = 0.0, 0, 0.0
    terminated = truncated = False
    while not (terminated or truncated):
        obs, r, terminated, truncated, _ = env.step(act_fn(obs))
        total += float(r)
        steps += 1
        last_r = float(r)
    if terminated and last_r <= -99.999:
        outcome = "crash"
    elif terminated and last_r >= 99.999:
        outcome = "landed"
    elif truncated:
        outcome = "timeout"
    else:
        outcome = "other"
    return dict(seed=int(seed), ret=total, length=steps, outcome=outcome, last_reward=last_r)


def evaluate_episodes(act_fn, seeds, env=None):
    env = env if env is not None else make_env()
    rows = [run_episode(env, act_fn, s) for s in seeds]
    return rows


def summarize(rows):
    r = np.array([x["ret"] for x in rows], dtype=float)
    n = len(r)
    outc = [x["outcome"] for x in rows]
    return dict(
        n=n,
        mean=float(r.mean()),
        std=float(r.std(ddof=1)) if n > 1 else 0.0,
        median=float(np.median(r)),
        min=float(r.min()),
        max=float(r.max()),
        success=float((r >= SOLVED).mean()),
        crash=float(np.mean([o == "crash" for o in outc])),
        timeout=float(np.mean([o == "timeout" for o in outc])),
        landed=float(np.mean([o == "landed" for o in outc])),
    )


def load_policy(algo, path, device="cpu"):
    from stable_baselines3.common.policies import ActorCriticPolicy
    from stable_baselines3.sac.policies import SACPolicy
    from stable_baselines3.td3.policies import TD3Policy
    cls = dict(sac=SACPolicy, td3=TD3Policy, ppo=ActorCriticPolicy)[algo]
    return cls.load(str(path), device=device)


def policy_act_fn(policy):
    def act(obs):
        a, _ = policy.predict(obs, deterministic=True)
        return a
    return act


# ------------------------------------------------------------------ dosya yardımcıları
def write_json_atomic(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def append_csv(path, row: dict):
    path = Path(path)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


def write_rows_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def run_dir_for(algo, tag, seed):
    return RUNS / algo / tag / f"seed{seed}"


def now_iso():
    return time.strftime("%Y-%m-%d %H:%M:%S")
