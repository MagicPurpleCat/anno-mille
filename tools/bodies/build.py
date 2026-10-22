"""Сборка pack/mods/annomille_bodies-1.0.0.jar: вышедший игрок остаётся в мире телом с его вещами (см. src/).

    python tools/bodies/build.py

Нужен JDK 21 (javac 17 не читает классы Minecraft 1.21): JAVA_HOME, PATH или %LOCALAPPDATA%\\AnnoMille\\jdk.
Classpath — библиотеки и клиент NeoForge 21.1.264 из %APPDATA%\\.minecraft (ставится install.py).
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VERSION = "1.0.0"
OUT = os.path.join(ROOT, "pack", "mods", f"annomille_bodies-{VERSION}.jar")
NEO = "21.1.264"
MC = os.path.join(os.environ.get("APPDATA", ""), ".minecraft")
LIB = os.path.join(MC, "libraries")


def javac21():
    cands = [os.path.join(os.environ["JAVA_HOME"], "bin", "javac.exe")] if os.environ.get("JAVA_HOME") else []
    cands += [shutil.which("javac")] + glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "AnnoMille", "jdk", "*", "bin", "javac.exe"))
    cands += glob.glob(r"C:\Program Files\*\jdk-*\bin\javac.exe")
    for exe in cands:
        if exe and os.path.exists(exe):
            v = subprocess.run([exe, "-version"], capture_output=True, text=True).stdout + ""
            m = re.search(r"javac (\d+)", v)
            if m and int(m.group(1)) >= 21:
                return exe
    sys.exit("нужен JDK 21 (javac): скачайте Adoptium JDK 21 в %LOCALAPPDATA%\\AnnoMille\\jdk")


def classpath():
    ver = json.load(open(os.path.join(MC, "versions", f"neoforge-{NEO}", f"neoforge-{NEO}.json"), encoding="utf-8"))
    jars = [os.path.join(LIB, f"net/neoforged/neoforge/{NEO}/neoforge-{NEO}-client.jar"),  # пропатченные классы — первыми
            os.path.join(LIB, f"net/neoforged/neoforge/{NEO}/neoforge-{NEO}-universal.jar")]
    jars += glob.glob(os.path.join(LIB, "net", "minecraft", "client", "1.21.1-*", "client-1.21.1-*-srg.jar"))
    jars += [os.path.join(LIB, l["artifact"]["path"]) for l in ver["libraries"] if l.get("artifact")]
    jars = [j for j in jars if os.path.exists(j)]
    if len(jars) < 10:
        sys.exit(f"не найдены библиотеки NeoForge {NEO} в {LIB}")
    return os.pathsep.join(jars)


TOML = f'''modLoader="javafml"
loaderVersion="[4,)"
license="CC0"

[[mods]]
modId="annomille_bodies"
version="{VERSION}"
displayName="Anno Mille: тело вышедшего игрока"
description=\'\'\'Вышедший игрок остаётся в мире телом с его вещами: тело можно обыскать или убить.
Когда игрок заходит, тело исчезает, а оставшиеся вещи возвращаются.\'\'\'

[[dependencies.annomille_bodies]]
modId="neoforge"
type="required"
versionRange="[21.1,)"
ordering="NONE"
side="BOTH"
'''
FILES = {
    # Carry On не поднимает тело; в чужом привате FTB Chunks обыск запрещён (тела нет в entity_interact_whitelist)
    "data/carryon/tags/entity_types/entity_blacklist.json": '{"replace": false, "values": ["annomille_bodies:body"]}\n',
    "assets/annomille_bodies/lang/ru_ru.json": '{"entity.annomille_bodies.body": "Тело игрока"}\n',
    "assets/annomille_bodies/lang/en_us.json": '{"entity.annomille_bodies.body": "Player body"}\n',
}

with tempfile.TemporaryDirectory() as tmp:
    srcs = glob.glob(os.path.join(HERE, "src", "**", "*.java"), recursive=True)
    subprocess.run([javac21(), "--release", "21", "-proc:none", "-encoding", "UTF-8", "-nowarn", "-cp", classpath(), "-d", tmp, *srcs], check=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        z.writestr("META-INF/neoforge.mods.toml", TOML)
        for name, text in FILES.items():
            z.writestr(name, text.encode("utf-8"))
        for p in glob.glob(os.path.join(tmp, "**", "*.class"), recursive=True):
            z.write(p, os.path.relpath(p, tmp).replace(os.sep, "/"))
print("ok:", OUT)
