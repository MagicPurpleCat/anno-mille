"""Сборка pack/mods/annomille_reputation-1.0.0.jar: репутация Millénaire растёт в 5 раз медленнее (mixin, см. src/).

    python tools/reputation/build.py

Нужен JDK 17+ (javac) и библиотека Mixin из любой установки NeoForge (ищется в .minecraft/libraries).
Мод без кода загрузчика (lowcodefml): FML сам подключает mixin-конфиг из neoforge.mods.toml.
"""
import glob, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "pack", "mods", "annomille_reputation-1.0.0.jar")
APPDATA = os.environ.get("APPDATA", "")

javac = shutil.which("javac") or next(iter(glob.glob(r"C:\Program Files\*\jdk-*\bin\javac.exe")), None)
mixin = next(iter(glob.glob(os.path.join(APPDATA, ".minecraft", "libraries", "net", "fabricmc", "sponge-mixin", "*", "*.jar"))), None)
if not javac or not mixin:
    sys.exit(f"нужны javac и sponge-mixin: javac={javac}, mixin={mixin}")

TOML = '''modLoader="lowcodefml"
loaderVersion="[1,)"
license="CC0"

[[mixins]]
config="annomille_reputation.mixins.json"

[[mods]]
modId="annomille_reputation"
version="1.0.0"
displayName="Anno Mille: медленная репутация"
description=\'\'\'Репутация в деревнях Millénaire растёт в 5 раз медленнее.\'\'\'

[[dependencies.annomille_reputation]]
modId="millenaire"
type="required"
versionRange="*"
ordering="AFTER"
side="BOTH"
'''
MIXINS = '''{
  "required": true,
  "minVersion": "0.8",
  "package": "annomille.mixin",
  "compatibilityLevel": "JAVA_17",
  "mixins": ["VillageReputationMixin"],
  "injectors": {"defaultRequire": 1}
}
'''

with tempfile.TemporaryDirectory() as tmp:
    srcs = glob.glob(os.path.join(HERE, "src", "**", "*.java"), recursive=True)
    subprocess.run([javac, "--release", "17", "-proc:none", "-encoding", "UTF-8", "-cp", mixin, "-d", tmp, *srcs], check=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        z.writestr("META-INF/neoforge.mods.toml", TOML)
        z.writestr("annomille_reputation.mixins.json", MIXINS)
        for p in glob.glob(os.path.join(tmp, "**", "*.class"), recursive=True):
            z.write(p, os.path.relpath(p, tmp).replace(os.sep, "/"))
print("ok:", OUT)
