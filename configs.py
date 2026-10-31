"""Hiperparametre ön ayarları ve model kurucu.

"zoo" ön ayarları rl-baselines3-zoo (master, hyperparams/{sac,td3,ppo}.yml,
LunarLanderContinuous-v3 girdileri) dosyasından elle doğrulanmıştır:
  SAC : n_timesteps 5e5, lr lin_7.3e-4 (doğrusal azalan), buffer 1e6, batch 256, gamma 0.99,
        tau 0.01, learning_starts 10000, ent_coef auto, ağ [400,300], train_freq 1, gradient_steps 1
  TD3 : n_timesteps 3e5, lr 1e-3, gamma 0.98, buffer 2e5, learning_starts 10000,
        normal gürültü sigma 0.1, ağ [400,300], train_freq 1, gradient_steps 1
        (yaml'da batch_size/tau yok -> SB3 varsayılanları: 256 / 0.005)
  PPO : n_envs 16, n_timesteps 1e6, n_steps 1024, batch 64, gae 0.98, gamma 0.999,
        n_epochs 4, ent_coef 0.01 (ağ ve lr yaml'da yok -> SB3 varsayılanları: [64,64] tanh, 3e-4)
"""
import _deps  # noqa: F401

import copy
import json
from pathlib import Path

ZOO = {
    "sac": dict(steps=500_000, lr=7.3e-4, lr_linear=True, buffer=1_000_000, batch=256, gamma=0.99,
                tau=0.01, learning_starts=10_000, net=[400, 300], train_freq=1, gradient_steps=1,
                ent_coef="auto"),
    "td3": dict(steps=300_000, lr=1e-3, lr_linear=False, buffer=200_000, batch=256, gamma=0.98,
                tau=0.005, learning_starts=10_000, net=[400, 300], train_freq=1, gradient_steps=1,
                noise_std=0.1, policy_delay=2),
    "ppo": dict(steps=1_000_000, lr=3e-4, lr_linear=False, n_envs=16, n_steps=1024, batch=64,
                gae_lambda=0.98, gamma=0.999, n_epochs=4, ent_coef=0.01, clip_range=0.2, net=[64, 64]),
}


def get_config(algo, preset="zoo", overrides=None, config_file=None):
    """ZOO taban + (json dosyası) + (komut satırı override'ları)."""
    cfg = copy.deepcopy(ZOO[algo])
    if config_file:
        with open(config_file, encoding="utf-8") as f:
            cfg.update(json.load(f))
    if overrides:
        cfg.update(overrides)
    return cfg


def parse_overrides(items):
    """['lr=3e-4', 'net=256,256', 'steps=200000'] -> dict (json benzeri tür çıkarımı)."""
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        if k == "net":
            out[k] = [int(x) for x in v.split(",")]
            continue
        try:
            out[k] = json.loads(v.lower() if v.lower() in ("true", "false") else v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def _lr(cfg):
    if cfg.get("lr_linear"):
        base = cfg["lr"]
        return lambda progress_remaining: base * progress_remaining
    return cfg["lr"]


def build_model(algo, cfg, env, seed, device="cpu"):
    import numpy as np
    from stable_baselines3 import PPO, SAC, TD3
    from stable_baselines3.common.noise import NormalActionNoise

    net = list(cfg["net"])
    if algo == "sac":
        return SAC("MlpPolicy", env, learning_rate=_lr(cfg), buffer_size=cfg["buffer"], batch_size=cfg["batch"],
                   gamma=cfg["gamma"], tau=cfg["tau"], learning_starts=cfg["learning_starts"],
                   train_freq=cfg["train_freq"], gradient_steps=cfg["gradient_steps"], ent_coef=cfg["ent_coef"],
                   target_entropy=cfg.get("target_entropy", "auto"),  # Aşama 9: daha az rastgelelik denemesi
                   policy_kwargs=dict(net_arch=net), seed=seed, device=device, verbose=0)
    if algo == "td3":
        n_act = env.action_space.shape[0]
        noise = NormalActionNoise(mean=np.zeros(n_act), sigma=cfg["noise_std"] * np.ones(n_act))
        return TD3("MlpPolicy", env, learning_rate=_lr(cfg), buffer_size=cfg["buffer"], batch_size=cfg["batch"],
                   gamma=cfg["gamma"], tau=cfg["tau"], learning_starts=cfg["learning_starts"],
                   train_freq=cfg["train_freq"], gradient_steps=cfg["gradient_steps"],
                   policy_delay=cfg["policy_delay"], action_noise=noise,
                   policy_kwargs=dict(net_arch=net), seed=seed, device=device, verbose=0)
    if algo == "ppo":
        return PPO("MlpPolicy", env, learning_rate=_lr(cfg), n_steps=cfg["n_steps"], batch_size=cfg["batch"],
                   gae_lambda=cfg["gae_lambda"], gamma=cfg["gamma"], n_epochs=cfg["n_epochs"],
                   ent_coef=cfg["ent_coef"], clip_range=cfg["clip_range"],
                   policy_kwargs=dict(net_arch=dict(pi=net, vf=net)), seed=seed, device=device, verbose=0)
    raise ValueError(algo)


def n_envs_for(algo, cfg):
    return int(cfg.get("n_envs", 1)) if algo == "ppo" else 1


def algo_class(algo):
    from stable_baselines3 import PPO, SAC, TD3
    return dict(sac=SAC, td3=TD3, ppo=PPO)[algo]
