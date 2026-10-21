"""Окно установщика Anno Mille. Собирается в AnnoMille-Setup.exe командой tools/build_exe.bat."""
import glob, os, sys, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import install  # noqa: E402

BG, PANEL, TEXT, MUTED, ACCENT = "#121214", "#1c1c20", "#f4f4f5", "#9a9aa2", "#e8c26a"
APPDATA, HOME = os.environ.get("APPDATA", ""), os.path.expanduser("~")


def profile_info(path):
    """(версия Minecraft, загрузчик) из файлов лаунчера, если их удаётся прочитать."""
    import json
    try:
        s = os.path.join(path, "millida-settings.json")                 # Millida
        if os.path.exists(s):
            j = json.load(open(s, encoding="utf-8"))
            return j.get("version"), j.get("loader")
        s = os.path.join(os.path.dirname(path), "mmc-pack.json")         # Prism / MultiMC
        if os.path.exists(s):
            comps = {c["uid"]: c.get("version") for c in json.load(open(s, encoding="utf-8"))["components"]}
            loader = next((n for u, n in (("net.neoforged", "neoforge"), ("net.minecraftforge", "forge"),
                                          ("net.fabricmc.fabric-loader", "fabric"), ("org.quiltmc.quilt-loader", "quilt")) if u in comps), "vanilla")
            return comps.get("net.minecraft"), loader
        s = os.path.join(path, "profile.json")                           # Modrinth App
        if os.path.exists(s):
            j = json.load(open(s, encoding="utf-8"))
            return j.get("game_version") or j.get("metadata", {}).get("game_version"), j.get("loader") or j.get("metadata", {}).get("loader")
        s = os.path.join(path, "minecraftinstance.json")                 # CurseForge
        if os.path.exists(s):
            j = json.load(open(s, encoding="utf-8"))
            ml = (j.get("baseModLoader") or {}).get("name", "")
            return j.get("gameVersion"), ml.split("-")[0] if ml else None
    except Exception:
        pass
    return None, None


def suits(info):
    v, l = info
    if v is None:
        return None                       # неизвестно
    return v == "1.21.1" and (l or "").lower() == "neoforge"


def find_game_folders():
    """Папки игры популярных лаунчеров: (подпись, путь), подходящие профили — первыми."""
    found = []

    def add(label, path):
        if os.path.isdir(path) and os.path.normcase(path) not in {os.path.normcase(f[1]) for f in found}:
            v, l = profile_info(path)
            ok = suits((v, l))
            tag = "✓ подходит" if ok else (f"✗ {v} {l or ''}".strip() if ok is False else "версия неизвестна")
            found.append((f"{label}   [{tag}]", path, ok))

    for p in glob.glob(os.path.join(APPDATA, "net.millida.launcher", "minecraft", "profiles", "*")):
        try:
            import json
            name = json.load(open(os.path.join(p, "millida-settings.json"), encoding="utf-8")).get("name") or os.path.basename(p)
        except Exception:
            name = os.path.basename(p)
        add(f"Millida · {name}", p)
    for p in glob.glob(os.path.join(APPDATA, "PrismLauncher", "instances", "*")):
        sub = next((s for s in ("minecraft", ".minecraft") if os.path.isdir(os.path.join(p, s))), None)
        if sub:
            add(f"Prism Launcher · {os.path.basename(p)}", os.path.join(p, sub))
    for base in ("ModrinthApp", "com.modrinth.theseus"):
        for p in glob.glob(os.path.join(APPDATA, base, "profiles", "*")):
            add(f"Modrinth App · {os.path.basename(p)}", p)
    for p in glob.glob(os.path.join(HOME, "curseforge", "minecraft", "Instances", "*")):
        add(f"CurseForge · {os.path.basename(p)}", p)
    for p in glob.glob(os.path.join(APPDATA, "ATLauncher", "instances", "*")):
        add(f"ATLauncher · {os.path.basename(p)}", p)
    add("TLauncher / официальный лаунчер · .minecraft", os.path.join(APPDATA, ".minecraft"))
    order = {True: 0, None: 1, False: 2}
    return sorted(found, key=lambda f: order[f[2]])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Anno Mille · установка")
        self.configure(bg=BG)
        self.geometry("720x560")
        self.minsize(640, 520)
        try:
            self.iconbitmap(os.path.join(install.data_root(), "tools", "icon.ico"))
        except tk.TclError:
            pass
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor=PANEL, background=ACCENT, bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)

        tk.Label(self, text="Anno Mille", font=("Segoe UI Semibold", 30), fg=TEXT, bg=BG).pack(pady=(22, 0))
        tk.Label(self, text="Год тысячный · сборка вокруг Millénaire · Minecraft 1.21.1 + NeoForge",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG).pack()

        tk.Label(self, text="1. Создай в лаунчере профиль Minecraft 1.21.1 + NeoForge 21.1.264 и запусти его один раз.\n"
                            "2. Выбери этот профиль ниже и нажми «Установить».",
                 font=("Segoe UI", 10), fg=TEXT, bg=BG, justify="left").pack(anchor="w", padx=28, pady=(18, 8))

        box = tk.Frame(self, bg=PANEL)
        box.pack(fill="x", padx=28)
        self.var = tk.StringVar()
        self.list = tk.Listbox(box, height=6, bg=PANEL, fg=TEXT, selectbackground="#3a3a42", selectforeground=TEXT,
                               highlightthickness=0, borderwidth=0, font=("Segoe UI", 10), activestyle="none")
        self.list.pack(fill="x", padx=8, pady=8)
        self.folders = find_game_folders()
        for i, (label, path, ok) in enumerate(self.folders):
            self.list.insert("end", f"  {label}")
            self.list.itemconfig(i, fg=TEXT if ok else (MUTED if ok is None else "#8a6a6a"))
        if self.folders:
            self.list.selection_set(0)
        self.list.bind("<<ListboxSelect>>", lambda e: self.show_path())

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=28, pady=(6, 0))
        self.path_label = tk.Label(row, text="", font=("Segoe UI", 9), fg=MUTED, bg=BG, anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True)
        self.btn(row, "Другая папка…", self.pick).pack(side="right")
        self.show_path()

        self.go = self.btn(self, "Установить", self.start, big=True)
        self.go.pack(pady=(16, 8))
        self.bar = ttk.Progressbar(self, mode="determinate")
        self.bar.pack(fill="x", padx=28)
        self.log = tk.Text(self, height=8, bg=PANEL, fg=TEXT, borderwidth=0, highlightthickness=0, font=("Consolas", 9),
                           wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=28, pady=(10, 20))

    def btn(self, parent, text, cmd, big=False):
        return tk.Button(parent, text=text, command=cmd, bg="#2a2a30" if not big else ACCENT, fg=TEXT if not big else "#141416",
                         activebackground="#3a3a42" if not big else "#f2d58e", relief="flat", cursor="hand2",
                         font=("Segoe UI Semibold", 13 if big else 10), padx=28 if big else 12, pady=8 if big else 4, borderwidth=0)

    def selected(self):
        sel = self.list.curselection()
        return self.folders[sel[0]] if sel else None

    def show_path(self):
        f = self.selected()
        self.path_label.config(text=f[1] if f else "Папка не выбрана")

    def pick(self):
        p = filedialog.askdirectory(title="Папка игры профиля (там, где mods и config)")
        if p:
            p = os.path.normpath(p)
            self.folders.append(("Выбрано вручную", p, suits(profile_info(p))))
            self.list.insert("end", "  Выбрано вручную · " + os.path.basename(p))
            self.list.selection_clear(0, "end")
            self.list.selection_set("end")
            self.show_path()

    def write(self, msg):
        def do():
            self.log.config(state="normal")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.config(state="disabled")
        self.after(0, do)

    def progress(self, done, total):
        self.after(0, lambda: self.bar.config(maximum=total, value=done))

    def start(self):
        f = self.selected()
        if not f:
            messagebox.showwarning("Anno Mille", "Выбери папку игры.")
            return
        game, ok = f[1], f[2]
        if ok is False:
            v, l = profile_info(game)
            text = (f"Этот профиль на Minecraft {v} ({l}).\n\n"
                    "Сборке нужен Minecraft 1.21.1 с NeoForge, иначе игра не запустится. "
                    "Создай в лаунчере такой профиль и выбери его.\n\nВсё равно установить сюда?")
            if not messagebox.askyesno("Anno Mille", text):
                return
        self.go.config(state="disabled", text="Устанавливаю…")
        threading.Thread(target=self.work, args=(game,), daemon=True).start()

    def work(self, game):
        try:
            install.run(game, log=self.write, progress=self.progress)
            self.after(0, lambda: messagebox.showinfo("Anno Mille", "Готово! Выдели игре 8 ГБ памяти и запускай."))
            self.after(0, lambda: self.go.config(text="Установлено ✓"))
        except Exception as e:
            import socket, urllib.error
            if isinstance(e, (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError)):
                hint = "Не удалось скачать файлы. Проверь интернет и попробуй ещё раз."
            elif isinstance(e, PermissionError):
                hint = "Windows не дала записать файл. Закрой игру и лаунчер и попробуй ещё раз."
            else:
                hint = "Попробуй ещё раз. Если ошибка повторится, пришли этот текст автору сборки."
            self.write(f"Ошибка: {e}")
            self.after(0, lambda: messagebox.showerror("Anno Mille", f"{hint}\n\nПодробности: {e}"))
            self.after(0, lambda: self.go.config(state="normal", text="Попробовать ещё раз"))


if __name__ == "__main__":
    App().mainloop()
