"""Готовит config/defaultoptions/ для мода Default Options из pack/options.txt.

keybindings.txt делает наши клавиши стандартными: даже если лаунчер или сбой сбросят options.txt,
квесты останутся на Ё, зум на своей клавише и т. д. options.txt копируется модом, только если у игрока его ещё нет.
Пак интерфейса включает Open Loader (config/openloader/packs), поэтому в списке resourcePacks его нет.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pack", "options.txt")
OUT = os.path.join(ROOT, "pack", "config", "defaultoptions")
DROP = {"file/MillenaireUI"}


def clean(lines):
    out = []
    for l in lines:
        k, _, v = l.partition(":")
        if k == "resourcePacks":
            v = json.dumps([p for p in json.loads(v) if p not in DROP and "MedievalMenu" not in p], ensure_ascii=False)
        elif k == "darkMojangStudiosBackground":
            v = "true"
        out.append(f"{k}:{v}")
    if not any(l.startswith("darkMojangStudiosBackground:") for l in out):
        out.append("darkMojangStudiosBackground:true")
    out = [l for l in out if not l.startswith("version:")]
    return ["version:3955"] + out


def main():
    lines = clean([l for l in open(SRC, encoding="utf-8-sig").read().splitlines() if ":" in l])
    text = "\n".join(lines) + "\n"
    open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "options.txt"), "w", encoding="utf-8", newline="\n").write(text)
    keys = [l for l in lines if l.startswith("key_")]
    open(os.path.join(OUT, "keybindings.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(keys) + "\n")
    print(f"options: {len(lines)} строк, клавиш: {len(keys)}")


if __name__ == "__main__":
    main()
