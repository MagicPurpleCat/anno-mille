"""Окно установщика Anno Mille в стиле фона главного меню: тёмный фон с живыми волнами, белый текст,
полупрозрачные кнопки-«таблетки» с тонкой обводкой. Собирается в AnnoMille-Setup.exe командой tools/build_exe.py."""
import ctypes, gc, glob, io, json, os, queue, sys, threading, zipfile, tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import install  # noqa: E402

W, H = 960, 600
TEXT, MUTED, DIM, BAD = "#f4f4f5", "#9a9aa2", "#5f5f68", "#e39a9a"
APPDATA, HOME = os.environ.get("APPDATA", ""), os.path.expanduser("~")
ROOT = install.data_root()
FONT, FONT_B = "Inter Medium", "Inter SemiBold"


# ---------------------------------------------------------------- профили лаунчеров
def profile_info(path):
    """(версия Minecraft, загрузчик) из файлов лаунчера, если их удаётся прочитать."""
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
    """Папки игры популярных лаунчеров: (подпись, путь, подходит ли), подходящие первыми."""
    found = []

    def add(label, path):
        if os.path.isdir(path) and os.path.normcase(path) not in {os.path.normcase(f[1]) for f in found}:
            found.append((label, path, suits(profile_info(path))))

    for p in glob.glob(os.path.join(APPDATA, "net.millida.launcher", "minecraft", "profiles", "*")):
        try:
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


def tag_of(path, ok):
    if ok:
        return "подходит", MUTED
    if ok is None:
        return "версия неизвестна", DIM
    v, l = profile_info(path)
    return f"{v} {l or ''}".strip(), BAD


# ---------------------------------------------------------------- графика
def pill(w, h, fill, outline, radius=None):
    """Скруглённая полупрозрачная плашка с тонкой обводкой (рисуется вчетверо крупнее и уменьшается для гладких краёв)."""
    s = 4
    r = (radius if radius is not None else h / 2) * s
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r, fill=fill, outline=outline, width=s)
    return ImageTk.PhotoImage(im.resize((w, h), Image.LANCZOS))


def load_fonts():
    for f in glob.glob(os.path.join(ROOT, "tools", "ui", "fonts", "*.ttf")):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(f, 0x10, 0)   # FR_PRIVATE: шрифт виден только этой программе
        except Exception:
            pass


class Background:
    """Петля фона из главного меню сборки (кадры FMA), подогнанная под окно."""

    def __init__(self):
        self.frames, self.i = [], 0
        self.path = os.path.join(ROOT, "pack", "config", "fancymenu", "assets", "millenaire_bg.fma")
        self.first = self._frame(0) if os.path.exists(self.path) else Image.new("RGB", (W, H), (12, 12, 13))
        threading.Thread(target=self._load, daemon=True).start()

    def _fit(self, im):
        im = im.convert("RGB")
        k = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.BILINEAR)
        x, y = (im.width - W) // 2, im.height - H          # волны внизу кадра — оставляем низ
        return im.crop((x, y, x + W, y + H))

    def _frame(self, n):
        with zipfile.ZipFile(self.path) as z:
            return self._fit(Image.open(io.BytesIO(z.read(f"frames/{n}.png"))))

    def _load(self):
        try:
            with zipfile.ZipFile(self.path) as z:
                names = sorted((n for n in z.namelist() if n.startswith("frames/")), key=lambda n: int(n[7:-4]))
                for n in names[::2]:
                    buf = io.BytesIO()
                    self._fit(Image.open(io.BytesIO(z.read(n)))).save(buf, "JPEG", quality=90)
                    self.frames.append(buf.getvalue())
        except Exception:
            pass

    def next(self):
        if not self.frames:
            return self.first
        self.i = (self.i + 1) % len(self.frames)
        return Image.open(io.BytesIO(self.frames[self.i]))


# ---------------------------------------------------------------- окно
class Button:
    def __init__(self, app, x, y, w, h, text, cmd, big=False):
        self.app, self.cmd, self.enabled = app, cmd, True
        c = app.canvas
        a = (16, 70, 34, 210) if big else (10, 40, 24, 140)
        self.img_n = pill(w, h, (255, 255, 255, a[0]), (255, 255, 255, a[1]))
        self.img_h = pill(w, h, (255, 255, 255, a[2]), (255, 255, 255, a[3]))
        self.img = c.create_image(x, y, image=self.img_n)
        self.txt = c.create_text(x, y, text=text, fill=TEXT, font=(FONT_B if big else FONT, 12 if big else 10))
        for item in (self.img, self.txt):
            c.tag_bind(item, "<Enter>", lambda e: self.hover(True))
            c.tag_bind(item, "<Leave>", lambda e: self.hover(False))
            c.tag_bind(item, "<Button-1>", lambda e: self.enabled and self.cmd())

    def hover(self, on):
        if self.enabled:
            self.app.canvas.itemconfig(self.img, image=self.img_h if on else self.img_n)
            self.app.canvas.config(cursor="hand2" if on else "")

    def set(self, text=None, enabled=None, visible=None):
        c = self.app.canvas
        if text is not None:
            c.itemconfig(self.txt, text=text)
        if enabled is not None:
            self.enabled = enabled
            c.itemconfig(self.txt, fill=TEXT if enabled else DIM)
            c.itemconfig(self.img, image=self.img_n)
        if visible is not None:
            for item in (self.img, self.txt):
                c.itemconfig(item, state="normal" if visible else "hidden")


class App(tk.Tk):
    ROWS, ROW_H, LIST_X, LIST_W, LIST_Y = 5, 44, 200, 560, 228

    def __init__(self):
        super().__init__()
        load_fonts()
        self.title("Anno Mille · установка")
        self.geometry(f"{W}x{H}")
        self.resizable(False, False)
        self.configure(bg="#0c0c0d")
        try:
            self.iconbitmap(os.path.join(ROOT, "tools", "icon.ico"))
        except tk.TclError:
            pass
        self.after(10, self.dark_titlebar)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        c = self.canvas = tk.Canvas(self, width=W, height=H, highlightthickness=0, bd=0, bg="#0c0c0d")
        c.pack()
        self.bg = Background()
        self.bg_img = ImageTk.PhotoImage(self.bg.first)
        self.bg_item = c.create_image(0, 0, anchor="nw", image=self.bg_img)

        try:
            head = Image.open(os.path.join(ROOT, "tools", "installer_header.png"))
            self.head = ImageTk.PhotoImage(head)
            c.create_image(W // 2, 92, image=self.head)
        except OSError:
            c.create_text(W // 2, 92, text="ANNO MILLE", fill=TEXT, font=("Cinzel", 40))
        c.create_text(W // 2, 162, text="Г О Д   Т Ы С Я Ч Н Ы Й   ·   M I L L É N A I R E", fill=MUTED, font=(FONT, 9))

        c.create_text(self.LIST_X + 4, self.LIST_Y - 20, anchor="w", text="Куда установить", fill=MUTED, font=(FONT, 10))
        c.create_text(self.LIST_X + self.LIST_W - 4, self.LIST_Y - 20, anchor="e",
                      text="нужен профиль Minecraft 1.21.1 + NeoForge", fill=DIM, font=(FONT, 9))
        self.row_imgs = {k: pill(self.LIST_W, self.ROW_H - 8, *v, radius=14) for k, v in {
            "n": ((255, 255, 255, 8), (255, 255, 255, 26)), "h": ((255, 255, 255, 16), (255, 255, 255, 70)),
            "s": ((255, 255, 255, 24), (255, 255, 255, 190))}.items()}
        self.folders, self.sel, self.offset, self.hover_row, self.rows = find_game_folders(), 0, 0, None, []
        for i in range(self.ROWS):
            y = self.LIST_Y + i * self.ROW_H + self.ROW_H // 2
            img = c.create_image(W // 2, y, image=self.row_imgs["n"])
            dot = c.create_text(self.LIST_X + 22, y, text="", fill=TEXT, font=(FONT_B, 11))
            lab = c.create_text(self.LIST_X + 40, y, anchor="w", text="", fill=TEXT, font=(FONT, 11))
            tag = c.create_text(self.LIST_X + self.LIST_W - 22, y, anchor="e", text="", fill=MUTED, font=(FONT, 9))
            self.rows.append((img, dot, lab, tag))
            for item in (img, dot, lab, tag):
                c.tag_bind(item, "<Button-1>", lambda e, i=i: self.choose(i))
                c.tag_bind(item, "<Enter>", lambda e, i=i: self.set_hover(i))
                c.tag_bind(item, "<Leave>", lambda e: self.set_hover(None))
        c.bind("<MouseWheel>", self.wheel)
        list_bottom = self.LIST_Y + self.ROWS * self.ROW_H
        self.empty = c.create_text(W // 2, self.LIST_Y + 90, text="Лаунчеры не найдены. Выбери папку игры вручную.",
                                   fill=MUTED, font=(FONT, 11), state="hidden")
        self.path_txt = c.create_text(self.LIST_X + 4, list_bottom + 16, anchor="w", text="", fill=DIM, font=(FONT, 9))
        self.other = Button(self, self.LIST_X + self.LIST_W - 70, list_bottom + 16, 140, 30, "Другая папка…", self.pick)

        self.go = Button(self, W // 2, 526, 240, 50, "Установить", self.start, big=True)
        self.status = c.create_text(W // 2, 510, text="", fill=MUTED, font=(FONT, 10), state="hidden")
        self.bar_bg = c.create_rectangle(W // 2 - 220, 532, W // 2 + 220, 534, fill="#2a2a2e", width=0, state="hidden")
        self.bar = c.create_rectangle(W // 2 - 220, 532, W // 2 - 220, 534, fill=TEXT, width=0, state="hidden")
        self.details = c.create_text(W // 2, 540, text="", fill=DIM, font=(FONT, 9), state="hidden")
        c.tag_bind(self.details, "<Button-1>", lambda e: self.show_log())
        self.close = Button(self, W // 2, 526, 200, 46, "Закрыть", self.quit_app, big=True)
        self.close.set(visible=False)
        c.create_text(W // 2, H - 14, text="Minecraft 1.21.1  ·  NeoForge 21.1.264  ·  около 190 модов", fill=DIM, font=(FONT, 9))

        self.log_lines, self.busy = [], False
        # Фоновый поток установки не трогает окно сам: он кладёт действия в очередь, а главный поток их выполняет.
        # Вызов Tk из другого потока приводит к падению «alloc: invalid block».
        self.ui_queue = queue.Queue()
        self.redraw()
        self.animate()
        self.pump()

    # --- оформление окна
    def dark_titlebar(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(0x0d0c0c)), 4)  # цвет заголовка
        except Exception:
            pass

    def quit_app(self):
        """Выход без разборки Tk: окно прячется, процесс завершается сразу.
        Обычный destroy() из обработчика кнопки и удаление картинок при выходе роняли программу («alloc: invalid block»)."""
        if self.busy and not messagebox.askyesno("Anno Mille", "Установка ещё идёт. Прервать и закрыть?"):
            return
        self.withdraw()
        self.after(50, lambda: os._exit(0))

    def ui(self, fn):
        self.ui_queue.put(fn)

    def pump(self):
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.after(40, self.pump)

    def animate(self):
        # Одна и та же картинка перерисовывается на месте: новые PhotoImage каждый кадр сборщик мусора
        # мог удалять из потока установки, а Tk падает, если его трогают не из главного потока.
        self.bg_img.paste(self.bg.next())
        self.after(66, self.animate)

    # --- список профилей
    def redraw(self):
        c = self.canvas
        c.itemconfig(self.empty, state="normal" if not self.folders else "hidden")
        for i, (img, dot, lab, tag) in enumerate(self.rows):
            k = self.offset + i
            visible = k < len(self.folders)
            for item in (img, dot, lab, tag):
                c.itemconfig(item, state="normal" if visible and not self.busy_hidden() else "hidden")
            if not visible:
                continue
            label, path, ok = self.folders[k]
            t, col = tag_of(path, ok)
            key = "s" if k == self.sel else ("h" if i == self.hover_row else "n")
            c.itemconfig(img, image=self.row_imgs[key])
            c.itemconfig(dot, text="◆" if k == self.sel else "◇", fill=TEXT if k == self.sel else DIM)
            c.itemconfig(lab, text=label if len(label) < 58 else label[:56] + "…", fill=TEXT if ok is not False else MUTED)
            c.itemconfig(tag, text=t, fill=col)
        f = self.selected()
        p = f[1] if f else ""
        c.itemconfig(self.path_txt, text=p if len(p) < 62 else "…" + p[-60:])

    def busy_hidden(self):
        return False

    def selected(self):
        return self.folders[self.sel] if self.folders else None

    def choose(self, i):
        if self.busy or self.offset + i >= len(self.folders):
            return
        self.sel = self.offset + i
        self.redraw()

    def set_hover(self, i):
        self.hover_row = i
        self.canvas.config(cursor="hand2" if i is not None else "")
        self.redraw()

    def wheel(self, e):
        if len(self.folders) > self.ROWS:
            self.offset = max(0, min(len(self.folders) - self.ROWS, self.offset + (-1 if e.delta > 0 else 1)))
            self.redraw()

    def pick(self):
        if self.busy:
            return
        p = filedialog.askdirectory(title="Папка игры профиля (там, где mods и config)")
        if p:
            p = os.path.normpath(p)
            self.folders.append(("Выбрано вручную · " + os.path.basename(p), p, suits(profile_info(p))))
            self.sel = len(self.folders) - 1
            self.offset = max(0, len(self.folders) - self.ROWS)
            self.redraw()

    # --- установка
    def write(self, msg):
        def do():
            self.log_lines.append(msg)
            self.canvas.itemconfig(self.status, text=msg if len(msg) < 90 else msg[:88] + "…")
        self.ui(do)

    def progress(self, done, total):
        def do():
            x0 = W // 2 - 220
            self.canvas.coords(self.bar, x0, 532, x0 + 440 * done / max(total, 1), 534)
        self.ui(do)

    def start(self):
        f = self.selected()
        if not f:
            messagebox.showwarning("Anno Mille", "Выбери папку игры.")
            return
        game, ok = f[1], f[2]
        if ok is False:
            v, l = profile_info(game)
            if not messagebox.askyesno("Anno Mille", f"Этот профиль на Minecraft {v} ({l}).\n\nСборке нужен Minecraft 1.21.1 с NeoForge, "
                                                     "иначе игра не запустится. Создай в лаунчере такой профиль и выбери его.\n\nВсё равно установить сюда?"):
                return
        self.busy = True
        self.go.set(visible=False)
        self.other.set(enabled=False)
        c = self.canvas
        for item in (self.status, self.bar_bg, self.bar):
            c.itemconfig(item, state="normal")
        c.itemconfig(self.status, fill=MUTED)
        c.itemconfig(self.details, state="hidden")
        self.progress(0, 1)
        gc.collect()
        gc.disable()      # чтобы сборщик мусора не запускался в потоке установки (см. animate)
        threading.Thread(target=self.work, args=(game,), daemon=True).start()

    def work(self, game):
        try:
            if os.environ.get("ANNO_DEMO"):          # показ вида окна без установки
                import time
                self.write("Скачиваю 199 файлов (уже скачанные пропускаю)...")
                for i in range(0, 200, 5):
                    self.progress(i, 199); time.sleep(0.05)
                if os.environ["ANNO_DEMO"] == "done":
                    self.ui(self.done)
                return
            install.run(game, log=self.write, progress=self.progress)
            self.ui(self.done)
        except Exception as e:
            import socket, urllib.error
            if isinstance(e, (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError)):
                hint = "Не удалось скачать файлы. Проверь интернет и попробуй ещё раз."
            elif isinstance(e, install.GameRunning):
                hint = "Игра сейчас открыта. Закрой Minecraft и нажми «Установить» ещё раз."
            elif isinstance(e, PermissionError):
                hint = "Windows не дала записать файл. Закрой игру и лаунчер и попробуй ещё раз."
            else:
                hint = "Что-то пошло не так. Попробуй ещё раз, а если не выйдет, пришли подробности автору."
            self.write(f"Ошибка: {e}")
            self.ui(lambda: self.failed(hint))

    def done(self):
        gc.enable()
        self.busy = False
        c = self.canvas
        self.progress(1, 1)
        c.itemconfig(self.status, text="Готово. Открой лаунчер, выбери этот профиль и выдели игре 8 ГБ памяти.", fill=TEXT)
        c.itemconfig(self.bar_bg, state="hidden")
        c.itemconfig(self.bar, state="hidden")
        c.coords(self.status, W // 2, 494)
        self.close.set(visible=True)
        self.show_details_link()

    def failed(self, hint):
        gc.enable()
        c = self.canvas
        c.itemconfig(self.status, text=hint, fill=BAD)
        c.itemconfig(self.bar_bg, state="hidden")
        c.itemconfig(self.bar, state="hidden")
        c.coords(self.status, W // 2, 494)
        self.busy = False
        self.other.set(enabled=True)
        self.go.set(text="Попробовать ещё раз", visible=True)
        self.show_details_link()

    def show_details_link(self):
        self.canvas.itemconfig(self.details, text="подробности установки", state="normal")
        self.canvas.coords(self.details, W // 2, 562)

    def show_log(self):
        top = tk.Toplevel(self, bg="#0c0c0d")
        top.title("Anno Mille · подробности")
        top.geometry("720x420")
        t = tk.Text(top, bg="#121214", fg=TEXT, insertbackground=TEXT, borderwidth=0, highlightthickness=0,
                    font=("Consolas", 9), wrap="word", padx=14, pady=12)
        t.pack(fill="both", expand=True)
        t.insert("end", "\n".join(self.log_lines))
        t.config(state="disabled")


if __name__ == "__main__":
    app = App()
    shot = os.environ.get("ANNO_SHOT")          # для проверки вида: снимок окна и выход
    if shot:
        def snap():
            from PIL import ImageGrab
            x, y = app.canvas.winfo_rootx(), app.canvas.winfo_rooty()
            ImageGrab.grab((x, y, x + W, y + H)).save(shot)
            app.destroy()
        if os.environ.get("ANNO_DEMO"):
            app.after(800, app.start)
        app.after(int(os.environ.get("ANNO_SHOT_MS", "2500")), snap)
    target = os.environ.get("ANNO_TARGET")      # проверка: настоящая установка в указанную папку, итог в консоль
    if target:
        app.folders.append(("Проверка", os.path.normpath(target), True))
        app.sel = len(app.folders) - 1
        app.after(800, app.start)
        def finished():
            if app.canvas.itemcget(app.close.img, "state") == "normal" or (not app.busy and app.log_lines):
                print("RESULT:", app.canvas.itemcget(app.status, "text"), flush=True)
                app.close.cmd()                 # как нажатие «Закрыть»
            else:
                app.after(1000, finished)
        app.after(5000, finished)
    app.mainloop()
