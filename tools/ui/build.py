"""Сборка ресурспака MillenaireUI: тёмный интерфейс в стиле фона-петли guns.lol.

Запуск:  python build.py "<путь к .minecraft>"
Шаблоны берутся из vanilla/ (извлечено из 1.21.1.jar) и из jar-модов в <.minecraft>/mods.
Результат: out/MillenaireUI/ (папка ресурспака) + out/report.txt.
"""
import io, json, os, re, shutil, sys, zipfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
GAME = sys.argv[1]
VAN = os.path.join(HERE, "vanilla", "assets", "minecraft")
OUT = os.path.join(HERE, "out", "MillenaireUI")
FONT_SEMI = os.path.join(HERE, "src", "Inter-SemiBold.ttf")
FONT_MED = os.path.join(HERE, "src", "Inter-Medium.ttf")

# ---------- палитра (из src/Video.jsx референса) ----------
BG = (18, 18, 20)            # #121214 — основной графит
BG_DEEP = (11, 11, 12)       # #0B0B0C
TEXT = (244, 244, 245)       # #F4F4F5
# Ванильные оттенки окон -> новые
CONTAINER_MAP = {
    (198, 198, 198): (30, 30, 34),     # панель #C6C6C6
    (255, 255, 255): (58, 58, 66),     # блик фаски / светлый край ячейки
    (85, 85, 85): (14, 14, 16),        # тень фаски
    (0, 0, 0): (6, 6, 7),              # чёрная заливка (окно с игроком и т.п.)
    (139, 139, 139): (12, 12, 14),     # ячейка
    (55, 55, 55): (4, 4, 5),           # тень ячейки
}
OUTLINE = (92, 92, 104)                # чёрный контур по краю текстуры -> тонкая светлая рамка
VANILLA_GRAYS = set(CONTAINER_MAP)
PANEL_GRAYS = {(198, 198, 198), (139, 139, 139)}

report = []


def out_path(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def vanilla_share(im):
    """Доля ванильных серых среди непрозрачных пикселей; 0, если нет панели/ячеек (значит это иконка)."""
    if max(im.size) < 32:          # мелкие спрайты — иконки, не окна
        return 0.0
    px = [p for p in im.getdata() if p[3] > 0]
    if not px:
        return 0.0
    panel = sum(1 for p in px if p[3] == 255 and p[:3] in PANEL_GRAYS)
    if panel / len(px) < 0.3:
        return 0.0
    return sum(1 for p in px if p[3] == 255 and p[:3] in VANILLA_GRAYS) / len(px)


def recolor_container(im):
    im = im.convert("RGBA")
    w, h = im.size
    src = im.load()
    out = im.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a != 255 or (r, g, b) not in CONTAINER_MAP:
                continue
            if (r, g, b) == (0, 0, 0):
                edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] == 0
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                dst[x, y] = (*(OUTLINE if edge else CONTAINER_MAP[(0, 0, 0)]), 255)
            else:
                dst[x, y] = (*CONTAINER_MAP[(r, g, b)], 255)
    return out


def darken_grays(im, keep_white=True):
    """Серые пиксели (HUD) -> тёмные, яркие белые (рамка выбора) остаются."""
    im = im.convert("RGBA")
    out = []
    for r, g, b, a in im.getdata():
        if a and max(r, g, b) - min(r, g, b) < 14 and not (keep_white and min(r, g, b) > 215):
            l = (r + g + b) / 3
            v = int(10 + l * 0.32)
            out.append((v, v, v + 2, a))
        else:
            out.append((r, g, b, a))
    im.putdata(out)
    return im


# ---------- 1. окна (ванилла) ----------
SKIP_DIRS = ("title", os.path.join("sprites", "widget"), os.path.join("sprites", "hud"))
gui_root = os.path.join(VAN, "textures", "gui")
done = skipped = 0
for root, _, files in os.walk(gui_root):
    rel_dir = os.path.relpath(root, gui_root)
    if rel_dir.startswith(SKIP_DIRS):
        continue
    for f in files:
        if not f.endswith(".png"):
            continue
        src = os.path.join(root, f)
        im = Image.open(src).convert("RGBA")
        if vanilla_share(im) >= 0.5:
            recolor_container(im).save(out_path("assets", "minecraft", "textures", "gui", rel_dir, f))
            m = src + ".mcmeta"
            if os.path.exists(m):
                shutil.copy(m, out_path("assets", "minecraft", "textures", "gui", rel_dir, f + ".mcmeta"))
            done += 1
        else:
            skipped += 1
report.append(f"vanilla gui recolored: {done}, untouched: {skipped}")


# ---------- 2. виджеты-«таблетки» ----------
def pill(w, h, fill, border, open_bottom=False):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], fill=fill)
    d.line([2, 0, w - 3, 0], fill=border)                       # верх
    d.line([0, 2, 0, h - 3 if not open_bottom else h - 1], fill=border)   # лево
    d.line([w - 1, 2, w - 1, h - 3 if not open_bottom else h - 1], fill=border)  # право
    d.point([(1, 1), (w - 2, 1)], fill=border)
    if not open_bottom:
        d.line([2, h - 1, w - 3, h - 1], fill=border)            # низ
        d.point([(1, h - 2), (w - 2, h - 2)], fill=border)
    return im


W = os.path.join(VAN, "textures", "gui", "sprites", "widget")
STYLES = {
    "button": ((22, 22, 25, 205), (255, 255, 255, 46)),
    "button_highlighted": ((40, 40, 46, 225), (255, 255, 255, 150)),
    "button_disabled": ((16, 16, 18, 130), (255, 255, 255, 20)),
    "slider": ((16, 16, 18, 190), (255, 255, 255, 40)),
    "slider_highlighted": ((22, 22, 26, 205), (255, 255, 255, 90)),
    "slider_handle": ((70, 70, 78, 240), (255, 255, 255, 120)),
    "slider_handle_highlighted": ((110, 110, 120, 250), (255, 255, 255, 220)),
    "text_field": ((8, 8, 9, 235), (255, 255, 255, 46)),
    "text_field_highlighted": ((8, 8, 9, 245), (255, 255, 255, 150)),
    "tab": ((16, 16, 18, 200), (255, 255, 255, 36)),
    "tab_highlighted": ((30, 30, 34, 215), (255, 255, 255, 110)),
    "tab_selected": ((26, 26, 30, 235), (255, 255, 255, 80)),
    "tab_selected_highlighted": ((34, 34, 40, 240), (255, 255, 255, 150)),
    "scroller": ((90, 90, 100, 230), (255, 255, 255, 140)),
    "scroller_background": ((10, 10, 11, 200), (255, 255, 255, 30)),
}
for name, (fill, border) in STYLES.items():
    src = os.path.join(W, name + ".png")
    if not os.path.exists(src):
        report.append(f"widget missing in vanilla: {name}")
        continue
    w, h = Image.open(src).size
    pill(w, h, fill, border, open_bottom=name.startswith("tab_selected")).save(
        out_path("assets", "minecraft", "textures", "gui", "sprites", "widget", name + ".png"))
    if os.path.exists(src + ".mcmeta"):
        shutil.copy(src + ".mcmeta", out_path("assets", "minecraft", "textures", "gui", "sprites", "widget", name + ".png.mcmeta"))
report.append(f"widgets drawn: {len(STYLES)}")

# ---------- 3. HUD ----------
HUD = os.path.join(VAN, "textures", "gui", "sprites", "hud")
for f in ("hotbar.png", "hotbar_selection.png", "hotbar_offhand_left.png", "hotbar_offhand_right.png"):
    p = os.path.join(HUD, f)
    if os.path.exists(p):
        darken_grays(Image.open(p)).save(out_path("assets", "minecraft", "textures", "gui", "sprites", "hud", f))
report.append("hud: hotbar, selection, offhand")

# ---------- 4. фоны меню, разделители, панорама-заглушка ----------
G = ("assets", "minecraft", "textures", "gui")
for f, rgba in {"menu_background.png": (*BG_DEEP, 215), "menu_list_background.png": (14, 14, 16, 170),
                "inworld_menu_background.png": (*BG_DEEP, 165), "inworld_menu_list_background.png": (14, 14, 16, 120)}.items():
    Image.new("RGBA", (16, 16), rgba).save(out_path(*G, f))
for f, top in {"header_separator.png": True, "footer_separator.png": False,
               "inworld_header_separator.png": True, "inworld_footer_separator.png": False}.items():
    im = Image.new("RGBA", (32, 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).line([0, 0 if top else 1, 31, 0 if top else 1], fill=(255, 255, 255, 46))
    im.save(out_path(*G, f))
for i in range(6):
    Image.new("RGB", (256, 256), (14, 14, 16)).save(out_path(*G, "title", "background", f"panorama_{i}.png"))
Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(out_path(*G, "title", "background", "panorama_overlay.png"))


# ---------- 5. логотип ----------
def text_image(size, text, font_path, max_w, max_h, color, glow=True):
    w, h = size
    fs = max_h
    while fs > 8:
        font = ImageFont.truetype(font_path, fs)
        l, t, r, b = font.getbbox(text)
        if r - l <= max_w and b - t <= max_h:
            break
        fs -= 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    l, t, r, b = font.getbbox(text)
    x, y = (w - (r - l)) // 2 - l, (h - (b - t)) // 2 - t
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((x, y), text, font=font, fill=(255, 255, 255, 110))
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).text((x, y), text, font=font, fill=color)
    return im


logo = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
logo.alpha_composite(text_image((1024, 176), "Anno Mille", FONT_SEMI, 940, 120, (*TEXT, 255)), (0, 0))
for f in ("minecraft.png", "minceraft.png"):
    logo.save(out_path(*G, "title", f))
    shutil.copy(os.path.join(VAN, "textures", "gui", "title", "minecraft.png.mcmeta"), out_path(*G, "title", f + ".mcmeta"))
text_image((512, 64), "Год тысячный · Millénaire", FONT_MED, 480, 40, (255, 255, 255, 135), glow=False).save(out_path(*G, "title", "edition.png"))
shutil.copy(os.path.join(VAN, "textures", "gui", "title", "edition.png.mcmeta"), out_path(*G, "title", "edition.png.mcmeta"))
open(out_path("assets", "minecraft", "texts", "splashes.txt"), "w", encoding="utf-8").write("")
report.append("logo: Anno Mille / Год тысячный · Millénaire; splashes off")

# ---------- 6. белые заголовки окон ----------
def white_titles(lang_json):
    return {k: ("§f" + v if not v.startswith("§") else v) for k, v in lang_json.items()
            if re.match(r"^container\.", k) and isinstance(v, str)}


lang = {"ru_ru": {}, "en_us": {}}
for loc in lang:
    p = os.path.join(VAN, "lang", f"{loc}.json")
    lang[loc].update(white_titles(json.load(open(p, encoding="utf-8"))))

# ---------- 7. окна модов ----------
mods_dir = os.path.join(GAME, "mods")
mod_done, mod_ns = 0, {}
for jar in sorted(os.listdir(mods_dir)):
    if not jar.endswith(".jar"):
        continue
    try:
        z = zipfile.ZipFile(os.path.join(mods_dir, jar))
    except zipfile.BadZipFile:
        continue
    for n in z.namelist():
        m = re.match(r"assets/([^/]+)/textures/gui/(.+\.png)$", n)
        if m and m.group(1) != "minecraft":
            try:
                im = Image.open(io.BytesIO(z.read(n))).convert("RGBA")
            except Exception:
                continue
            if im.width * im.height <= 4096 * 4096 and vanilla_share(im) >= 0.6:
                recolor_container(im).save(out_path("assets", m.group(1), "textures", "gui", m.group(2)))
                if n + ".mcmeta" in z.namelist():
                    open(out_path("assets", m.group(1), "textures", "gui", m.group(2) + ".mcmeta"), "wb").write(z.read(n + ".mcmeta"))
                mod_done += 1
                mod_ns[m.group(1)] = mod_ns.get(m.group(1), 0) + 1
        lm = re.match(r"assets/([^/]+)/lang/(ru_ru|en_us)\.json$", n)
        if lm and lm.group(1) != "minecraft":
            try:
                data = json.loads(z.read(n).decode("utf-8-sig"))
            except Exception:
                continue
            lang.setdefault((lm.group(1), lm.group(2)), {}).update(white_titles(data))
report.append(f"mod gui recolored: {mod_done} in {len(mod_ns)} mods: " + ", ".join(f"{k}({v})" for k, v in sorted(mod_ns.items())))

for key, entries in lang.items():
    if not entries:
        continue
    ns, loc = ("minecraft", key) if isinstance(key, str) else key
    json.dump(entries, open(out_path("assets", ns, "lang", f"{loc}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
report.append("white titles: " + ", ".join(f"{k if isinstance(k, str) else k[0] + '/' + k[1]}={len(v)}" for k, v in lang.items() if v))

# ---------- 8. pack.mcmeta + иконка ----------
json.dump({"pack": {"pack_format": 34, "description": "§fAnno Mille §7— интерфейс"}},
          open(out_path("pack.mcmeta"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
icon = Image.new("RGBA", (128, 128), (*BG, 255))
icon.alpha_composite(text_image((128, 128), "1000", FONT_SEMI, 110, 60, (*TEXT, 255)))
icon.save(out_path("pack.png"))

open(os.path.join(HERE, "out", "report.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")
print("\n".join(report))
