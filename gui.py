from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import ImageTk

from iprocess import DEFAULT_IMAGE, render_poster


class MemeEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Cem Yılmaz Miim Editörü")
        self.geometry("1060x720")
        self.minsize(940, 650)
        self.configure(bg="#111827")
        self.image_path = str(DEFAULT_IMAGE)
        self.preview_photo = None
        self.text_var = tk.StringVar(value="Cem Yılmaz hayatını kaybetti.")
        self.tint_var = tk.StringVar(value="#2436B9")
        self.text_glow_color_var = tk.StringVar(value="#55CCFF")
        self.values = {
            "Katman opaklığı": tk.IntVar(value=115), "Parlaklık": tk.IntVar(value=100),
            "Kontrast": tk.IntVar(value=115), "Doygunluk": tk.IntVar(value=35),
            "Bulanıklık": tk.IntVar(value=0), "Keskinlik": tk.IntVar(value=100),
            "Tüm görsel yatay sıkıştırma": tk.IntVar(value=0), "Tüm görsel dikey basıklık": tk.IntVar(value=0),
            "Girdap": tk.IntVar(value=0), "Aşırı parlama": tk.IntVar(value=0),
            "Sepya": tk.IntVar(value=0), "Posterleştirme": tk.IntVar(value=8), "Pikselleştirme": tk.IntVar(value=1),
            "Kenar çizgileri": tk.IntVar(value=0), "Film greni": tk.IntVar(value=0), "RGB kayması": tk.IntVar(value=0),
            "Vinyet": tk.IntVar(value=0), "Tarama çizgileri": tk.IntVar(value=0),
            "Yazı parlaması": tk.IntVar(value=0),
        }
        self.negative_var = tk.BooleanVar(value=False)
        self.emboss_var = tk.BooleanVar(value=False)
        self.mirror_var = tk.BooleanVar(value=False)
        self.text_rgb_var = tk.BooleanVar(value=False)
        self.side_strip_var = tk.BooleanVar(value=False)
        self._build()
        self.after(100, self.refresh_preview)

    def _build(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#111827")
        style.configure("TLabel", background="#111827", foreground="#E5E7EB")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="white")
        style.configure("TButton", font=("Segoe UI", 10))
        sidebar = ttk.Frame(self)
        sidebar.pack(side="left", fill="y")
        self.controls_canvas = tk.Canvas(sidebar, background="#111827", highlightthickness=0, width=350)
        scrollbar = ttk.Scrollbar(sidebar, orient="vertical", command=self.controls_canvas.yview)
        self.controls_canvas.configure(yscrollcommand=scrollbar.set)
        self.controls_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        controls = ttk.Frame(self.controls_canvas, padding=22)
        self.controls_window = self.controls_canvas.create_window((0, 0), window=controls, anchor="nw")
        controls.bind("<Configure>", self._update_scroll_region)
        self.controls_canvas.bind("<Configure>", self._fit_controls_width)
        # Mouse-wheel scrolling works while the cursor is over any control.
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        ttk.Label(controls, text="Miim Editörü", style="Title.TLabel").pack(anchor="w")
        ttk.Label(controls, text="Fotoğrafı, yazıyı ve renk efektini düzenle.").pack(anchor="w", pady=(2, 18))
        ttk.Button(controls, text="Fotoğraf seç", command=self.choose_image).pack(fill="x")
        self.file_label = ttk.Label(controls, text="Varsayılan Cem Yılmaz görseli", wraplength=280)
        self.file_label.pack(anchor="w", pady=(6, 18))
        ttk.Label(controls, text="Alt yazı").pack(anchor="w")
        entry = ttk.Entry(controls, textvariable=self.text_var, width=34)
        entry.pack(fill="x", pady=(4, 14))
        entry.bind("<KeyRelease>", lambda _event: self.refresh_preview())
        color_row = ttk.Frame(controls)
        color_row.pack(fill="x", pady=(0, 10))
        ttk.Label(color_row, text="Tint rengi").pack(side="left")
        ttk.Button(color_row, text="Renk seç", command=self.choose_color).pack(side="right")
        ttk.Label(controls, textvariable=self.tint_var).pack(anchor="w", pady=(0, 12))
        text_color_row = ttk.Frame(controls)
        text_color_row.pack(fill="x", pady=(0, 4))
        ttk.Label(text_color_row, text="Yazı parlaması rengi").pack(side="left")
        ttk.Button(text_color_row, text="Renk seç", command=self.choose_text_glow_color).pack(side="right")
        ttk.Label(controls, textvariable=self.text_glow_color_var).pack(anchor="w", pady=(0, 8))
        ranges = {
            "Katman opaklığı": (0, 220), "Parlaklık": (30, 180), "Kontrast": (30, 220),
            "Doygunluk": (0, 180), "Bulanıklık": (0, 12), "Keskinlik": (0, 250),
            "Tüm görsel yatay sıkıştırma": (-70, 100), "Tüm görsel dikey basıklık": (-70, 100),
            "Girdap": (-180, 180), "Aşırı parlama": (0, 200),
            "Sepya": (0, 100), "Posterleştirme": (1, 8), "Pikselleştirme": (1, 30), "Kenar çizgileri": (0, 100),
            "Film greni": (0, 100), "RGB kayması": (0, 30), "Vinyet": (0, 100), "Tarama çizgileri": (0, 100),
            "Yazı parlaması": (0, 100),
        }
        for label, variable in self.values.items():
            row = ttk.Frame(controls)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label).pack(side="left")
            ttk.Label(row, textvariable=variable, width=4, anchor="e").pack(side="right")
            ttk.Scale(controls, from_=ranges[label][0], to=ranges[label][1], variable=variable, command=lambda _value: self.refresh_preview()).pack(fill="x", pady=(0, 7))
        ttk.Checkbutton(controls, text="Negatif renk", variable=self.negative_var, command=self.refresh_preview).pack(anchor="w", pady=(5, 0))
        ttk.Checkbutton(controls, text="Kabartma", variable=self.emboss_var, command=self.refresh_preview).pack(anchor="w", pady=(5, 0))
        ttk.Checkbutton(controls, text="Yatay ayna", variable=self.mirror_var, command=self.refresh_preview).pack(anchor="w", pady=(5, 0))
        ttk.Checkbutton(controls, text="Yazıda RGB ayrışması", variable=self.text_rgb_var, command=self.refresh_preview).pack(anchor="w", pady=(5, 0))
        ttk.Checkbutton(controls, text="Solda BPT Haber şeridi", variable=self.side_strip_var, command=self.refresh_preview).pack(anchor="w", pady=(5, 0))
        buttons = ttk.Frame(controls)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Sıfırla", command=self.reset).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="PNG kaydet", command=self.save).pack(side="left", fill="x", expand=True, padx=(8, 0))
        preview_area = ttk.Frame(self, padding=(20, 20, 28, 20))
        preview_area.pack(side="left", fill="both", expand=True)
        ttk.Label(preview_area, text="Canlı önizleme", style="Title.TLabel").pack(anchor="w", pady=(0, 12))
        self.preview = ttk.Label(preview_area, anchor="center")
        self.preview.pack(fill="both", expand=True)

    def _update_scroll_region(self, _event=None) -> None:
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def _fit_controls_width(self, event) -> None:
        self.controls_canvas.itemconfigure(self.controls_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        if self.winfo_containing(event.x_root, event.y_root) in (None, self.preview):
            return
        self.controls_canvas.yview_scroll(-int(event.delta / 120), "units")

    def current_image(self):
        return render_poster(
            self.image_path, self.text_var.get(), self.tint_var.get(), self.values["Katman opaklığı"].get(),
            self.values["Parlaklık"].get(), self.values["Kontrast"].get(), self.values["Doygunluk"].get(),
            self.values["Bulanıklık"].get(), self.values["Keskinlik"].get(),
            self.values["Tüm görsel yatay sıkıştırma"].get(), self.values["Tüm görsel dikey basıklık"].get(),
            self.values["Girdap"].get(), self.negative_var.get(), self.values["Aşırı parlama"].get(),
            self.values["Sepya"].get(), self.values["Posterleştirme"].get(), self.values["Pikselleştirme"].get(),
            self.values["Kenar çizgileri"].get(), self.values["Film greni"].get(), self.values["RGB kayması"].get(),
            self.values["Vinyet"].get(), self.values["Tarama çizgileri"].get(), self.emboss_var.get(), self.mirror_var.get(),
            self.values["Yazı parlaması"].get(), self.text_glow_color_var.get(), self.text_rgb_var.get(),
            self.side_strip_var.get(),
        )

    def refresh_preview(self) -> None:
        try:
            image = self.current_image()
            image.thumbnail((470, 610))
            self.preview_photo = ImageTk.PhotoImage(image)
            self.preview.configure(image=self.preview_photo, text="")
        except Exception as error:
            self.preview.configure(image="", text=f"Önizleme oluşturulamadı:\n{error}")

    def choose_image(self) -> None:
        path = filedialog.askopenfilename(title="Bir fotoğraf seç", filetypes=[("Görseller", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Tüm dosyalar", "*.*")])
        if path:
            self.image_path = path
            self.file_label.configure(text=path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
            self.refresh_preview()

    def choose_color(self) -> None:
        color = colorchooser.askcolor(color=self.tint_var.get(), title="Tint rengini seç")[1]
        if color:
            self.tint_var.set(color.upper())
            self.refresh_preview()

    def choose_text_glow_color(self) -> None:
        color = colorchooser.askcolor(color=self.text_glow_color_var.get(), title="Yazı parlama rengini seç")[1]
        if color:
            self.text_glow_color_var.set(color.upper())
            self.refresh_preview()

    def reset(self) -> None:
        self.text_var.set("Cem Yılmaz hayatını kaybetti.")
        self.tint_var.set("#2436B9")
        for variable, value in zip(self.values.values(), (115, 100, 115, 35, 0, 100, 0, 0, 0, 0, 0, 8, 1, 0, 0, 0, 0, 0, 0)):
            variable.set(value)
        self.negative_var.set(False)
        self.emboss_var.set(False)
        self.mirror_var.set(False)
        self.text_rgb_var.set(False)
        self.side_strip_var.set(False)
        self.text_glow_color_var.set("#55CCFF")
        self.refresh_preview()

    def save(self) -> None:
        path = filedialog.asksaveasfilename(title="Meme'i kaydet", defaultextension=".png", initialfile="cem-yilmaz-meme.png", filetypes=[("PNG görseli", "*.png")])
        if not path:
            return
        try:
            self.current_image().save(path, "PNG")
            messagebox.showinfo("Kaydedildi", f"Görsel kaydedildi:\n{path}")
        except Exception as error:
            messagebox.showerror("Kaydedilemedi", str(error))


def run() -> None:
    MemeEditor().mainloop()
