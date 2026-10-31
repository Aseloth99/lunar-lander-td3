"""En iyi ajanın GIF + MP4'ü (birkaç bölüm, puanlar ekranda; deterministik politika).

"En iyi ajan" DOĞRULAMA sonucuyla seçilir (selection.json), test sonucuna bakılmaz. Gösterilen bölümler,
seçim yapılmadan, test tohumlarının İLK n tanesidir (10000, 10001, ...), yani ayıklanmış değildir.

  python3 make_video.py --algo sac --tag tuned --out results/en_iyi_ajan            # en iyi tohumu otomatik seç
  python3 make_video.py --run-dir runs/sac/tuned/seed2 --episodes 4 --out results/en_iyi_ajan
Test koruması: FROZEN dosyası yoksa test tohumlarıyla video üretilmez (yerine --split val kullanın).
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import _deps  # noqa: F401,E402

import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import common  # noqa: E402
from evaluate import load_for_eval  # noqa: E402

W, H = 480, 320


def pick_best_seed(algo, tag):
    best, best_v = None, -1e18
    for d in sorted((common.RUNS / algo / tag).glob("seed*")):
        sel = d / "selection.json"
        if sel.exists() and (d / "DONE").exists():
            v = json.load(open(sel, encoding="utf-8"))["chosen"]["val100"]["mean"]
            if v > best_v:
                best, best_v = d, v
    if best is None:
        sys.exit("seçilebilecek tamamlanmış koşu yok")
    print(f"en iyi tohum (doğrulama ort. {best_v:.1f}): {best}")
    return best


def font(size, bold=False):
    import matplotlib
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name), size)


def overlay(frame, lines, color=(255, 255, 255), banner=None):
    img = Image.fromarray(frame).resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 58], fill=(0, 0, 0, 150))
    for i, t in enumerate(lines):
        d.text((8, 5 + 17 * i), t, fill=color, font=font(14, bold=(i == 0)))
    if banner:
        text, bg = banner
        d.rectangle([0, H - 40, W, H], fill=bg)
        d.text((10, H - 33), text, fill=(255, 255, 255, 255), font=font(18, bold=True))
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", default=None)
    p.add_argument("--algo", default=None)
    p.add_argument("--tag", default=None)
    p.add_argument("--episodes", type=int, default=4)
    p.add_argument("--split", choices=["test", "test2", "test3", "test4", "test5", "test6", "test7", "test8", "val"], default="test")
    p.add_argument("--ckpt", default="best", help="best | best_v2")
    p.add_argument("--out", required=True, help="çıktı yolu (uzantısız)")
    p.add_argument("--skip", type=int, default=2, help="GIF için her n. kare")
    p.add_argument("--colors", type=int, default=64, help="GIF palet renk sayısı (ffmpeg varsa)")
    p.add_argument("--lang", choices=["tr", "en"], default="tr", help="ekrandaki yazıların dili")
    a = p.parse_args()
    T = dict(tr=dict(test="test", val="doğrulama", ep="bölümü", seed="tohum", step="adım", score="puan",
                     crash="ÇAKILMA", land="İNİŞ", timeout="ZAMAN AŞIMI"),
             en=dict(test="test", val="validation", ep="episode", seed="seed", step="step", score="score",
                     crash="CRASH", land="LANDED", timeout="TIMEOUT"))[a.lang]

    frozen = {"test": common.FROZEN_FILE, "test2": common.FROZEN2_FILE, "test3": common.FROZEN3_FILE,
              "test4": common.FROZEN4_FILE, "test5": common.FROZEN5_FILE,
              "test6": common.FROZEN6_FILE, "test7": common.FROZEN7_FILE, "test8": common.FROZEN8_FILE}.get(a.split)
    if frozen is not None and not frozen.exists():
        sys.exit(f"REDDEDİLDİ: {frozen.name} yok; test tohumlarıyla video üretilmez (geçici olarak --split val kullanın).")
    run_dir = Path(a.run_dir) if a.run_dir else pick_best_seed(a.algo, a.tag)
    cfg = json.load(open(run_dir / "config.json", encoding="utf-8"))
    algo = cfg["algo"]
    policy = load_for_eval(run_dir, algo, a.ckpt)
    act = common.policy_act_fn(policy)
    seeds = {"test": common.TEST_SEEDS, "test2": common.TEST2_SEEDS, "test3": common.TEST3_SEEDS, "test4": common.TEST4_SEEDS,
             "test5": common.TEST5_SEEDS, "test6": common.TEST6_SEEDS, "test7": common.TEST7_SEEDS, "test8": common.TEST8_SEEDS,
             "val": common.VAL_SEEDS}[a.split][: a.episodes]

    import gymnasium as gym
    env = gym.make(common.ENV_ID, continuous=True, render_mode="rgb_array")
    frames, results = [], []
    split_name = T["test"] if a.split.startswith("test") else T["val"]
    for k, sd in enumerate(seeds):
        obs, _ = env.reset(seed=int(sd))
        total, t, done, last_r, term = 0.0, 0, False, 0.0, False
        head = f"{algo.upper()} · {split_name} {T['ep']} {k + 1}/{len(seeds)} ({T['seed']} {sd})"
        while not done:
            frame = env.render()
            frames.append(overlay(frame, [head, f"{T['step']} {t:4d}", f"{T['score']} {total:7.1f}"]))
            obs, r, term, trunc, _ = env.step(act(obs))
            total += float(r)
            last_r = float(r)
            t += 1
            done = term or trunc
        kind = "crash" if term and last_r <= -99.999 else ("land" if term and last_r >= 99.999 else "timeout")
        outcome = T[kind]
        bg = (200, 60, 30, 230) if kind == "crash" else ((0, 120, 80, 230) if kind == "land" else (120, 120, 120, 230))
        final = env.render()
        for _ in range(30):  # sonucu ~1 sn göster
            frames.append(overlay(final, [head, f"{T['step']} {t:4d}", f"{T['score']} {total:7.1f}"],
                                  banner=(f"{outcome} · {T['score']} {total:.1f}", bg)))
        results.append((sd, total, outcome))
        print(f"{T['ep']} {k + 1}: {T['seed']} {sd} {T['score']} {total:.1f} {outcome}")
    env.close()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as tmp:
            for i, f in enumerate(frames):
                f.save(f"{tmp}/{i:06d}.png")
            # GIF: bütün karelerden tek ortak palet, titreşimsiz (düz renkli sahne), sonraki karelerde yalnızca değişen
            # dikdörtgen yazılır -> aynı görüntü, çok daha küçük dosya
            vf = (f"fps={30 / a.skip:g},split[a][b];[a]palettegen=max_colors={a.colors}[p];"
                  "[b][p]paletteuse=dither=none:diff_mode=rectangle")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", f"{tmp}/%06d.png", "-vf", vf,
                            "-loop", "0", str(out) + ".gif"], check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", f"{tmp}/%06d.png",
                            "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(out) + ".mp4"], check=True)
    else:
        gif_frames = [f.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for f in frames[:: a.skip]]
        gif_frames[0].save(str(out) + ".gif", save_all=True, append_images=gif_frames[1:],
                           duration=int(1000 / 30 * a.skip), loop=0, optimize=True, disposal=2)
    (Path(str(out) + ".json")).write_text(json.dumps(dict(
        run_dir=str(run_dir.resolve().relative_to(common.ROOT)), split=a.split,
        episodes=[dict(seed=s, score=round(sc, 2), outcome=o) for s, sc, o in results]), ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"yazıldı: {out}.gif (+ .mp4, .json)")


if __name__ == "__main__":
    main()
