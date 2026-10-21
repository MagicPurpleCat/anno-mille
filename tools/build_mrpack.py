"""Сборка Anno-Mille-<версия>.mrpack (формат Modrinth): моды с Modrinth ссылками + overrides из pack/.

    python tools/build_mrpack.py <версия>

Файлы не с Modrinth (Millénaire, FTB, SWEM, Excalibur) в .mrpack не входят — их докачивает
tools/install.py --extra-only (см. README).
"""
import concurrent.futures as cf, json, os, sys, urllib.parse, urllib.request, zipfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
API, UA = "https://api.modrinth.com/v2", {"User-Agent": "anno-mille-builder/1.0"}
DIRS = {"mod": "mods", "rp": "resourcepacks", "shader": "shaderpacks"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def resolve(e):
    kind, slug, want = e
    q = urllib.parse.quote
    url = f"{API}/project/{slug}/version?game_versions={q(json.dumps(['1.21.1']))}"
    if kind == "mod":
        url += f"&loaders={q(json.dumps(['neoforge']))}"
    vs = get(url)
    v = next((x for x in vs if x["version_type"] == "release"), vs[0]) if want == "*" else next(x for x in vs if x["version_number"] == want)
    p = get(f"{API}/project/{slug}")
    f = next((x for x in v["files"] if x["primary"]), v["files"][0])
    env = {"client": "required" if p["client_side"] != "unsupported" else "unsupported",
           "server": "required" if p["server_side"] != "unsupported" else "unsupported"}
    if kind != "mod":
        env = {"client": "required", "server": "unsupported"}
    return {"path": f"{DIRS[kind]}/{f['filename']}", "hashes": {"sha1": f["hashes"]["sha1"], "sha512": f["hashes"]["sha512"]},
            "env": env, "downloads": [f["url"]], "fileSize": f["size"]}


entries = [tuple(l.split()[:3]) for l in open(os.path.join(ROOT, "tools", "manifest.txt"), encoding="utf-8")
           if l.strip() and not l.startswith("#")]
with cf.ThreadPoolExecutor(8) as ex:
    files = list(ex.map(resolve, entries))
index = {"formatVersion": 1, "game": "minecraft", "versionId": VER, "name": "Anno Mille",
         "summary": "Сборка вокруг Millénaire: живые деревни XI века, сложное выживание, квесты и прокачка.",
         "files": files, "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.264"}}
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
out = os.path.join(ROOT, "dist", f"Anno-Mille-{VER}.mrpack")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("modrinth.index.json", json.dumps(index, ensure_ascii=False, indent=1))
    pack = os.path.join(ROOT, "pack")
    for r, _, fs in os.walk(pack):
        for f in fs:
            p = os.path.join(r, f)
            z.write(p, "overrides/" + os.path.relpath(p, pack).replace(os.sep, "/"))
print(f"{out}: {len(files)} files from Modrinth, {os.path.getsize(out) / 1e6:.1f} MB")
