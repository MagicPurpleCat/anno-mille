"""Переносит собранный пак (out/MillenaireUI) в pack/config/openloader/packs/MillenaireUI.

Перекрашенные окна модов не переносятся: это производные чужих текстур, установщик делает их сам на компьютере игрока.
"""
import os, shutil, sys

UI = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(UI, "out", "MillenaireUI")
DST = os.path.join(os.path.dirname(os.path.dirname(UI)), "pack", "config", "openloader", "packs", "MillenaireUI")

shutil.rmtree(DST, ignore_errors=True)
n = 0
for root, _, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC).replace("\\", "/")
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] == "assets" and parts[1] != "minecraft" and parts[2] == "textures":
        continue
    for f in files:
        os.makedirs(os.path.join(DST, rel), exist_ok=True)
        shutil.copy2(os.path.join(root, f), os.path.join(DST, rel, f))
        n += 1
print(f"скопировано файлов: {n}")
