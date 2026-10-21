"""Фон-петля главного меню: те же формулы, что Background в guns-lol-andy-warhol/src/Video.jsx,
отрисованные кадрами в FMA-анимацию FancyMenu (zip: metadata.json + frames/N.png).

Запуск: python bg.py [ширина] [кадров/с]   (по умолчанию 960 и 24)
Результат: out/millenaire_bg.fma и out/bg_preview.png
"""
import io, json, math, os, sys, zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W = int(sys.argv[1]) if len(sys.argv) > 1 else 960
FPS = int(sys.argv[2]) if len(sys.argv) > 2 else 24
H = W * 9 // 16
S = W / 1920.0                        # масштаб относительно 1920×1080 оригинала
LOOP_SEC = round(60 / 125 * 60 * 4 * 8) / 60   # LOOP_FRAMES = round(BAR*8) при 60 fps -> 15.36 c
FRAMES = round(LOOP_SEC * FPS)

WAVES = [  # y, амплитуды, волновые числа, обороты за петлю, непрозрачность, размытие (как в Video.jsx)
    dict(y=0.66, a=(70, 28), k=(1.1, 2.3), n=(1, -2), o=0.05, blur=34),
    dict(y=0.74, a=(60, 24), k=(1.6, 3.1), n=(-1, 2), o=0.06, blur=26),
    dict(y=0.82, a=(50, 20), k=(0.9, 2.7), n=(2, -1), o=0.07, blur=20),
    dict(y=0.90, a=(40, 16), k=(1.4, 3.6), n=(-2, 3), o=0.06, blur=16),
]

# Градиент #0B0B0C -> #0F0F11 (55%) -> #121214
ys = np.linspace(0, 1, H)[:, None]
def lerp(a, b, t): return a + (b - a) * t
grad = np.where(ys < 0.55, lerp(np.array([11, 11, 12.]), np.array([15, 15, 17.]), ys / 0.55),
                lerp(np.array([15, 15, 17.]), np.array([18, 18, 20.]), (ys - 0.55) / 0.45))
BASE = np.broadcast_to(grad[:, None, :] if grad.ndim == 2 else grad, (H, W, 3)).astype(np.float32)
if BASE.shape != (H, W, 3):
    BASE = np.repeat(grad[:, None, :], W, axis=1).astype(np.float32)

# Виньетка: radial-gradient(ellipse 75% 70% at 50% 45%, transparent 40%, rgba(0,0,0,0.65) 100%)
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - 0.5 * W) / (0.75 * W)) ** 2 + ((yy - 0.45 * H) / (0.70 * H)) ** 2)
VIG = (np.clip((r - 0.4) / 0.6, 0, 1) * 0.65)[..., None].astype(np.float32)


def wave_mask(w, t):
    pts = []
    for i in range(49):
        x = (i / 48) * (1920 + 400) - 200
        u = (x / 1920) * math.pi * 2
        y = w["y"] * 1080
        for j, a in enumerate(w["a"]):
            y += a * math.sin(w["k"][j] * u + w["n"][j] * t + j * 1.7)
        pts.append((x * S, y * S))
    poly = [(-200 * S, (1080 + 200) * S)] + pts + [((1920 + 200) * S, (1080 + 200) * S)]
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(w["blur"] * S)), dtype=np.float32)[..., None] / 255.0


def frame(i):
    t = i / FRAMES * math.pi * 2
    img = BASE.copy()
    for w in WAVES:
        a = wave_mask(w, t) * w["o"]
        img = img * (1 - a) + 255.0 * a
    img = img * (1 - VIG)
    gray = img.mean(axis=2)                       # фон по сути серый — 8-битный L-PNG жмётся лучше
    return Image.fromarray(np.clip(gray + 0.5, 0, 255).astype(np.uint8), "L")


os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
dst = os.path.join(HERE, "out", "millenaire_bg.fma")
with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
    z.writestr("metadata.json", json.dumps({"loop_count": 0, "frame_time": round(1000 / FPS)}))
    for i in range(FRAMES):
        im = frame(i)
        buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
        z.writestr(f"frames/{i}.png", buf.getvalue())
        if i == 0:
            im.convert("RGB").save(os.path.join(HERE, "out", "bg_preview.png"))
print(f"{W}x{H}, {FPS} fps, {FRAMES} frames, loop {LOOP_SEC:.2f}s, {os.path.getsize(dst) / 1e6:.1f} MB")
