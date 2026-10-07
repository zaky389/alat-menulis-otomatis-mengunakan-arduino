"""
GUI Aplikasi Robot Penulis AI
===============================
Antarmuka grafis menggunakan Tkinter (built-in Python, tanpa install tambahan).
Semua fitur bisa diakses via GUI yang user-friendly.
Bekerja 100% offline.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os

from writing_robot import WritingRobot
from config import PAPER_SIZES, SPEED_PRESETS


class WritingRobotGUI:
    """Aplikasi GUI untuk Robot Penulis AI."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Robot Penulis AI - Controller")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Warna tema
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent = "#89b4fa"
        self.success = "#a6e3a1"
        self.warning = "#f9e2af"
        self.error = "#f38ba8"
        self.surface = "#313244"

        self.root.configure(bg=self.bg_color)

        # Robot instance
        self.robot = WritingRobot(simulate=True)
        self.is_writing = False

        self._build_ui()

    def _build_ui(self):
        """Bangun semua elemen UI."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles
        style.configure("Title.TLabel",
                         background=self.bg_color,
                         foreground=self.accent,
                         font=("Segoe UI", 16, "bold"))
        style.configure("Header.TLabel",
                         background=self.bg_color,
                         foreground=self.fg_color,
                         font=("Segoe UI", 11, "bold"))
        style.configure("Info.TLabel",
                         background=self.bg_color,
                         foreground=self.fg_color,
                         font=("Segoe UI", 9))
        style.configure("Custom.TFrame",
                         background=self.bg_color)
        style.configure("Surface.TFrame",
                         background=self.surface)
        style.configure("Accent.TButton",
                         font=("Segoe UI", 10, "bold"))

        # === HEADER ===
        header_frame = ttk.Frame(self.root, style="Custom.TFrame")
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        ttk.Label(header_frame,
                  text="🤖 Robot Penulis AI",
                  style="Title.TLabel").pack(side=tk.LEFT)

        self.status_label = ttk.Label(header_frame,
                                       text="⚪ Belum Terhubung",
                                       style="Info.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        # === MAIN CONTENT ===
        main_frame = ttk.Frame(self.root, style="Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # --- Left Panel: Settings ---
        left_frame = ttk.Frame(main_frame, style="Custom.TFrame", width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # Koneksi
        conn_frame = ttk.LabelFrame(left_frame, text="📡 Koneksi",
                                     padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 8))

        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill=tk.X, pady=2)
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="COM3")
        self.port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.simulate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(conn_frame, text="Mode Simulasi",
                         variable=self.simulate_var).pack(anchor=tk.W, pady=2)

        self.connect_btn = ttk.Button(conn_frame, text="🔌 Hubungkan",
                                       command=self._connect)
        self.connect_btn.pack(fill=tk.X, pady=5)

        # Ukuran Kertas
        paper_frame = ttk.LabelFrame(left_frame, text="📄 Ukuran Kertas",
                                      padding=10)
        paper_frame.pack(fill=tk.X, pady=(0, 8))

        self.paper_var = tk.StringVar(value="A4")
        paper_combo = ttk.Combobox(paper_frame,
                                    textvariable=self.paper_var,
                                    values=list(PAPER_SIZES.keys()),
                                    state="readonly", width=18)
        paper_combo.pack(fill=tk.X, pady=2)
        paper_combo.bind("<<ComboboxSelected>>", self._on_paper_change)

        # Custom size
        custom_frame = ttk.Frame(paper_frame)
        custom_frame.pack(fill=tk.X, pady=5)
        ttk.Label(custom_frame, text="Custom (mm):").pack(anchor=tk.W)

        size_frame = ttk.Frame(custom_frame)
        size_frame.pack(fill=tk.X)
        ttk.Label(size_frame, text="W:").pack(side=tk.LEFT)
        self.custom_w = tk.StringVar(value="200")
        ttk.Entry(size_frame, textvariable=self.custom_w, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(size_frame, text="H:").pack(side=tk.LEFT, padx=(5, 0))
        self.custom_h = tk.StringVar(value="250")
        ttk.Entry(size_frame, textvariable=self.custom_h, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(size_frame, text="Set", width=4,
                    command=self._set_custom_paper).pack(side=tk.LEFT, padx=5)

        self.paper_info = ttk.Label(paper_frame, text="210 x 297 mm",
                                     style="Info.TLabel")
        self.paper_info.pack(anchor=tk.W)

        # Kecepatan
        speed_frame = ttk.LabelFrame(left_frame, text="⚡ Kecepatan",
                                      padding=10)
        speed_frame.pack(fill=tk.X, pady=(0, 8))

        self.speed_var = tk.StringVar(value="normal")
        speed_combo = ttk.Combobox(speed_frame,
                                    textvariable=self.speed_var,
                                    values=list(SPEED_PRESETS.keys()),
                                    state="readonly", width=18)
        speed_combo.pack(fill=tk.X, pady=2)
        speed_combo.bind("<<ComboboxSelected>>", self._on_speed_change)

        # Speed slider
        ttk.Label(speed_frame, text="Custom (mm/s):").pack(anchor=tk.W, pady=(5, 0))
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=60,
                                     orient=tk.HORIZONTAL, length=200,
                                     bg=self.surface, fg=self.fg_color,
                                     highlightthickness=0)
        self.speed_scale.set(20)
        self.speed_scale.pack(fill=tk.X)

        # Font Size
        font_frame = ttk.LabelFrame(left_frame, text="✏️ Ukuran Huruf",
                                     padding=10)
        font_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(font_frame, text="Tinggi huruf (mm):").pack(anchor=tk.W)
        self.font_scale = tk.Scale(font_frame, from_=2, to=10,
                                    orient=tk.HORIZONTAL, resolution=0.5,
                                    length=200,
                                    bg=self.surface, fg=self.fg_color,
                                    highlightthickness=0)
        self.font_scale.set(4.0)
        self.font_scale.pack(fill=tk.X)

        # Margin
        margin_frame = ttk.LabelFrame(left_frame, text="📐 Margin (mm)",
                                       padding=10)
        margin_frame.pack(fill=tk.X, pady=(0, 8))

        margins = [("Atas", "15"), ("Bawah", "15"), ("Kiri", "15"), ("Kanan", "15")]
        self.margin_vars = {}
        for label, default in margins:
            row = ttk.Frame(margin_frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=f"{label}:", width=6).pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            ttk.Entry(row, textvariable=var, width=6).pack(side=tk.LEFT, padx=5)
            self.margin_vars[label.lower()] = var

        # --- Right Panel: Text & Actions ---
        right_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Text Input
        text_frame = ttk.LabelFrame(right_frame, text="📝 Teks yang Akan Ditulis",
                                     padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.text_input = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD, height=12,
            font=("Consolas", 11),
            bg=self.surface, fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.accent
        )
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.insert(tk.END, "Ketik teks Anda di sini...\n\n"
                               "Robot akan menulis teks ini di atas kertas.\n"
                               "Mendukung huruf besar, kecil, angka, dan tanda baca.")

        # File load button
        file_frame = ttk.Frame(text_frame)
        file_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(file_frame, text="📂 Muat dari File",
                    command=self._load_file).pack(side=tk.LEFT)
        self.char_count = ttk.Label(file_frame, text="Karakter: 0",
                                     style="Info.TLabel")
        self.char_count.pack(side=tk.RIGHT)

        # Action Buttons
        action_frame = ttk.Frame(right_frame, style="Custom.TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 8))

        self.write_btn = ttk.Button(action_frame, text="✍️ MULAI MENULIS",
                                     command=self._start_writing,
                                     style="Accent.TButton")
        self.write_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.continuous_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(action_frame, text="Tanpa Batas Halaman",
                         variable=self.continuous_var).pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="👁️ Preview SVG",
                    command=self._preview).pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="⏹️ Stop",
                    command=self._stop_writing).pack(side=tk.RIGHT)

        # Log Output
        log_frame = ttk.LabelFrame(right_frame, text="📋 Log",
                                    padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_output = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=8,
            font=("Consolas", 9),
            bg="#11111b", fg="#a6adc8",
            insertbackground="#a6adc8",
            state=tk.DISABLED
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.text_input.bind("<KeyRelease>", self._update_char_count)
        self._update_char_count()

    def _log(self, message):
        """Tulis pesan ke log panel."""
        self.log_output.config(state=tk.NORMAL)
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.log_output.config(state=tk.DISABLED)

    def _connect(self):
        """Hubungkan ke robot."""
        port = self.port_var.get()
        simulate = self.simulate_var.get()

        self.robot = WritingRobot(port=port, simulate=simulate)
        success = self.robot.connect()

        if self.robot.is_connected:
            self.status_label.config(text="🟢 Terhubung" +
                                     (" (Simulasi)" if simulate else ""))
            self._log(f"✅ Terhubung ke {'simulasi' if simulate else port}")
            self.connect_btn.config(text="🔌 Terhubung ✓")
        else:
            self.status_label.config(text="🔴 Gagal")
            self._log(f"❌ Gagal terhubung ke {port}")

    def _on_paper_change(self, event=None):
        """Handler perubahan ukuran kertas."""
        name = self.paper_var.get()
        if name in PAPER_SIZES:
            w, h = PAPER_SIZES[name]
            self.robot.set_paper_size(name)
            self.paper_info.config(text=f"{w} x {h} mm")
            self._log(f"📄 Kertas: {name} ({w}x{h}mm)")

    def _set_custom_paper(self):
        """Set ukuran kertas custom."""
        try:
            w = float(self.custom_w.get())
            h = float(self.custom_h.get())
            self.robot.set_paper_size(width=w, height=h)
            self.paper_info.config(text=f"{w} x {h} mm (Custom)")
            self._log(f"📄 Kertas custom: {w}x{h}mm")
        except ValueError:
            messagebox.showerror("Error", "Masukkan angka yang valid!")

    def _on_speed_change(self, event=None):
        """Handler perubahan kecepatan."""
        name = self.speed_var.get()
        self.robot.set_speed(name)
        self.speed_scale.set(self.robot.writing_speed)
        self._log(f"⚡ Kecepatan: {name} ({self.robot.writing_speed} mm/s)")

    def _load_file(self):
        """Muat teks dari file."""
        filepath = filedialog.askopenfilename(
            title="Pilih File Teks",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert(tk.END, content)
                self._log(f"📂 File dimuat: {os.path.basename(filepath)}")
                self._update_char_count()
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membaca file:\n{e}")

    def _update_char_count(self, event=None):
        """Update jumlah karakter."""
        text = self.text_input.get("1.0", tk.END).strip()
        self.char_count.config(text=f"Karakter: {len(text)}")

    def _apply_settings(self):
        """Terapkan semua pengaturan ke robot."""
        # Font size
        self.robot.set_font_size(self.font_scale.get())

        # Speed from slider if different from preset
        custom_speed = self.speed_scale.get()
        self.robot.set_speed(speed_mm_s=custom_speed)

        # Margins
        try:
            self.robot.set_margins(
                top=float(self.margin_vars['atas'].get()),
                bottom=float(self.margin_vars['bawah'].get()),
                left=float(self.margin_vars['kiri'].get()),
                right=float(self.margin_vars['kanan'].get()),
            )
        except ValueError:
            self._log("⚠️ Margin tidak valid, menggunakan default")

    def _start_writing(self):
        """Mulai menulis di thread terpisah."""
        if not self.robot.is_connected:
            messagebox.showwarning("Peringatan", "Robot belum terhubung!\nKlik 'Hubungkan' terlebih dahulu.")
            return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Peringatan", "Teks kosong!")
            return

        self._apply_settings()
        self.is_writing = True
        self.write_btn.config(state=tk.DISABLED)
        self._log(f"\n{'='*40}")
        self._log(f"✍️ Mulai menulis... ({len(text)} karakter)")

        # Jalankan di thread agar GUI tidak freeze
        thread = threading.Thread(
            target=self._writing_thread,
            args=(text,),
            daemon=True
        )
        thread.start()

    def _writing_thread(self, text):
        """Thread untuk proses menulis."""
        try:
            continuous = self.continuous_var.get()
            self.robot.write_text(text, continuous=continuous)
            self._log("✅ Selesai menulis!")
        except Exception as e:
            self._log(f"❌ Error: {e}")
        finally:
            self.is_writing = False
            self.root.after(0, lambda: self.write_btn.config(state=tk.NORMAL))

    def _stop_writing(self):
        """Hentikan proses menulis."""
        if self.is_writing:
            self.is_writing = False
            self.robot.pen_up()
            self.robot.move_to(0, 0)
            self._log("⏹️ Proses dihentikan")
            self.write_btn.config(state=tk.NORMAL)

    def _preview(self):
        """Buat preview SVG."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Peringatan", "Teks kosong!")
            return

        self._apply_settings()

        try:
            filepath = self.robot.preview_text(text, "preview_tulisan.svg")
            self._log(f"👁️ Preview disimpan: {filepath}")
            messagebox.showinfo("Preview",
                                f"Preview SVG disimpan!\n\n{filepath}\n\n"
                                "Buka file ini di browser untuk melihat hasil tulisan.")
        except Exception as e:
            self._log(f"❌ Error preview: {e}")
            messagebox.showerror("Error", f"Gagal membuat preview:\n{e}")

    def run(self):
        """Jalankan aplikasi."""
        self.root.mainloop()


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    app = WritingRobotGUI()
    app.run()
