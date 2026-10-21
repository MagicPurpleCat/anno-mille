"""Пишет tools/expected_mods.txt — точные имена jar сборки (для удаления старых версий установщиком)."""
import concurrent.futures as cf, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import install  # noqa: E402

root = install.data_root()
entries = [tuple(l.split()[:3]) for l in open(os.path.join(root, "tools", "manifest.txt"), encoding="utf-8")
           if l.strip() and not l.startswith("#")]
with cf.ThreadPoolExecutor(8) as ex:
    resolved = list(ex.map(lambda e: install._resolve(*e), entries))
names = sorted({r[1] for r in resolved if r and r[0] == "mods"} | {n for s, n, _ in install.EXTRA if s == "mods"}
               | {f for f in os.listdir(os.path.join(root, "pack", "mods")) if f.endswith(".jar")})
open(os.path.join(root, "tools", "expected_mods.txt"), "w", encoding="utf-8").write("\n".join(names) + "\n")
print(len(names), "mods")
