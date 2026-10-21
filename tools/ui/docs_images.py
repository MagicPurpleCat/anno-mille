"""Картинки для README: баннер, главное меню, окна, деревья навыков, карта квестов.

    python tools/ui/docs_images.py <ui-pack dir с out/ и vanilla/> <skills data dir> <quests dir> <docs/img>
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
UI, SKILLS, QUESTS, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(UI, "src", "Inter-SemiBold.ttf")
FONT_M = os.path.join(UI, "src", "Inter-Medium.ttf")
F = lambda s, m=False: ImageFont.truetype(FONT_M if m else FONT, s)
BG, TEXT, MUTED, LINE = (14, 14, 16), (244, 244, 245), (150, 150, 158), (60, 60, 68)
PACK = os.path.join(UI, "out", "MillenaireUI", "assets")
bgframe = Image.open(os.path.join(UI, "out", "bg_preview.png")).convert("RGB")


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def center_text(d, xy, text, font, fill, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, anchor=anchor)


def glow_text(img, xy, text, font, fill=TEXT, blur=14):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text(xy, text, font=font, fill=(255, 255, 255, 90), anchor="mm")
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor="mm")


# 1. Баннер
W, H = 1600, 520
b = cover(bgframe, W, H).convert("RGBA")
lg = Image.open(os.path.join(PACK, "minecraft/textures/gui/title/minecraft.png")).convert("RGBA").crop((0, 0, 1024, 176))
lg = lg.resize((1100, 189), Image.LANCZOS)
b.alpha_composite(lg, ((W - 1100) // 2, 110))
d = ImageDraw.Draw(b)
center_text(d, (W // 2, 318), "Год тысячный · сборка вокруг Millénaire", F(36, True), (210, 210, 216))
center_text(d, (W // 2, 372), "Minecraft 1.21.1  ·  NeoForge  ·  185 модов  ·  145 квестов  ·  4 дерева навыков", F(24, True), MUTED)
b.convert("RGB").save(os.path.join(OUT, "banner.png"))

# 2. Главное меню (макет 16:9)
W, H = 1280, 720
m = cover(bgframe, W, H).convert("RGBA")
logo = Image.open(os.path.join(PACK, "minecraft/textures/gui/title/minecraft.png")).convert("RGBA").resize((768, 192), Image.LANCZOS)
ed = Image.open(os.path.join(PACK, "minecraft/textures/gui/title/edition.png")).convert("RGBA").resize((256, 32), Image.LANCZOS)
m.alpha_composite(logo, ((W - 768) // 2, 70)); m.alpha_composite(ed, ((W - 256) // 2, 205))
btn = {s: Image.open(os.path.join(PACK, f"minecraft/textures/gui/sprites/widget/{s}.png")).convert("RGBA")
       for s in ("button", "button_highlighted")}
d = ImageDraw.Draw(m)
labels = [("Одиночная игра", "button"), ("Сетевая игра", "button_highlighted"), ("Моды", "button")]
for i, (t, s) in enumerate(labels):
    m.alpha_composite(btn[s].resize((600, 60), Image.NEAREST), ((W - 600) // 2, 300 + i * 76))
    center_text(d, (W // 2, 330 + i * 76), t, F(24, True), TEXT)
for j, t in enumerate(["Настройки", "Выйти"]):
    x = (W - 600) // 2 + j * 310
    m.alpha_composite(btn["button"].resize((290, 60), Image.NEAREST), (x, 300 + 3 * 76))
    center_text(d, (x + 145, 330 + 3 * 76), t, F(24, True), TEXT)
m.convert("RGB").save(os.path.join(OUT, "menu.png"))

# 3. Окна: было / стало
VAN = os.path.join(UI, "vanilla", "assets", "minecraft", "textures", "gui", "container")
W, H = 1600, 640
w = Image.new("RGBA", (W, H), (*BG, 255))
d = ImageDraw.Draw(w)
center_text(d, (W // 2, 40), "Окна игры: было → стало", F(30), TEXT)
for i, (name, crop, title) in enumerate([("inventory", (0, 0, 176, 166), "Инвентарь"), ("generic_54", (0, 0, 176, 166), "Сундук"),
                                          ("furnace", (0, 0, 176, 166), "Печь")]):
    a = Image.open(os.path.join(VAN, f"{name}.png")).convert("RGBA").crop(crop).resize((352, 332), Image.NEAREST)
    n = Image.open(os.path.join(PACK, f"minecraft/textures/gui/container/{name}.png")).convert("RGBA").crop(crop).resize((352, 332), Image.NEAREST)
    x = 40 + i * 520
    w.alpha_composite(a, (x, 110)); w.alpha_composite(n, (x + 120, 230))
    ImageDraw.Draw(w).text((x + 136, 240), title, font=F(18, True), fill=TEXT)
    center_text(d, (x + 236, 600), title, F(22, True), MUTED)
w.convert("RGB").save(os.path.join(OUT, "windows.png"))

# 4. Деревья навыков
COLORS = [(214, 92, 76), (94, 168, 222), (122, 196, 110)]
GOLD = (240, 196, 96)
cats = json.load(open(os.path.join(SKILLS, "puffish_skills", "puffish_skills", "config.json"), encoding="utf-8"))["categories"]
TW, TH = 760, 640
sheet = Image.new("RGBA", (TW * 2 + 60, TH * 2 + 140), (*BG, 255))
sd = ImageDraw.Draw(sheet)
center_text(sd, (sheet.width // 2, 50), "Деревья навыков  ·  клавиша P", F(34), TEXT)
for ci, cat in enumerate(cats):
    base = os.path.join(SKILLS, "puffish_skills", "puffish_skills", "categories", cat)
    cj = json.load(open(os.path.join(base, "category.json"), encoding="utf-8"))
    sk = json.load(open(os.path.join(base, "skills.json"), encoding="utf-8"))
    df = json.load(open(os.path.join(base, "definitions.json"), encoding="utf-8"))
    cn = json.load(open(os.path.join(base, "connections.json"), encoding="utf-8"))
    xp = json.load(open(os.path.join(base, "experience.json"), encoding="utf-8"))
    ox, oy = 20 + (ci % 2) * (TW + 20), 100 + (ci // 2) * (TH + 20)
    panel = Image.new("RGBA", (TW, TH), (20, 20, 23, 255))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([0, 0, TW - 1, TH - 1], 16, outline=LINE, width=2)
    pd.text((24, 18), cj["title"], font=F(30), fill=TEXT)
    pd.text((24, 58), cj["description"], font=F(16, True), fill=MUTED)
    cx, cy, k = TW // 2, TH // 2 + 40, 0.42
    pos = {sid: (cx + s["x"] * k, cy + s["y"] * k) for sid, s in sk.items()}
    for a_, b_ in cn["normal"]["bidirectional"]:
        pd.line([pos[a_], pos[b_]], fill=(80, 80, 90), width=3)
    for sid, (x, y) in pos.items():
        did = sk[sid]["definition"]
        if sid == "root":
            r, col = 13, TEXT
        elif did.startswith("cap"):
            r, col = 14, GOLD
        else:
            r, col = (9 if df[did].get("frame") else 7), COLORS[int(sid[1])]
        pd.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(10, 10, 12), width=2)
        if did.startswith("cap"):
            t = df[did]["title"]
            tx = max(70, min(TW - 70, x))
            pd.text((tx, y + (24 if y > cy else -24)), t, font=F(18), fill=GOLD, anchor="mm")
    branch_names = [df[sk[f"b{b}_0"]["definition"]]["title"].split(":")[0] for b in range(3)]
    for bi, name in enumerate(branch_names):
        pd.ellipse([24, TH - 92 + bi * 26, 38, TH - 78 + bi * 26], fill=COLORS[bi])
        pd.text((46, TH - 93 + bi * 26), name, font=F(16, True), fill=(210, 210, 216))
    pd.ellipse([TW - 300, TH - 92, TW - 286, TH - 78], fill=GOLD)
    pd.text((TW - 278, TH - 93), "мастерство, одно на выбор", font=F(16, True), fill=(210, 210, 216))
    pd.text((TW - 300, TH - 67), f"{len(sk)} навыков · {xp['level_limit']} уровней", font=F(16, True), fill=MUTED)
    sheet.alpha_composite(panel, (ox, oy))
sheet.convert("RGB").save(os.path.join(OUT, "skills.png"))

# 5. Карта квестов
lang = {}
for line in open(os.path.join(QUESTS, "lang", "ru_ru.snbt"), encoding="utf-8"):
    line = line.strip()
    if ": " in line and not line.startswith("{"):
        k, v = line.split(": ", 1)
        lang[k] = v
chapters = []
for f in sorted(os.listdir(os.path.join(QUESTS, "chapters"))):
    txt = open(os.path.join(QUESTS, "chapters", f), encoding="utf-8").read()
    cid = txt.split('\tid: "')[1].split('"')[0]
    order = int(txt.split("order_index: ")[1].split("\n")[0])
    count = txt.count('\t\t\tid: "')
    title = json.loads(lang.get(f"chapter.{cid}.title", '"?"'))
    sub = json.loads(lang.get(f"chapter.{cid}.chapter_subtitle", '[""]'))[0]
    chapters.append((order, title, sub, count))
chapters.sort()
W = 1600
H = 150 + 74 * len(chapters)
q = Image.new("RGBA", (W, H), (*BG, 255))
qd = ImageDraw.Draw(q)
center_text(qd, (W // 2, 50), "Книга квестов  ·  клавиша Ё", F(34), TEXT)
center_text(qd, (W // 2, 92), "Главная линия ведёт через всю сборку, остальные главы открываются по пути", F(20, True), MUTED)
for i, (_, title, sub, count) in enumerate(chapters):
    y = 130 + i * 74
    main = i == 0
    qd.rounded_rectangle([60, y, W - 60, y + 60], 12, fill=(28, 28, 32) if main else (22, 22, 25), outline=GOLD if main else LINE, width=2)
    qd.text((90, y + 30), title, font=F(24), fill=GOLD if main else TEXT, anchor="lm")
    qd.text((470, y + 30), sub, font=F(18, True), fill=(200, 200, 206), anchor="lm")
    qd.text((W - 90, y + 30), f"{count} квестов", font=F(18, True), fill=MUTED, anchor="rm")
q.convert("RGB").save(os.path.join(OUT, "quests.png"))
print("ok:", sorted(os.listdir(OUT)))
