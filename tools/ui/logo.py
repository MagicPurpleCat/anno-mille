"""Логотип Anno Mille: знак «M» (1000 римскими) + надпись ANNO MILLE шрифтом Cinzel.

    python logo.py concepts           -> out/logo_concepts.png (3 варианта)
    python logo.py build <A|B|C>      -> out/logo/: menu_logo.png 1024x256, icon_512.png, icon_128.png
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
_FD = os.path.join(HERE, "src") if os.path.isdir(os.path.join(HERE, "src")) else os.path.join(HERE, "fonts")
CINZEL = os.path.join(_FD, "Cinzel.ttf")
INTER = os.path.join(_FD, "Inter-Medium.ttf")
TEXT, GOLD, MUTED, BG = (244, 244, 245), (232, 194, 106), (160, 160, 168), (14, 14, 16)


def cinzel(size, weight=700):
    f = ImageFont.truetype(CINZEL, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def glow(img, draw_fn, blur=10, alpha=90):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(g), (255, 255, 255, alpha))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))
    draw_fn(ImageDraw.Draw(img), None)


def spaced(d, xy, text, font, fill, spacing, anchor="mm"):
    """Текст с разрядкой (буквы чуть разнесены, как в надписях на камне)."""
    widths = [d.textlength(c, font=font) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = xy[0] - total / 2 if anchor[0] == "m" else xy[0]
    for c, w in zip(text, widths):
        d.text((x, xy[1]), c, font=font, fill=fill, anchor="lm" if anchor[1] == "m" else "ls")
        x += w + spacing
    return total


def emblem(size, style):
    """Квадратный знак: A — медальон, B — щит, C — ромб."""
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = max(2, s // 64)
    if style == "A":
        d.ellipse([w, w, s - w, s - w], fill=(20, 20, 23, 255), outline=GOLD, width=w * 2)
        d.ellipse([s * 0.09, s * 0.09, s * 0.91, s * 0.91], outline=(*GOLD, 120), width=w)
        d.text((s / 2, s * 0.53), "M", font=cinzel(int(s * 0.58)), fill=TEXT, anchor="mm")
    elif style == "B":
        # каплевидный щит: прямой верх, боковины до середины, затем дуги сходятся к острию
        pts = [(s * 0.14, s * 0.07), (s * 0.86, s * 0.07)]
        for t in range(0, 41):
            a = t / 40 * math.pi
            pts.append((s * 0.5 + s * 0.36 * math.cos(a), s * 0.45 + s * 0.48 * math.sin(a) ** 1.3))
        d.polygon(pts, fill=(20, 20, 23, 255), outline=GOLD, width=w * 2)
        d.text((s / 2, s * 0.44), "M", font=cinzel(int(s * 0.5)), fill=TEXT, anchor="mm")
    else:
        return diamond_emblem(s)
    return im


def draw_m(d, cx, cy, h, color):
    """Строго симметричная буква M: две ножки, две диагонали одной толщины, сходятся точно в центре."""
    w = h * 1.0                  # ширина буквы
    sw = h * 0.16                # толщина ножки
    dw = sw * 1.15               # горизонтальная толщина диагонали
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    vy = y0 + h * 0.78           # нижняя точка средней «V»
    d.rectangle([x0, y0, x0 + sw, y1], fill=color)                                  # левая ножка
    d.rectangle([x1 - sw, y0, x1, y1], fill=color)                                  # правая ножка
    d.polygon([(x0, y0), (x0 + dw, y0), (cx + dw / 2, vy), (cx - dw / 2, vy)], fill=color)   # левая диагональ
    d.polygon([(x1, y0), (x1 - dw, y0), (cx - dw / 2, vy), (cx + dw / 2, vy)], fill=color)   # правая диагональ
    ser, st = sw * 0.55, sw * 0.32                                                  # засечки
    for xa, xb in ((x0 - ser, x0 + sw + ser), (x1 - sw - ser, x1 + ser)):
        d.rectangle([xa, y1 - st, xb, y1], fill=color)                              # внизу ножек
    d.rectangle([x0 - ser, y0, x0 + dw, y0 + st], fill=color)                       # вверху слева
    d.rectangle([x1 - dw, y0, x1 + ser, y0 + st], fill=color)                       # вверху справа


def diamond_emblem(s):
    """Знак C: ромб с золотой рамкой и симметричной M. Рисуется в 4x и уменьшается для гладких краёв."""
    k = 4
    S = s * k
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = max(2 * k, S // 40)
    c = S / 2
    d.polygon([(c, w), (S - w, c), (c, S - w), (w, c)], fill=GOLD)
    i = w * 2.2
    d.polygon([(c, i), (S - i, c), (c, S - i), (i, c)], fill=(20, 20, 23, 255))
    j = w * 3.4
    d.polygon([(c, j), (S - j, c), (c, S - j), (j, c)], outline=(*GOLD, 90), width=max(1, w // 3))
    draw_m(d, c, c + S * 0.005, S * 0.34, TEXT)
    return im.resize((s, s), Image.LANCZOS)


def menu_logo(style):
    """1024x256 (в игре видна верхняя часть 1024x176): знак слева, ANNO MILLE справа."""
    im = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
    em = emblem(150, style)
    word = cinzel(96)
    d = ImageDraw.Draw(im)
    tw = sum(d.textlength(c, font=word) for c in "ANNO MILLE") + 10 * 9
    total = 150 + 36 + tw
    x0 = (1024 - total) / 2
    im.alpha_composite(em, (int(x0), 13))
    glow(im, lambda dd, col: spaced(dd, (x0 + 150 + 36, 92), "ANNO MILLE", word, col or TEXT, 10, anchor="lm"), blur=12, alpha=70)
    return im


def concepts():
    W, H = 1500, 960
    sheet = Image.new("RGBA", (W, H), (*BG, 255))
    bg = Image.open(os.path.join(HERE, "out", "bg_preview.png")).convert("RGBA").resize((960, 540))
    d = ImageDraw.Draw(sheet)
    names = {"A": "A · Медальон", "B": "B · Щит", "C": "C · Ромб"}
    for i, st in enumerate("ABC"):
        y = 20 + i * 312
        d.text((30, y), names[st], font=ImageFont.truetype(INTER, 26), fill=TEXT)
        ic = emblem(220, st)
        sheet.alpha_composite(ic, (30, y + 50))
        sheet.alpha_composite(emblem(64, st), (270, y + 206))
        sheet.alpha_composite(emblem(32, st), (350, y + 238))
        menu = bg.crop((0, 0, 960, 270)).copy()
        menu.alpha_composite(menu_logo(st).resize((768, 192), Image.LANCZOS), (96, 20))
        md = ImageDraw.Draw(menu)
        md.text((480, 205), "Год тысячный · Millénaire", font=ImageFont.truetype(INTER, 22), fill=MUTED, anchor="mm")
        sheet.alpha_composite(menu, (520, y + 20))
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sheet.convert("RGB").save(os.path.join(HERE, "out", "logo_concepts.png"))


if __name__ == "__main__":
    if sys.argv[1] == "concepts":
        concepts()
    else:
        st, out = sys.argv[2], os.path.join(HERE, "out", "logo")
        os.makedirs(out, exist_ok=True)
        menu_logo(st).save(os.path.join(out, "menu_logo.png"))
        for n in (512, 256, 128):
            emblem(n, st).save(os.path.join(out, f"icon_{n}.png"))
    print("ok")
