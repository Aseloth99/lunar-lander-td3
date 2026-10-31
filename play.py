"""Ajanı CANLI izle: bir pencerede gerçek zamanlı oynar, adım ve puan ekranda görünür.
Bölümler her seferinde rastgele seçilir (hiç görülmemiş bölümler; tohum numarası ekrana yazılır).

  python3 play.py                            # ana sonuç ajanı (en son tamamlanan tur), 5 bölüm
  python3 play.py --episodes 10 --speed 2    # 10 bölüm, 2 kat hızlı
  python3 play.py --group ppo/tuned --seed 1 # başka bir ajan
  python3 play.py --group sac/v4@800k        # aynı koşunun 800 bin adımdaki anı (@1600k: 1,6 milyon)
  python3 play.py --group sac/v4 --ckpt final  # kontrol noktasını açıkça seç
  python3 play.py --bolum 20001              # belirli bir bölümü tekrar izle
Windows'ta: 1-AJANI-CANLI-IZLE.bat dosyasına çift tıkla. Pencereyi kapatınca durur.
"""
import os
import platform

# Pencere sürücüsü: WSL'de WSLg (x11); Windows/macOS/Linux'ta platformun kendi varsayılanı. make_video içe aktarılırken
# (video için) "dummy" koyar; kullanıcı kendisi bir sürücü seçmediyse aşağıda geri alınır.
_USER_DRIVER = os.environ.get("SDL_VIDEODRIVER")
_WSL = "microsoft" in platform.uname().release.lower()
if _WSL and _USER_DRIVER is None:
    os.environ["SDL_VIDEODRIVER"] = "x11"
os.environ.setdefault("OMP_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import json  # noqa: E402

import numpy as np  # noqa: E402

import common  # noqa: E402
from evaluate import load_for_eval  # noqa: E402
from make_video import overlay  # noqa: E402

if _USER_DRIVER is None and not _WSL:
    os.environ.pop("SDL_VIDEODRIVER", None)

SCALE = 1.75


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--group", default=None, help="algo/etiket[@800k|@1600k] (varsayılan: ana sonuç)")
    p.add_argument("--ckpt", default=None, help="best | best_v2 | best_800k | best_1600k | final (varsayılan: gruptan)")
    p.add_argument("--seed", type=int, default=None, help="eğitim tohumu (varsayılan: ana sonucun video tohumu)")
    p.add_argument("--episodes", type=int, default=5)
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--bolum", type=int, nargs="*", default=None, help="izlenecek bölüm tohum(lar)ı")
    a = p.parse_args()

    main_group, main_seed, main_ckpt = common.latest_main()
    group = a.group or main_group
    seed = main_seed if a.seed is None else a.seed
    base, _, suf = group.partition("@")
    algo, tag = base.split("/")
    run_dir = common.RUNS / algo / tag / f"seed{seed}"
    ckpt = a.ckpt or (main_ckpt if a.group is None else common.ckpt_for_group(run_dir, suf))
    common.require_ckpt(run_dir, ckpt)
    act = common.policy_act_fn(load_for_eval(run_dir, algo, ckpt))
    if ckpt.startswith("best_") and ckpt[5:] in ("800k", "1600k"):
        tag += f"@{ckpt[5:]}"  # pencerede/ekranda hangi an olduğu görünsün
    seeds = a.bolum or list(np.random.default_rng().integers(1_000_000, 2_000_000, size=a.episodes))

    import gymnasium as gym
    import pygame
    from PIL import Image  # noqa: F401
    pygame.init()
    size = (int(480 * SCALE), int(320 * SCALE))
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption(f"Ay'a İniş — {algo.upper()} {tag} (tohum {seed})")
    clock = pygame.time.Clock()

    def show(img):
        surf = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
        screen.blit(pygame.transform.smoothscale(surf, size), (0, 0))
        pygame.display.flip()

    def alive():
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                return False
        return True

    env = gym.make(common.ENV_ID, continuous=True, render_mode="rgb_array")
    scores = []
    print(f"İzlenen ajan: {group} tohum {seed} ({ckpt}). Pencereyi kapatınca veya ESC'ye basınca durur.\n")
    for k, sd in enumerate(seeds):
        obs, _ = env.reset(seed=int(sd))
        total, t, done, r, term = 0.0, 0, False, 0.0, False
        head = f"{algo.upper()} {tag} · bölüm {k + 1}/{len(seeds)} (bölüm no {sd})"
        while not done:
            if not alive():
                pygame.quit()
                return
            show(overlay(env.render(), [head, f"adım {t:4d}", f"puan {total:7.1f}"]))
            clock.tick(int(50 * a.speed))
            obs, r, term, trunc, _ = env.step(act(obs))
            total += float(r)
            t += 1
            done = term or trunc
        outcome = "ÇAKILMA" if term and r <= -99.9 else ("İNİŞ" if term and r >= 99.9 else "ZAMAN AŞIMI")
        bg = (200, 60, 30, 230) if outcome == "ÇAKILMA" else ((0, 120, 80, 230) if outcome == "İNİŞ" else (120, 120, 120, 230))
        final = env.render()
        for _ in range(int(60 / max(a.speed, 0.5))):
            if not alive():
                pygame.quit()
                return
            show(overlay(final, [head, f"adım {t:4d}", f"puan {total:7.1f}"], banner=(f"{outcome} · puan {total:.1f}", bg)))
            clock.tick(50)
        scores.append(total)
        print(f"bölüm {k + 1}: bölüm no {sd:>8}  puan {total:6.1f}  {outcome}")
    if scores:
        print(f"\nortalama {np.mean(scores):.1f} | en düşük {min(scores):.1f} | en yüksek {max(scores):.1f}")
    pygame.quit()


if __name__ == "__main__":
    main()
