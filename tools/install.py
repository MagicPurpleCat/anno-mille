"""Установщик Anno Mille (логика). Окно программы — tools/installer_gui.py, оно же собирается в AnnoMille-Setup.exe.

Из командной строки:  python tools/install.py "<папка игры>"

<папка игры> — та, где у профиля лежат (или появятся) mods/, config/, resourcepacks/.
Minecraft 1.21.1 + NeoForge 21.1.264 ставит лаунчер, либо install_neoforge() в папку .minecraft
(для TLauncher и официального лаунчера; Java 21 берётся из лаунчера или скачивается).

Что делает:
 1. Скачивает моды, ресурспаки и шейдеры из tools/manifest.txt с Modrinth (с проверкой SHA-512),
    файлы с CurseForge и Millénaire с официального сайта. Уже скачанные файлы с верным хешем пропускает,
    поэтому установщик можно запускать повторно и после импорта .mrpack.
 2. Копирует настройки, квесты, ресурспак интерфейса и мини-мод сборки; переносит в options.txt клавиши и порядок паков.
 3. Перекрашивает окна модов в тёмный стиль интерфейса.
"""
import concurrent.futures as cf, glob, hashlib, io, json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request, zipfile

API = "https://api.modrinth.com/v2"
UA = {"User-Agent": "anno-mille-installer/1.2"}
DIRS = {"mod": "mods", "rp": "resourcepacks", "shader": "shaderpacks"}
CF = "https://www.curseforge.com/api/v1/mods/{}/files/{}/download"
EXTRA = [  # не с Modrinth: (папка, имя файла, URL)
    ("mods", "millenaire-9.0.3.jar", "https://www.millenaire.org/api/downloads/9.0.3~millenaire-9.0.3.jar"),
    ("resourcepacks", "millenaire-hd-9.0.zip", "https://www.millenaire.org/api/downloads/hd-1.21~millenaire-hd-9.0.zip"),
    ("mods", "ftb-chunks-neoforge-2101.1.22.jar", CF.format(314906, 8791113)),
    ("mods", "ftb-library-neoforge-2101.1.37.jar", CF.format(404465, 9008089)),
    ("mods", "ftb-teams-neoforge-2101.1.11.jar", CF.format(404468, 8724782)),
    ("mods", "ftb-quests-neoforge-2101.1.36.jar", CF.format(289412, 8885017)),
    ("mods", "ftb-xmod-compat-neoforge-21.1.12.jar", CF.format(889915, 8909889)),
    ("mods", "swem-1.21.1-1.6.14.jar", CF.format(582697, 9156395)),
    ("mods", "CinematicInteraction-NeoForge-1.21.1-0.18.2.jar", CF.format(1743441, 9220261)),
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


FTB_THEME = {  # тёмная тема окна квестов: правки поверх темы из самого мода
    "background": "ftblibrary:textures/gui/background_squares.png; color=#F02A2A30; tile_size=64",
    "chapter_panel_background": "hollow_rectangle:{{widget_border}}; round_edges + #F0141416; padding=1",
    "key_reference_background": "ftblibrary:textures/gui/background_squares.png; color=#F02A2A30; tile_size=64",
    "context_menu": "hollow_rectangle:{{widget_border}}; round_edges + #F0141416; padding=1",
    "selected_chapter_highlight_1": "#50E8C26A",
    "selected_chapter_highlight_2": "#20E8C26A",
    "hover_text_color": "#E8C26A",
    "disabled_text_color": "#8A8A92",
    "widget_border": "#5C5C68",
    "widget_background": "#30FFFFFF",
    "quest_view_title": "#E8C26A",
    "tasks_text_color": "#9DB4FF",
    "rewards_text_color": "#E8C26A",
}


def _ftb_theme(game, pack):
    jar = next((os.path.join(game, "mods", f) for f in os.listdir(os.path.join(game, "mods"))
                if f.startswith("ftb-quests-") and f.endswith(".jar")), None)
    if not jar:
        return
    try:
        src = zipfile.ZipFile(jar).read("assets/ftbquests/ftb_quests_theme.txt").decode("utf-8")
    except (KeyError, zipfile.BadZipFile):
        return
    out = []
    for line in src.splitlines():
        m = re.match(r"^(\w+):(\s*)(.*)$", line)
        out.append(f"{m.group(1)}:{m.group(2)}{FTB_THEME[m.group(1)]}" if m and m.group(1) in FTB_THEME else line)
    dest = os.path.join(pack, "assets", "ftbquests", "ftb_quests_theme.txt")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


def _fix_animations(game, pack):
    """Некоторые моды (Born in Chaos) кладут в анимации GeckoLib пустое выражение «-», и анимация не грузится.
    Пишем в пак исправленную копию с «0» вместо «-»."""
    fixed = 0
    def walk(o):
        nonlocal changed
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, str) and o.strip() == "-":
            changed = True
            return "0"
        if isinstance(o, str) and re.search(r"\bnan\b", o):  # «nan» GeckoLib тоже не понимает
            changed = True
            return re.sub(r"\bnan\b", "0", o)
        return o
    for jar in os.listdir(os.path.join(game, "mods")):
        if not jar.endswith(".jar"):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(game, "mods", jar))
        except zipfile.BadZipFile:
            continue
        for name in z.namelist():
            if not re.match(r"assets/[^/]+/animations/.+\.json$", name):
                continue
            try:
                data = json.loads(z.read(name).decode("utf-8-sig"))
            except ValueError:
                continue
            changed = False
            data = walk(data)
            if changed:
                dest = os.path.join(pack, *name.split("/"))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                json.dump(data, open(dest, "w", encoding="utf-8"))
                fixed += 1
    return fixed


# Что оставляем от Excalibur в textures/entity и optifine/random/entity: блоки-сущности и снаряды, но не мобов.
EXCALIBUR_KEEP = {"banner", "banner_base.png", "bed", "bell", "chest", "decorated_pot", "shield", "shield_base.png",
                  "shield_base_nopattern.png", "signs", "conduit", "enchanting_table_book.png", "beacon_beam.png",
                  "end_portal.png", "end_gateway_beam.png", "boat", "chest_boat", "minecart.png", "arrow.png",
                  "trident.png", "trident_riptide.png", "projectiles", "experience_orb.png", "explosion.png",
                  "fishing_hook.png", "lead_knot.png", "elytra.png", "armorstand", "end_crystal"}
EXCALIBUR_CEM = re.compile(r"(chest|chest_large|ender_chest|trapped_chest|trapped_chest_large|enchanting_book|lectern_book)\.jem$")


def _excalibur_mob_file(name):
    m = re.match(r"assets/minecraft/(?:textures|optifine/random)/entity/([^/]+)", name)
    if m:
        return m.group(1) not in EXCALIBUR_KEEP
    m = re.match(r"assets/minecraft/optifine/cem/(.+)", name)
    return bool(m) and not EXCALIBUR_CEM.match(m.group(1))


def _fix_excalibur(game):
    """Excalibur перекрашивает мобов под свои модели, а модели мобов задаёт Fresh Animations.
    Вместе получаются мобы с текстурой не на своих местах, поэтому мобов из Excalibur убираем."""
    path = os.path.join(game, "resourcepacks", "Excalibur_V1.21.1.zip")
    if not os.path.exists(path):
        return 0
    with zipfile.ZipFile(path) as z:
        drop = [n for n in z.namelist() if _excalibur_mob_file(n) and not n.endswith("/")]
        if not drop:
            return 0
        tmp = path + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
            for info in z.infolist():
                if not _excalibur_mob_file(info.filename):
                    out.writestr(info, z.read(info))
    _make_writable(path)
    os.replace(tmp, path)
    return len(drop)


# Mixin-ы, которые ломают игру вместе с другими модами сборки: (jar, конфиг mixin, что убрать, почему)
MIXIN_FIXES = [
    # Cinematic Interactions и Amendments оба добавляют варочной стойке getUpdatePacket — падение при запуске.
    # Синхронизацию стойки даёт Amendments, сцена варки отключена в config/cinematic-client.toml. Лицензия MIT.
    ("CinematicInteraction*.jar", "cinematic.mixins.json", "BrewingStandBlockEntityMixin",
     "Cinematic Interactions: убран конфликт с Amendments у варочной стойки."),
    # Thirst Was Taken 2.1.5 встраивается в подсказку Jade о жидкостях, а в Jade 15.10 этот код изменился:
    # игра падает, когда смотришь на бак или котёл. Пропадает только пометка Thirst в подсказке Jade.
    ("ThirstWasTaken-*.jar", "thirst.mixins.json", "jade.MixinFluidView",
     "Thirst Was Taken: убрано встраивание в Jade, из-за которого игра падала при взгляде на жидкость."),
]


def _fix_mixins(game, log=print):
    n = 0
    for pattern, cfg_name, mixin, msg in MIXIN_FIXES:
        for f in glob.glob(os.path.join(game, "mods", pattern)):
            with zipfile.ZipFile(f) as z:
                cfg = json.loads(z.read(cfg_name))
                lists = [k for k in ("mixins", "client", "server") if mixin in cfg.get(k, [])]
                if not lists:
                    continue
                for k in lists:
                    cfg[k].remove(mixin)
                tmp = f + ".tmp"
                with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
                    for info in z.infolist():
                        out.writestr(info, json.dumps(cfg, indent=2) if info.filename == cfg_name else z.read(info))
            _make_writable(f)
            os.replace(tmp, f)
            log(msg)
            n += 1
    return n


RARE_MAX, RARE_FROM_SPAWN, VILLAGE_RADIUS = 1, 1000, 120  # радиус 120 — предел Millénaire (villageRadiusOverride)


def _rare_villages(game):
    """Деревня Millénaire должна быть находкой: каждый тип деревни не больше одной на мир и не ближе 1000 блоков от спавна,
    а территория у каждой деревни максимальная, какую держит мод.
    Правки пишем в millenaire-custom — Millénaire читает их поверх своих файлов и не трогает при обновлении."""
    jar = next((os.path.join(game, "mods", f) for f in os.listdir(os.path.join(game, "mods"))
                if re.match(r"millenaire-\d.*\.jar$", f)), None)
    if not jar:
        return 0
    out, n = os.path.join(game, "millenaire-custom", "annomille_rare", "cultures"), 0
    with zipfile.ZipFile(jar) as z:
        for name in z.namelist():
            m = re.match(r"millenaire/cultures/([^/]+)/villages/([^/]+\.json)$", name)
            if not m:
                continue
            j = json.loads(z.read(name).decode("utf-8-sig"))
            if j.get("lone_building") or j.get("player_controlled") or not j.get("weight") or j.get("spawnable") is False:
                continue
            j["max"] = min(j.get("max", RARE_MAX), RARE_MAX)
            j["min_distance_from_spawn"] = max(j.get("min_distance_from_spawn", 0), RARE_FROM_SPAWN)
            j["radius"] = max(j.get("radius", 0), VILLAGE_RADIUS)
            dest = os.path.join(out, m.group(1), "villages", m.group(2))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            json.dump(j, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            n += 1
    return n


NEOFORGE = "21.1.264"
NEO_ID = f"neoforge-{NEOFORGE}"
NEO_URL = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{NEOFORGE}/{NEO_ID}-installer.jar"
JRE_URL = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse"
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CACHE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "AnnoMille")


def _java_version(exe):
    try:
        out = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=30, creationflags=NOWIN).stderr
    except (OSError, subprocess.SubprocessError):
        return 0
    m = re.search(r'version "(\d+)', out)
    return int(m.group(1)) if m else 0


def find_java(log=print):
    """Java 21+: из официального лаунчера, TLauncher, системы или скачанная в кэш установщика."""
    appdata, local = os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")
    cands = [os.path.join(os.environ["JAVA_HOME"], "bin", "java.exe")] if os.environ.get("JAVA_HOME") else []
    cands.append(shutil.which("java"))
    for base in (os.path.join(CACHE, "jre"), os.path.join(appdata, ".minecraft", "runtime"), os.path.join(appdata, ".tlauncher"),
                 os.path.join(local, "Packages", "Microsoft.4297127D64EC6_8wekyb3d8bbwe", "LocalCache", "Local", "runtime"),
                 os.path.join(os.environ.get("ProgramFiles", ""), "Java"), os.path.join(os.environ.get("ProgramFiles", ""), "Eclipse Adoptium")):
        cands += glob.glob(os.path.join(base, "**", "bin", "java.exe"), recursive=True)
    for exe in cands:
        if exe and os.path.exists(exe) and _java_version(exe) >= 21:
            return exe
    log("Java 21 не нашлась, скачиваю (около 45 МБ)...")
    data = urllib.request.urlopen(urllib.request.Request(JRE_URL, headers=UA), timeout=600).read()
    dest = os.path.join(CACHE, "jre")
    shutil.rmtree(dest, ignore_errors=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(dest)
    exe = next(iter(glob.glob(os.path.join(dest, "*", "bin", "java.exe"))), None)
    if not exe or _java_version(exe) < 21:
        raise RuntimeError("не удалось подготовить Java 21")
    return exe


def install_neoforge(mc, log=print):
    """Ставит версию NeoForge 1.21.1 в папку лаунчера mc (обычно %APPDATA%\\.minecraft). Уже стоящую пропускает."""
    if os.path.exists(os.path.join(mc, "versions", NEO_ID, NEO_ID + ".json")):
        log(f"NeoForge {NEOFORGE} уже установлен.")
        return
    os.makedirs(mc, exist_ok=True)
    prof = os.path.join(mc, "launcher_profiles.json")
    if not os.path.exists(prof):  # без этого файла установщик NeoForge отказывается работать
        open(prof, "w", encoding="utf-8").write('{"profiles": {}}')
    java = find_java(log)
    log(f"Скачиваю NeoForge {NEOFORGE}...")
    jar = os.path.join(CACHE, NEO_ID + "-installer.jar")
    os.makedirs(CACHE, exist_ok=True)
    open(jar, "wb").write(urllib.request.urlopen(urllib.request.Request(NEO_URL, headers=UA), timeout=300).read())
    log("Ставлю Minecraft 1.21.1 и NeoForge (несколько минут)...")
    for attempt in range(3):  # библиотеки иногда не докачиваются с первого раза; скачанные повторно не качаются
        r = subprocess.run([java, "-jar", jar, "--install-client", mc], cwd=CACHE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800, creationflags=NOWIN)
        if r.returncode == 0:
            break
        log("Не всё скачалось, пробую ещё раз...")
    if r.returncode != 0 or not os.path.exists(os.path.join(mc, "versions", NEO_ID, NEO_ID + ".json")):
        for line in (r.stdout + r.stderr).strip().splitlines()[-15:]:
            log("  " + line)
        raise RuntimeError("установщик NeoForge завершился с ошибкой")
    log(f"NeoForge {NEOFORGE} установлен.")


PROFILE = "Anno Mille"
MILLIDA_PROFILE = "ANNO MILLE"


def launchers():
    """Найденные лаунчеры, где установщик сам создаёт профиль NeoForge 1.21.1: (название, способ, папка)."""
    appdata, local = os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")
    mc, found = os.path.join(appdata, ".minecraft"), []
    if os.path.isdir(os.path.join(appdata, "net.millida.launcher")):
        found.append(("Millida", "millida", _millida_dir()))
    if os.path.exists(os.path.join(appdata, "KLauncher", "config.json")):
        found.append(("KLauncher", "klauncher", os.path.join(_klauncher_game()[0], "instances", PROFILE)))
    if os.path.isdir(os.path.join(appdata, ".tlauncher")):
        found.append(("TLauncher", "mc", mc))
    if os.path.exists(os.path.join(mc, "launcher_profiles.json")) or \
            os.path.isdir(os.path.join(local, "Packages", "Microsoft.4297127D64EC6_8wekyb3d8bbwe")):
        found.append(("Официальный лаунчер Minecraft", "mc", mc))
    if os.path.isdir(os.path.join(appdata, "PrismLauncher")):
        found.append(("Prism Launcher", "prism", os.path.dirname(_prism_dir())))
    return found


def _millida_dir():
    return os.path.join(os.environ.get("APPDATA", ""), "net.millida.launcher", "minecraft", "profiles",
                        re.sub(r"[^A-Za-z0-9]", "", MILLIDA_PROFILE))


def millida_profile():
    """Профиль Millida «ANNO MILLE» на 1.21.1 + NeoForge (сам NeoForge Millida скачает при запуске). Уже созданный не трогает."""
    pj = os.path.join(os.environ.get("APPDATA", ""), "net.millida.launcher", "profiles.json")
    d = _millida_dir()
    profs = json.load(open(pj, encoding="utf-8")) if os.path.exists(pj) else []
    folder = os.path.basename(d).lower()   # Millida называет папку профиля его именем без пробелов и знаков
    if not any(re.sub(r"[^A-Za-z0-9]", "", p.get("name", "")).lower() == folder for p in profs):
        profs.append({"name": MILLIDA_PROFILE, "version": "1.21.1", "fabric": False, "loader": "neoforge",
                      "loader_version": NEOFORGE, "icon": None})
        json.dump(profs, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.makedirs(d, exist_ok=True)
    s = os.path.join(d, "millida-settings.json")
    if not os.path.exists(s):
        json.dump({"loader": "neoforge", "loaderVersion": NEOFORGE, "name": MILLIDA_PROFILE, "version": "1.21.1",
                   "ramMb": RAM_MB, "jvmArgs": JVM_ARGS}, open(s, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return d


RAM_MB = 8192
# G1 с короткими паузами: при ~200 модах сборка мусора по умолчанию даёт заметные фризы
JVM_ARGS = ("-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=50 -XX:+UnlockExperimentalVMOptions "
            "-XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 "
            "-XX:+DisableExplicitGC -XX:+AlwaysPreTouch")


def _tune_memory(game, log):
    """Профиль Millida без своей памяти получает от лаунчера слишком мало: ставим 8 ГБ и настройки сборщика мусора.
    Что игрок задал сам, не трогаем."""
    s = os.path.join(game, "millida-settings.json")
    if not os.path.exists(s):
        return
    j = json.load(open(s, encoding="utf-8"))
    changed = False
    if not j.get("ramMb"):
        j["ramMb"], changed = RAM_MB, True
    if not j.get("jvmArgs"):
        j["jvmArgs"], changed = JVM_ARGS, True
    if changed:
        json.dump(j, open(s, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        log(f"Millida: игре выделено {RAM_MB // 1024} ГБ памяти и настроена сборка мусора.")


def _klauncher_game():
    """(папка игры KLauncher, включены ли общие папки)."""
    base = os.path.join(os.environ.get("APPDATA", ""), "KLauncher")
    try:
        g = json.load(open(os.path.join(base, "config.json"), encoding="utf-8")).get("game", {})
    except (OSError, ValueError):
        g = {}
    return g.get("path") or os.path.join(base, "game"), g.get("useSharedFolder", False)


def klauncher_instance(log=print):
    """Сборка KLauncher «Anno Mille»: версия NeoForge в её versions/, библиотеки в общей папке библиотек KLauncher."""
    import datetime, _winapi
    game, shared = _klauncher_game()
    d = os.path.join(game, "instances", PROFILE)
    vdir = os.path.join(d, "versions", PROFILE)
    if not os.path.exists(os.path.join(vdir, PROFILE + ".json")):
        install_neoforge(game, log)
        os.makedirs(vdir, exist_ok=True)
        shutil.copy(os.path.join(game, "versions", NEO_ID, NEO_ID + ".json"), os.path.join(vdir, PROFILE + ".json"))
        shutil.copy(os.path.join(game, "versions", "1.21.1", "1.21.1.jar"), os.path.join(vdir, PROFILE + ".jar"))
    meta = os.path.join(d, ".meta")
    if not os.path.exists(meta):
        json.dump({"installedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                   "lastPlayed": None, "timePlayed": 0, "loader": {"type": "neoforge", "version": NEO_ID}, "modpackData": None},
                  open(meta, "w", encoding="utf-8"))
    if shared:  # как у сборок самого KLauncher: ресурспаки, миры, скриншоты и шейдеры общие
        for sub in ("resourcepacks", "saves", "screenshots", "shaderpacks"):
            link, target = os.path.join(d, sub), os.path.join(game, "shared", sub)
            os.makedirs(target, exist_ok=True)
            if not os.path.exists(link):
                _winapi.CreateJunction(target, link)
    return d


def _prism_dir():
    base, inst = os.path.join(os.environ.get("APPDATA", ""), "PrismLauncher"), "instances"
    cfg = os.path.join(base, "prismlauncher.cfg")
    if os.path.exists(cfg):
        m = re.search(r"^InstanceDir=(.+)$", open(cfg, encoding="utf-8", errors="replace").read(), re.M)
        inst = m.group(1).strip() if m else inst
    return os.path.join(base, inst, PROFILE, "minecraft")


def prism_instance(name=PROFILE):
    """Создаёт (или находит) экземпляр Prism с Minecraft 1.21.1 + NeoForge; сам NeoForge Prism скачает при запуске."""
    d = os.path.dirname(_prism_dir())
    os.makedirs(os.path.join(d, "minecraft"), exist_ok=True)
    if not os.path.exists(os.path.join(d, "mmc-pack.json")):
        json.dump({"formatVersion": 1, "components": [{"uid": "net.minecraft", "version": "1.21.1", "important": True},
                                                      {"uid": "net.neoforged", "version": NEOFORGE}]},
                  open(os.path.join(d, "mmc-pack.json"), "w", encoding="utf-8"), indent=2)
    if not os.path.exists(os.path.join(d, "instance.cfg")):
        open(os.path.join(d, "instance.cfg"), "w", encoding="utf-8").write(
            f"[General]\nConfigVersion=1.2\nInstanceType=OneSix\nname={name}\niconKey=default\n"
            f"OverrideMemory=true\nMinMemAlloc=1024\nMaxMemAlloc={RAM_MB}\nOverrideJavaArgs=true\nJvmArgs={JVM_ARGS}\n")
    return os.path.join(d, "minecraft")


class GameRunning(RuntimeError):
    pass


def game_running(game):
    """Пока игра открыта, её лог занят. Открытая игра при выходе перезапишет квесты старой копией из памяти."""
    p = os.path.join(game, "logs", "latest.log")
    try:
        os.rename(p, p)
    except OSError as e:
        return getattr(e, "winerror", None) == 32
    return False


def run(game, log=print, progress=lambda done, total: None):
    root = data_root()
    if game_running(game):
        raise GameRunning("игра с этим профилем сейчас запущена. Закрой Minecraft и запусти установку ещё раз.")
    os.makedirs(game, exist_ok=True)
    _tune_memory(game, log)

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
    n = _fix_excalibur(game)
    if n:
        log(f"Excalibur: убрал {n} текстур мобов, чтобы не спорили с Fresh Animations.")
    _fix_mixins(game, log)
    n = _rare_villages(game)
    if n:
        log(f"Деревни Millénaire: {n} типов, каждый не больше одного на мир, дальше {RARE_FROM_SPAWN} блоков от спавна, радиус {VILLAGE_RADIUS}.")

    log("Копирую настройки, квесты, интерфейс и навыки...")
    skipped = []
    old_ui = os.path.join(game, "resourcepacks", "MillenaireUI")
    if os.path.isdir(old_ui):  # раньше пак лежал здесь; теперь его всегда включает Open Loader
        os.makedirs(os.path.join(game, "_old"), exist_ok=True)
        shutil.move(old_ui, os.path.join(game, "_old", f"MillenaireUI-{int(time.time())}"))
    for sub in ("config", "resourcepacks", "mods"):
        if os.path.isdir(os.path.join(root, "pack", sub)):
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
        ref = dict(l.split(":", 1) for l in open(ref_path, encoding="utf-8-sig").read().splitlines() if ":" in l)
        lines = [l for l in open(opt, encoding="utf-8-sig", errors="replace").read().splitlines() if l.strip()]
        idx = {l.split(":", 1)[0]: i for i, l in enumerate(lines) if ":" in l}
        for k in [k for k in ref if k.startswith("key_") or k in ("lang", "resourcePacks", "darkMojangStudiosBackground")]:
            if k in idx:
                lines[idx[k]] = f"{k}:{ref[k]}"
            else:
                lines.append(f"{k}:{ref[k]}")
        # Без строки version первой игра считает файл очень старым, «чинит» его, падает и сбрасывает все настройки.
        lines = ["version:" + ref.get("version", "3955")] + [l for l in lines if not l.startswith("version:")]
        _make_writable(opt)
        open(opt, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    log("Клавиши и порядок ресурспаков применены.")

    log("Перекрашиваю окна модов в тёмный стиль...")
    from PIL import Image
    pack, n = os.path.join(game, "config", "openloader", "packs", "MillenaireUI"), 0
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
    _ftb_theme(game, pack)
    n = _fix_animations(game, pack)
    if n:
        log(f"Исправлено сломанных анимаций мобов: {n}.")
    log("Всё установлено. Выдели игре 8 ГБ памяти и создай новый мир на сложности «Сложная».")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run(sys.argv[1])
