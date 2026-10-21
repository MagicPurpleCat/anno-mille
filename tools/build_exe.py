"""Сборка dist/AnnoMille-Setup.exe (PyInstaller, один файл, внутри pack/ и списки модов).

    python tools/build_exe.py
"""
import os, sys
from PIL import Image
import PyInstaller.__main__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "tools")
icon = os.path.join(T, "icon.ico")
Image.open(os.path.join(T, "icon.png")).save(icon, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
sep = os.pathsep
PyInstaller.__main__.run([
    os.path.join(T, "installer_gui.py"), "--onefile", "--windowed", "--noconfirm", "--clean",
    "--name", "AnnoMille-Setup", "--icon", icon,
    "--distpath", os.path.join(ROOT, "dist"), "--workpath", os.path.join(ROOT, "build"), "--specpath", os.path.join(ROOT, "build"),
    "--add-data", f"{os.path.join(ROOT, 'pack')}{sep}pack",
    "--add-data", f"{os.path.join(T, 'manifest.txt')}{sep}tools",
    "--add-data", f"{os.path.join(T, 'expected_mods.txt')}{sep}tools",
    "--add-data", f"{icon}{sep}tools",
    "--hidden-import", "PIL.Image",
])
print("ok:", os.path.join(ROOT, "dist", "AnnoMille-Setup.exe"))
