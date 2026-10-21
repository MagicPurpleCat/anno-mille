"""Установщик Anno Mille.

    python tools/install.py "<папка игры>"

<папка игры> — та, где у профиля лежат mods/, config/, resourcepacks/ (для TLauncher это %APPDATA%\\.minecraft,
для Prism — instances/<имя>/minecraft). Minecraft 1.21.1 + NeoForge 21.1.264 должны быть уже установлены лаунчером.

Что делает:
 1. Скачивает все моды, ресурспаки и шейдеры из tools/manifest.txt с Modrinth (с проверкой SHA-512),
    файлы с CurseForge и Millénaire с официального сайта millenaire.org.
 2. Копирует настройки (config), квесты, ресурспак интерфейса, мини-мод сборки и options.txt.
 3. Если установлен Pillow (pip install pillow) — перекрашивает окна модов в тёмный стиль интерфейса.
"""
import concurrent.futures as cf, hashlib, io, json, os, re, shutil, sys, urllib.parse, urllib.request, zipfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
GAME = ARGS[0] if ARGS else sys.exit(__doc__)
EXTRA_ONLY = "--extra-only" in sys.argv   # после импорта .mrpack: докачать только файлы не с Modrinth + тёмные окна модов
API = "https://api.modrinth.com/v2"
UA = {"User-Agent": "anno-mille-installer/1.0"}
DIRS = {"mod": "mods", "rp": "resourcepacks", "shader": "shaderpacks"}

# Не с Modrinth: (папка, имя файла, URL)
CF = "https://www.curseforge.com/api/v1/mods/{}/files/{}/download"
EXTRA = [
    ("mods", "millenaire-9.0.2.jar", "https://www.millenaire.org/api/downloads/9.0.2~millenaire-9.0.2.jar"),
    ("resourcepacks", "millenaire-hd-9.0.zip", "https://www.millenaire.org/api/downloads/hd-1.21~millenaire-hd-9.0.zip"),
    ("mods", "ftb-chunks-neoforge-2101.1.22.jar", CF.format(314906, 8791113)),
    ("mods", "ftb-library-neoforge-2101.1.37.jar", CF.format(404465, 9008089)),
    ("mods", "ftb-teams-neoforge-2101.1.11.jar", CF.format(404468, 8724782)),
    ("mods", "ftb-quests-neoforge-2101.1.36.jar", CF.format(289412, 8885017)),
    ("mods", "ftb-xmod-compat-neoforge-21.1.12.jar", CF.format(889915, 8909889)),
    ("mods", "swem-1.21.1-1.6.14.jar", CF.format(582697, 9156395)),
    ("resourcepacks", "Excalibur_V1.21.1.zip", CF.format(228815, 5710779)),
]


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def resolve(kind, slug, want):
    q = urllib.parse.quote
    url = f"{API}/project/{slug}/version?game_versions={q(json.dumps(['1.21.1']))}"
    if kind == "mod":
        url += f"&loaders={q(json.dumps(['neoforge']))}"
    vs = get_json(url)
    v = next((x for x in vs if x["version_type"] == "release"), vs[0] if vs else None) if want == "*" else \
        next((x for x in vs if x["version_number"] == want), None)
    if not v:
        return None
    f = next((x for x in v["files"] if x["primary"]), v["files"][0])
    return DIRS[kind], f["filename"], f["url"], f["hashes"]["sha512"]


def download(item):
    sub, name, url, sha = item
    dest = os.path.join(GAME, sub, name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and (sha is None or hashlib.sha512(open(dest, "rb").read()).hexdigest() == sha):
        return f"  есть   {name}"
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read()
    if sha and hashlib.sha512(data).hexdigest() != sha:
        return f"  !! хеш не совпал: {name}"
    open(dest, "wb").write(data)
    return f"  скачан {name}"


print("1/3  Моды и паки")
entries = [] if EXTRA_ONLY else [tuple(l.split()[:3]) for l in open(os.path.join(ROOT, "tools", "manifest.txt"), encoding="utf-8")
                                 if l.strip() and not l.startswith("#")]
with cf.ThreadPoolExecutor(8) as ex:
    resolved = list(ex.map(lambda e: resolve(*e), entries))
missing = [e[1] for e, r in zip(entries, resolved) if r is None]
items = [r for r in resolved if r] + [(s, n, u, None) for s, n, u in EXTRA]
with cf.ThreadPoolExecutor(6) as ex:
    for line in ex.map(download, items):
        print(line)
if missing:
    print("  !! не найдены на Modrinth:", ", ".join(missing))

print("2/3  Настройки, квесты, ресурспак, мини-мод")
for sub in (() if EXTRA_ONLY else ("config", "resourcepacks", "mods")):
    shutil.copytree(os.path.join(ROOT, "pack", sub), os.path.join(GAME, sub), dirs_exist_ok=True)
opt = os.path.join(GAME, "options.txt")
ref = dict(l.split(":", 1) for l in open(os.path.join(ROOT, "pack", "options.txt"), encoding="utf-8").read().splitlines() if ":" in l)
if not os.path.exists(opt):
    shutil.copy(os.path.join(ROOT, "pack", "options.txt"), opt)
    print("  options.txt установлен")
elif not EXTRA_ONLY:
    # переносим только клавиши, язык и список ресурспаков — остальные настройки игрока не трогаем
    lines = open(opt, encoding="utf-8").read().splitlines()
    idx = {l.split(":", 1)[0]: i for i, l in enumerate(lines) if ":" in l}
    keys = [k for k in ref if k.startswith("key_") or k in ("lang", "resourcePacks")]
    for k in keys:
        if k in idx:
            lines[idx[k]] = f"{k}:{ref[k]}"
        else:
            lines.append(f"{k}:{ref[k]}")
    open(opt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"  options.txt: обновлено {len(keys)} строк (клавиши, язык, порядок паков)")

print("3/3  Тёмные окна модов")
try:
    from PIL import Image
except ImportError:
    print("  Pillow не установлен — пропуск (pip install pillow и запусти установщик ещё раз)")
    sys.exit(0)
MAP = {(198, 198, 198): (30, 30, 34), (255, 255, 255): (58, 58, 66), (85, 85, 85): (14, 14, 16),
       (0, 0, 0): (6, 6, 7), (139, 139, 139): (12, 12, 14), (55, 55, 55): (4, 4, 5)}
OUTLINE, PANEL = (92, 92, 104), {(198, 198, 198), (139, 139, 139)}


def is_window(im):
    if max(im.size) < 32:
        return False
    px = [p for p in im.getdata() if p[3] > 0]
    if not px or sum(1 for p in px if p[3] == 255 and p[:3] in PANEL) / len(px) < 0.3:
        return False
    return sum(1 for p in px if p[3] == 255 and p[:3] in MAP) / len(px) >= 0.6


def recolor(im):
    w, h = im.size
    src, out = im.load(), im.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 255 and (r, g, b) in MAP:
                if (r, g, b) == (0, 0, 0) and any(not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] == 0
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    dst[x, y] = (*OUTLINE, 255)
                else:
                    dst[x, y] = (*MAP[(r, g, b)], 255)
    return out


pack = os.path.join(GAME, "resourcepacks", "MillenaireUI")
n = 0
for jar in sorted(os.listdir(os.path.join(GAME, "mods"))):
    if not jar.endswith(".jar"):
        continue
    try:
        z = zipfile.ZipFile(os.path.join(GAME, "mods", jar))
    except zipfile.BadZipFile:
        continue
    for name in z.namelist():
        m = re.match(r"assets/([^/]+)/textures/gui/(.+\.png)$", name)
        if not m or m.group(1) == "minecraft":
            continue
        try:
            im = Image.open(io.BytesIO(z.read(name))).convert("RGBA")
        except Exception:
            continue
        if is_window(im):
            dest = os.path.join(pack, "assets", m.group(1), "textures", "gui", m.group(2))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            recolor(im).save(dest)
            if name + ".mcmeta" in z.namelist():
                open(dest + ".mcmeta", "wb").write(z.read(name + ".mcmeta"))
            n += 1
print(f"  перекрашено окон модов: {n}")
print("\nГотово. В лаунчере выдели 8 ГБ памяти и запускай. Новый мир — сложность «Сложная».")
