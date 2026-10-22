"""Загрузочный экран Anno Mille (Drippy Loading Screen + FancyMenu) в стиле главного меню.

Запуск: python loading.py   (нужен out/millenaire_bg.fma от bg.py — из него берётся кадр фона для раннего окна)
Результат в out/loading/:
  loading_logo.fma      — знак и ANNO MILLE: дышащее золотое свечение за ромбом, блик по надписи,
                          подпись и орнамент с бегущими искрами (петля 3.6 с)
  early_bg.png          — кадр фона-волн для раннего окна NeoForge
  early_logo.png        — тот же анимированный логотип в APNG для раннего окна
  early_bar_bg.png, early_bar_progress.png — полоса загрузки раннего окна
Файлы кладутся в pack/config/fancymenu/assets/.
"""
import io, json, math, os, sys, zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import logo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "loading")
W, H = 1100, 380
OX, OY = 38, 40                        # поля, чтобы свечение ромба не обрезалось краем кадра
FPS, LOOP_SEC = 20, 3.6
FRAMES = round(FPS * LOOP_SEC)
GOLD, MUTED, TEXT = logo.GOLD, (154, 154, 162), logo.TEXT
ORN_Y, ORN_HALF = 336, 300             # орнамент: высота и полудлина линий


def base():
    """Статичная часть: логотип меню, подпись и линии орнамента. Возвращает (картинка, центр ромба)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(logo.menu_logo("C"), (OX, OY))
    d = ImageDraw.Draw(im)
    sub = logo.ImageFont.truetype(logo.INTER, 22)
    logo.spaced(d, (W / 2, 278), "ГОД ТЫСЯЧНЫЙ  ·  MILLÉNAIRE", sub, MUTED + (255,), 7)
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    for i in range(ORN_HALF):  # линии гаснут к краям
        a = int(150 * (1 - i / ORN_HALF) ** 1.6)
        for x in (W / 2 + 16 + i, W / 2 - 16 - i):
            ld.point((x, ORN_Y), fill=GOLD + (a,))
    im.alpha_composite(line)
    word = logo.cinzel(96)
    tw = sum(d.textlength(c, font=word) for c in "ANNO MILLE") + 10 * 9
    x0 = (1024 - (150 + 36 + tw)) / 2
    return im, (OX + x0 + 75, OY + 13 + 75)


def frame(static, emblem_c, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1. дышащее золотое свечение за ромбом
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = emblem_c
    r = 70 + 10 * pulse
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD + (int(40 + 60 * pulse),))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(28)))
    im.alpha_composite(static)
    # 2. блик: светлая диагональная полоса проходит по логотипу в первые 45% петли
    if t < 0.45:
        p = -160 + (W + 320) * (t / 0.45)
        band = Image.new("L", (W, H), 0)
        bd = ImageDraw.Draw(band)
        for k in range(-60, 61):
            a = int(140 * (1 - abs(k) / 60) ** 2)
            x = p + k
            bd.line([(x + 60, OY), (x - 60, OY + 200)], fill=a, width=1)
        mask = np.minimum(np.asarray(band), np.asarray(static.getchannel("A")))
        mask[OY + 200:] = 0                     # только знак и надпись, не подпись и орнамент
        light = Image.new("RGBA", (W, H), (255, 248, 230, 0))
        light.putalpha(Image.fromarray(mask))
        im.alpha_composite(light)
    # 3. орнамент: ромбик в центре и две искры, бегущие от центра к краям
    d = ImageDraw.Draw(im)
    s = 6 + 1.5 * pulse
    d.polygon([(W / 2, ORN_Y - s), (W / 2 + s, ORN_Y), (W / 2, ORN_Y + s), (W / 2 - s, ORN_Y)], fill=GOLD + (230,))
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sp)
    for phase in (0.0, 0.5):
        u = (t + phase) % 1
        a = math.sin(math.pi * u)
        for sign in (1, -1):
            x = W / 2 + sign * (18 + u * (ORN_HALF - 30))
            sd.ellipse([x - 4, ORN_Y - 4, x + 4, ORN_Y + 4], fill=(255, 236, 190, int(255 * a)))
    im.alpha_composite(sp.filter(ImageFilter.GaussianBlur(2.2)))
    im.alpha_composite(sp)
    return im


def write_fma(path, frames, fps):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("metadata.json", json.dumps({"loop_count": 0, "frame_time": round(1000 / fps)}))
        for i, f in enumerate(frames):
            buf = io.BytesIO()
            f.save(buf, "PNG", optimize=True)
            z.writestr(f"frames/{i}.png", buf.getvalue())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    static, emblem_c = base()
    frames = [frame(static, emblem_c, i / FRAMES) for i in range(FRAMES)]
    write_fma(os.path.join(OUT, "loading_logo.fma"), frames, FPS)
    # раннее окно NeoForge (Drippy Early Loading Module) умеет APNG: та же анимация, уменьшенная под окно
    small = [f.resize((550, 190), Image.LANCZOS) for f in frames]
    small[0].save(os.path.join(OUT, "early_logo.png"), save_all=True, append_images=small[1:], duration=round(1000 / FPS), loop=0, optimize=True)

    bg = os.path.join(HERE, "out", "millenaire_bg.fma")
    if not os.path.exists(bg):
        bg = os.path.join(HERE, "..", "..", "pack", "config", "fancymenu", "assets", "millenaire_bg.fma")
    with zipfile.ZipFile(bg) as z:
        Image.open(io.BytesIO(z.read("frames/0.png"))).convert("RGB").save(os.path.join(OUT, "early_bg.png"))
    Image.new("RGBA", (64, 4), (42, 42, 46, 255)).save(os.path.join(OUT, "early_bar_bg.png"))
    Image.new("RGBA", (64, 4), TEXT + (255,)).save(os.path.join(OUT, "early_bar_progress.png"))

    sheet = Image.new("RGBA", (W, H * 3), (14, 14, 16, 255))
    for k, i in enumerate((int(FRAMES * 0.15), int(FRAMES * 0.3), int(FRAMES * 0.75))):
        sheet.alpha_composite(frames[i], (0, H * k))
    sheet.convert("RGB").save(os.path.join(OUT, "preview.png"))
    print(f"{FRAMES} frames, {os.path.getsize(os.path.join(OUT, 'loading_logo.fma')) / 1e6:.1f} MB")
