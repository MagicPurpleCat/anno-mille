"""Контактный лист для проверки пака: out/preview.png"""
import io, os, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = sys.argv[1]
PACK = os.path.join(HERE, "out", "MillenaireUI", "assets")
VAN = os.path.join(HERE, "vanilla", "assets")
F = ImageFont.truetype(os.path.join(HERE, "src", "Inter-Medium.ttf"), 18)
FS = ImageFont.truetype(os.path.join(HERE, "src", "Inter-Medium.ttf"), 13)
sheet = Image.new("RGB", (1940, 1640), (40, 40, 44))
d = ImageDraw.Draw(sheet)


def label(x, y, t): d.text((x, y), t, font=F, fill=(230, 230, 230))


def up(im, k): return im.resize((im.width * k, im.height * k), Image.NEAREST)


# 1. референс vs наш фон
ref = Image.open(os.path.join(HERE, "out", "ref_frame.png")).convert("RGB").resize((640, 360))
bg = Image.open(os.path.join(HERE, "out", "bg_preview.png")).convert("RGB").resize((640, 360))
label(20, 10, "Кадр из ролика"); sheet.paste(ref, (20, 36))
label(680, 10, "Наш фон (тот же кадр петли не обязателен)"); sheet.paste(bg, (680, 36))

# 2. макет главного меню
menu = Image.open(os.path.join(HERE, "out", "bg_preview.png")).convert("RGBA").resize((640, 360))
logo = Image.open(os.path.join(PACK, "minecraft/textures/gui/title/minecraft.png")).resize((384, 96))
ed = Image.open(os.path.join(PACK, "minecraft/textures/gui/title/edition.png")).resize((128, 16))
menu.alpha_composite(logo, (128, 30)); menu.alpha_composite(ed, (256, 92))
btn = {s: Image.open(os.path.join(PACK, f"minecraft/textures/gui/sprites/widget/{s}.png")).convert("RGBA")
       for s in ("button", "button_highlighted", "button_disabled")}
md = ImageDraw.Draw(menu)
for i, (s, t) in enumerate([("button", "Одиночная игра"), ("button_highlighted", "Сетевая игра (наведение)"),
                            ("button", "Моды"), ("button_disabled", "Недоступно")]):
    b = btn[s].resize((400, 40), Image.NEAREST)
    menu.alpha_composite(b, (120, 140 + i * 50))
    md.text((320, 160 + i * 50), t, font=FS, fill=(244, 244, 245) if s != "button_disabled" else (120, 120, 120), anchor="mm")
label(1340, 10, "Главное меню (макет)"); sheet.paste(menu.convert("RGB"), (1300, 36))

# 3. окна: было / стало
y0 = 420
for i, (name, crop) in enumerate([("inventory", (0, 0, 176, 166)), ("generic_54", (0, 0, 176, 222)), ("furnace", (0, 0, 176, 166))]):
    a = Image.open(os.path.join(VAN, f"minecraft/textures/gui/container/{name}.png")).convert("RGBA").crop(crop)
    b = Image.open(os.path.join(PACK, f"minecraft/textures/gui/container/{name}.png")).convert("RGBA").crop(crop)
    x = 20 + i * 640
    label(x, y0, f"{name}: было → стало")
    sheet.paste(up(a, 2), (x, y0 + 26), up(a, 2)); sheet.paste(up(b, 2), (x + 360, y0 + 26), up(b, 2))
    if i < 2:
        title = "Инвентарь" if name == "inventory" else "Сундук"
        d.text((x + 360 + 16, y0 + 26 + 12), title, font=FS, fill=(244, 244, 245))

# 4. текстуры модов (под подозрением + котёл)
y1 = 920
picks = ["farmersdelight/textures/gui/cooking_pot.png", "appleskin/textures/gui/icons.png",
         "shouldersurfing/textures/gui/crosshair.png", "jade/textures/gui/sprites/", "jei/textures/gui/", "fzzy_config/textures/gui/",
         "travelersbackpack/textures/gui/", "millenaire/textures/gui/"]
shown = 0
for jar in sorted(os.listdir(os.path.join(GAME, "mods"))):
    if not jar.endswith(".jar") or shown >= 12:
        continue
    z = zipfile.ZipFile(os.path.join(GAME, "mods", jar))
    for n in z.namelist():
        if shown >= 12:
            break
        rel = n.replace("assets/", "", 1)
        if not n.endswith(".png") or not os.path.exists(os.path.join(PACK, rel)):
            continue
        if not any(rel.startswith(p) for p in picks):
            continue
        a = Image.open(io.BytesIO(z.read(n))).convert("RGBA")
        b = Image.open(os.path.join(PACK, rel)).convert("RGBA")
        k = max(1, min(3, 200 // max(a.width, a.height, 1)))
        a, b = up(a, k).crop((0, 0, 300, 230)), up(b, k).crop((0, 0, 300, 230))
        col, row = shown % 3, shown // 3
        x, y = 20 + col * 640, y1 + row * 180
        d.text((x, y), rel[:70], font=FS, fill=(220, 220, 220))
        sheet.paste(a, (x, y + 18), a); sheet.paste(b, (x + 310, y + 18), b)
        picks = [p for p in picks if not rel.startswith(p)] + ([p for p in picks if rel.startswith(p)] if False else [])
        shown += 1
sheet.save(os.path.join(HERE, "out", "preview.png"))
print("ok")
