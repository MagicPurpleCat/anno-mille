"""Установщик Anno Mille (логика). Окно программы — tools/installer_gui.py, оно же собирается в AnnoMille-Setup.exe.

Из командной строки:  python tools/install.py "<папка игры>"

<папка игры> — та, где у профиля лежат (или появятся) mods/, config/, resourcepacks/.
Minecraft 1.21.1 + NeoForge 21.1.264 ставит сам лаунчер.

Что делает:
 1. Скачивает моды, ресурспаки и шейдеры из tools/manifest.txt с Modrinth (с проверкой SHA-512),
    файлы с CurseForge и Millénaire с официального сайта. Уже скачанные файлы с верным хешем пропускает,
    поэтому установщик можно запускать повторно и после импорта .mrpack.
 2. Копирует настройки, квесты, ресурспак интерфейса и мини-мод сборки; переносит в options.txt клавиши и порядок паков.
 3. Перекрашивает окна модов в тёмный стиль интерфейса.
"""
import concurrent.futures as cf, hashlib, io, json, os, re, shutil, sys, urllib.parse, urllib.request, zipfile

API = "https://api.modrinth.com/v2"
UA = {"User-Agent": "anno-mille-installer/1.1"}
DIRS = {"mod": "mods", "rp": "resourcepacks", "shader": "shaderpacks"}
CF = "https://www.curseforge.com/api/v1/mods/{}/files/{}/download"
EXTRA = [  # не с Modrinth: (папка, имя файла, URL)
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
MAP = {(198, 198, 198): (30, 30, 34), (255, 255, 255): (58, 58, 66), (85, 85, 85): (14, 14, 16),
       (0, 0, 0): (6, 6, 7), (139, 139, 139): (12, 12, 14), (55, 55, 55): (4, 4, 5)}
OUTLINE, PANEL = (92, 92, 104), {(198, 198, 198), (139, 139, 139)}


def data_root():
    """Папка с pack/ и tools/manifest.txt: рядом со скриптом или внутри собранного exe."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def _resolve(kind, slug, want):
    q = urllib.parse.quote
    url = f"{API}/project/{slug}/version?game_versions={q(json.dumps(['1.21.1']))}"
    if kind == "mod":
        url += f"&loaders={q(json.dumps(['neoforge']))}"
    vs = _get_json(url)
    v = next((x for x in vs if x["version_type"] == "release"), vs[0] if vs else None) if want == "*" else \
        next((x for x in vs if x["version_number"] == want), None)
    if not v:
        return None
    f = next((x for x in v["files"] if x["primary"]), v["files"][0])
    return DIRS[kind], f["filename"], f["url"], f["hashes"]["sha512"]


def _download(game, item):
    sub, name, url, sha = item
    dest = os.path.join(game, sub, name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and (sha is None or hashlib.sha512(open(dest, "rb").read()).hexdigest() == sha):
        return False, name
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read()
    if sha and hashlib.sha512(data).hexdigest() != sha:
        raise RuntimeError(f"файл повреждён при скачивании: {name}")
    if os.path.exists(dest):
        _make_writable(dest)
        os.remove(dest)
    open(dest, "wb").write(data)
    return True, name


def _is_window(im):
    if max(im.size) < 32:
        return False
    px = list(im.getdata())
    px = [p for p in px if p[3] > 0]
    if not px or sum(1 for p in px if p[3] == 255 and p[:3] in PANEL) / len(px) < 0.3:
        return False
    return sum(1 for p in px if p[3] == 255 and p[:3] in MAP) / len(px) >= 0.6


def _recolor(im):
    w, h = im.size
    src, out = im.load(), im.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 255 and (r, g, b) in MAP:
                edge = (r, g, b) == (0, 0, 0) and any(
                    not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] == 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                dst[x, y] = (*(OUTLINE if edge else MAP[(r, g, b)]), 255)
    return out


def _make_writable(path):
    """Снимает «только чтение» и «скрытый»: Windows не даёт перезаписывать скрытые файлы обычным способом."""
    try:
        os.chmod(path, 0o666)
    except OSError:
        pass
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x80)  # FILE_ATTRIBUTE_NORMAL


def safe_copytree(src, dst):
    """Копирует папку поверх существующей. Занятые файлы пропускает и возвращает их список."""
    skipped = []
    for r, _, files in os.walk(src):
        target_dir = os.path.join(dst, os.path.relpath(r, src))
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            s, d = os.path.join(r, f), os.path.join(target_dir, f)
            try:
                if os.path.exists(d):
                    _make_writable(d)
                    os.remove(d)
                shutil.copy2(s, d)
            except OSError:
                skipped.append(d)
    return skipped


def remove_duplicates(game, log):
    """Если в mods лежит старая версия того же файла из списка (например, после обновления) — убирает её в _old/."""
    mods = os.path.join(game, "mods")
    if not os.path.isdir(mods):
        return
    keep = {l.strip() for l in open(os.path.join(data_root(), "tools", "expected_mods.txt"), encoding="utf-8")}
    stem = lambda f: re.split(r"[-_+](?:v?\d|mc\d|neoforge-\d|1\.21)", f.lower(), maxsplit=1)[0]
    stems = {stem(f) for f in keep}
    for f in os.listdir(mods):
        if f.endswith(".jar") and f not in keep and stem(f) in stems:
            os.makedirs(os.path.join(game, "_old"), exist_ok=True)
            shutil.move(os.path.join(mods, f), os.path.join(game, "_old", f))
            log(f"Старая версия убрана в _old: {f}")


def run(game, log=print, progress=lambda done, total: None):
    root = data_root()
    os.makedirs(game, exist_ok=True)

    log("Ищу файлы модов...")
    entries = [tuple(l.split()[:3]) for l in open(os.path.join(root, "tools", "manifest.txt"), encoding="utf-8")
               if l.strip() and not l.startswith("#")]
    with cf.ThreadPoolExecutor(8) as ex:
        resolved = list(ex.map(lambda e: _resolve(*e), entries))
    missing = [e[1] for e, r in zip(entries, resolved) if r is None]
    if missing:
        raise RuntimeError("не нашлись на Modrinth: " + ", ".join(missing))
    items = resolved + [(s, n, u, None) for s, n, u in EXTRA]

    log(f"Скачиваю {len(items)} файлов (уже скачанные пропускаю)...")
    done = new = 0
    with cf.ThreadPoolExecutor(6) as ex:
        for fresh, name in ex.map(lambda it: _download(game, it), items):
            done += 1
            new += fresh
            progress(done, len(items))
    log(f"Готово: новых файлов {new}, уже было {len(items) - new}.")
    remove_duplicates(game, log)

    log("Копирую настройки, квесты, интерфейс и навыки...")
    skipped = []
    for sub in ("config", "resourcepacks", "mods"):
        skipped += safe_copytree(os.path.join(root, "pack", sub), os.path.join(game, sub))
    if skipped:
        log(f"Не удалось обновить файлов: {len(skipped)} (заняты другой программой):")
        for p in skipped[:10]:
            log("  " + os.path.relpath(p, game))
        log("Закрой игру и лаунчер и запусти установщик ещё раз, если что-то работает не так.")
    opt, ref_path = os.path.join(game, "options.txt"), os.path.join(root, "pack", "options.txt")
    if not os.path.exists(opt):
        shutil.copy(ref_path, opt)
    else:
        ref = dict(l.split(":", 1) for l in open(ref_path, encoding="utf-8").read().splitlines() if ":" in l)
        lines = open(opt, encoding="utf-8").read().splitlines()
        idx = {l.split(":", 1)[0]: i for i, l in enumerate(lines) if ":" in l}
        for k in [k for k in ref if k.startswith("key_") or k in ("lang", "resourcePacks")]:
            if k in idx:
                lines[idx[k]] = f"{k}:{ref[k]}"
            else:
                lines.append(f"{k}:{ref[k]}")
        _make_writable(opt)
        open(opt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    log("Клавиши и порядок ресурспаков применены.")

    log("Перекрашиваю окна модов в тёмный стиль...")
    from PIL import Image
    pack, n = os.path.join(game, "resourcepacks", "MillenaireUI"), 0
    for jar in sorted(os.listdir(os.path.join(game, "mods"))):
        if not jar.endswith(".jar"):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(game, "mods", jar))
        except zipfile.BadZipFile:
            continue
        names = set(z.namelist())
        for name in names:
            m = re.match(r"assets/([^/]+)/textures/gui/(.+\.png)$", name)
            if not m or m.group(1) == "minecraft":
                continue
            try:
                im = Image.open(io.BytesIO(z.read(name))).convert("RGBA")
            except Exception:
                continue
            if _is_window(im):
                dest = os.path.join(pack, "assets", m.group(1), "textures", "gui", m.group(2))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                _recolor(im).save(dest)
                if name + ".mcmeta" in names:
                    open(dest + ".mcmeta", "wb").write(z.read(name + ".mcmeta"))
                n += 1
    log(f"Перекрашено окон модов: {n}.")
    log("Всё установлено. Выдели игре 8 ГБ памяти и создай новый мир на сложности «Сложная».")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run(sys.argv[1])
