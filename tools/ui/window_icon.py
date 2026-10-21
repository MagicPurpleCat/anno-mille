"""Иконка и заголовок окна игры через FancyMenu: значки 16/32 px из логотипа и строки в config/fancymenu/options.txt."""
import os, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "pack", "config", "fancymenu", "assets")
OPTIONS = os.path.join(ROOT, "pack", "config", "fancymenu", "options.txt")
SET = {
    "B:show_custom_window_icon": "true",
    "S:custom_window_icon_16": "config/fancymenu/assets/window_icon_16.png",
    "S:custom_window_icon_32": "config/fancymenu/assets/window_icon_32.png",
    "S:custom_window_title": "Anno Mille",
}

src = Image.open(os.path.join(ROOT, "tools", "icon.png")).convert("RGBA")
for s in (16, 32):
    src.resize((s, s), Image.LANCZOS).save(os.path.join(ASSETS, f"window_icon_{s}.png"))

text = open(OPTIONS, encoding="utf-8").read()
for k, v in SET.items():
    text, n = re.subn(rf"^{re.escape(k)} = '.*?';$", f"{k} = '{v}';", text, flags=re.M)
    assert n == 1, k
open(OPTIONS, "w", encoding="utf-8", newline="\n").write(text)
print("ok")
