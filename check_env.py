"""Kurulumu doğrular: paket sürümleri, Box2D, LunarLander-v3 (sürekli) ve kısa SAC denemesi."""
import _deps  # noqa: F401

import importlib
import time

for name in ["torch", "numpy", "gymnasium", "stable_baselines3", "optuna",
             "pandas", "scipy", "matplotlib", "PIL", "imageio", "pygame", "Box2D"]:
    try:
        mod = importlib.import_module(name)
        print(f"{name:20s} {getattr(mod, '__version__', 'ok')}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name:20s} HATA: {type(exc).__name__}: {exc}")

import torch
print("cuda kullanilabilir:", torch.cuda.is_available(), "| torch iş parçacığı:", torch.get_num_threads())

import gymnasium as gym
env = gym.make("LunarLander-v3", continuous=True)
obs, _ = env.reset(seed=0)
print("gözlem:", obs.shape, "eylem uzayı:", env.action_space)
total, steps, done = 0.0, 0, False
while not done:
    obs, r, term, trunc, _ = env.step(env.action_space.sample())
    total += r
    steps += 1
    done = term or trunc
print(f"rastgele politika: {steps} adım, puan {total:.1f}, son ödül {r}")

# Çok kısa SAC denemesi (hız için gerçek ölçüm bench.py'de)
from stable_baselines3 import SAC
model = SAC("MlpPolicy", env, learning_starts=200, device="cpu", verbose=0, seed=0)
t0 = time.time()
model.learn(total_timesteps=1000)
print(f"SAC 1000 adım (200'ü ısınma): {time.time() - t0:.1f} sn")
