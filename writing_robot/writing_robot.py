"""
Robot Penulis AI - Modul Utama
================================
Mengontrol robot pen plotter via serial (Arduino).
Mendukung:
- Menulis tanpa batas (continuous writing)
- Kecepatan tulisan bisa diatur
- Custom teks
- Berbagai ukuran kertas/buku
- 100% offline, berjalan lokal
"""

import time
import math
import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[PERINGATAN] pyserial belum terinstall.")
    print("Install dengan: pip install pyserial")
    print("Mode simulasi akan digunakan.\n")

from config import (
    SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT,
    ROBOT_MAX_X, ROBOT_MAX_Y,
    PAPER_SIZES, DEFAULT_PAPER_SIZE,
    MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT,
    FONT_SIZE, LETTER_SPACING, WORD_SPACING, LINE_SPACING,
    SPEED_PRESETS, DEFAULT_SPEED, TRAVEL_SPEED,
    PEN_UP_ANGLE, PEN_DOWN_ANGLE, PEN_DELAY,
    STEPS_PER_MM,
)
from hershey_font import get_text_strokes


class WritingRobot:
    """
    Kelas utama untuk mengontrol robot penulis.

    Fitur:
        - Koneksi serial ke Arduino
        - Konversi teks → path tulisan (offline, tanpa internet)
        - Pengaturan kecepatan menulis
        - Pengaturan ukuran kertas / buku
        - Menulis tanpa batas (multi-halaman)
        - Mode simulasi (tanpa hardware)
    """

    def __init__(self, port=None, simulate=False):
        """
        Inisialisasi robot penulis.

        Args:
            port: Port serial Arduino (misal 'COM3' atau '/dev/ttyUSB0')
            simulate: Jika True, jalankan tanpa hardware (mode simulasi)
        """
        self.port = port or SERIAL_PORT
        self.simulate = simulate or not SERIAL_AVAILABLE
        self.serial_conn = None

        # State
        self.current_x = 0.0
        self.current_y = 0.0
        self.pen_is_down = False
        self.is_connected = False

        # Pengaturan
        self.paper_width = PAPER_SIZES[DEFAULT_PAPER_SIZE][0]
        self.paper_height = PAPER_SIZES[DEFAULT_PAPER_SIZE][1]
        self.paper_name = DEFAULT_PAPER_SIZE
        self.font_size = FONT_SIZE
        self.letter_spacing = LETTER_SPACING
        self.word_spacing = WORD_SPACING
        self.line_spacing = LINE_SPACING
        self.writing_speed = SPEED_PRESETS[DEFAULT_SPEED]  # mm/s
        self.travel_speed = TRAVEL_SPEED

        # Margin
        self.margin_top = MARGIN_TOP
        self.margin_bottom = MARGIN_BOTTOM
        self.margin_left = MARGIN_LEFT
        self.margin_right = MARGIN_RIGHT

        # Area tulisan efektif
        self._update_writing_area()

        # Statistik
        self.total_distance = 0.0
        self.total_characters = 0
        self.pages_written = 0

        # Log file
        self.log_file = None

    def _update_writing_area(self):
        """Hitung area tulisan berdasarkan ukuran kertas dan margin."""
        self.write_x_start = self.margin_left
        self.write_y_start = self.margin_top
        self.write_x_end = self.paper_width - self.margin_right
        self.write_y_end = self.paper_height - self.margin_bottom
        self.write_width = self.write_x_end - self.write_x_start
        self.write_height = self.write_y_end - self.write_y_start

    # ================================================================
    # KONEKSI
    # ================================================================

    def connect(self):
        """Hubungkan ke Arduino via serial."""
        if self.simulate:
            print("[SIMULASI] Mode simulasi aktif - tidak memerlukan hardware")
            self.is_connected = True
            return True

        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=SERIAL_BAUDRATE,
                timeout=SERIAL_TIMEOUT
            )
            time.sleep(2)  # Tunggu Arduino reset

            # Baca pesan selamat datang dari Arduino
            welcome = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            if welcome:
                print(f"[ARDUINO] {welcome}")

            # Kirim perintah home
            self._send_command("G28")  # Home all axes
            self.current_x = 0
            self.current_y = 0
            self.is_connected = True
            print(f"[OK] Terhubung ke Arduino di {self.port}")
            return True

        except Exception as e:
            print(f"[ERROR] Gagal terhubung: {e}")
            print("[INFO] Beralih ke mode simulasi")
            self.simulate = True
            self.is_connected = True
            return False

    def disconnect(self):
        """Putuskan koneksi dari Arduino."""
        if self.serial_conn and self.serial_conn.is_open:
            self.pen_up()
            self._send_command("G28")  # Home
            self.serial_conn.close()
            print("[OK] Koneksi diputus")
        self.is_connected = False

    def _send_command(self, cmd):
        """Kirim G-code command ke Arduino."""
        if self.simulate:
            return "ok"

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(f"{cmd}\n".encode())
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            return response
        return ""

    # ================================================================
    # GERAKAN DASAR
    # ================================================================

    def pen_up(self):
        """Angkat pena dari kertas."""
        if not self.pen_is_down:
            return
        cmd = f"M3 S{PEN_UP_ANGLE}"
        self._send_command(cmd)
        time.sleep(PEN_DELAY / 1000.0)
        self.pen_is_down = False

    def pen_down(self):
        """Turunkan pena ke kertas."""
        if self.pen_is_down:
            return
        cmd = f"M3 S{PEN_DOWN_ANGLE}"
        self._send_command(cmd)
        time.sleep(PEN_DELAY / 1000.0)
        self.pen_is_down = True

    def move_to(self, x, y, speed=None):
        """
        Gerakkan pena ke posisi (x, y) tanpa menulis.

        Args:
            x: Posisi X (mm)
            y: Posisi Y (mm)
            speed: Kecepatan gerakan (mm/menit), None = travel speed
        """
        self.pen_up()
        feed = speed or (self.travel_speed * 60)  # Convert mm/s ke mm/min
        cmd = f"G0 X{x:.3f} Y{y:.3f} F{feed:.0f}"
        self._send_command(cmd)

        dist = math.sqrt((x - self.current_x)**2 + (y - self.current_y)**2)
        if not self.simulate:
            # Estimasi waktu tunggu
            time_needed = dist / self.travel_speed
            time.sleep(max(time_needed, 0.01))

        self.total_distance += dist
        self.current_x = x
        self.current_y = y

    def draw_to(self, x, y, speed=None):
        """
        Gambar garis ke posisi (x, y).

        Args:
            x: Posisi X target (mm)
            y: Posisi Y target (mm)
            speed: Kecepatan menulis (mm/menit), None = writing speed
        """
        if not self.pen_is_down:
            self.pen_down()

        feed = speed or (self.writing_speed * 60)  # Convert mm/s ke mm/min
        cmd = f"G1 X{x:.3f} Y{y:.3f} F{feed:.0f}"
        self._send_command(cmd)

        dist = math.sqrt((x - self.current_x)**2 + (y - self.current_y)**2)
        if not self.simulate:
            time_needed = dist / self.writing_speed
            time.sleep(max(time_needed, 0.01))

        self.total_distance += dist
        self.current_x = x
        self.current_y = y

    # ================================================================
    # PENGATURAN
    # ================================================================

    def set_paper_size(self, paper_name=None, width=None, height=None):
        """
        Atur ukuran kertas / buku.

        Args:
            paper_name: Nama preset ('A4', 'A5', 'Buku Tulis', dll.)
            width: Lebar custom (mm)
            height: Tinggi custom (mm)
        """
        if paper_name and paper_name in PAPER_SIZES:
            self.paper_width, self.paper_height = PAPER_SIZES[paper_name]
            self.paper_name = paper_name
        elif width and height:
            self.paper_width = width
            self.paper_height = height
            self.paper_name = f"Custom ({width}x{height}mm)"
        else:
            print(f"[ERROR] Ukuran kertas tidak valid")
            print(f"Pilihan: {', '.join(PAPER_SIZES.keys())}")
            return

        # Validasi bahwa ukuran kertas tidak melebihi area kerja robot
        if self.paper_width > ROBOT_MAX_X:
            print(f"[PERINGATAN] Lebar kertas ({self.paper_width}mm) melebihi area kerja robot ({ROBOT_MAX_X}mm)")
            print(f"             Lebar akan dibatasi ke {ROBOT_MAX_X}mm")
            self.paper_width = ROBOT_MAX_X
        if self.paper_height > ROBOT_MAX_Y:
            print(f"[PERINGATAN] Tinggi kertas ({self.paper_height}mm) melebihi area kerja robot ({ROBOT_MAX_Y}mm)")
            print(f"             Tinggi akan dibatasi ke {ROBOT_MAX_Y}mm")
            self.paper_height = ROBOT_MAX_Y

        self._update_writing_area()
        print(f"[OK] Ukuran kertas: {self.paper_name} ({self.paper_width}x{self.paper_height}mm)")
        print(f"     Area tulis: {self.write_width:.1f}x{self.write_height:.1f}mm")

    def set_speed(self, speed_name=None, speed_mm_s=None):
        """
        Atur kecepatan menulis.

        Args:
            speed_name: Nama preset ('sangat_lambat', 'lambat', 'normal', 'cepat', 'sangat_cepat')
            speed_mm_s: Kecepatan custom dalam mm/detik
        """
        if speed_name and speed_name in SPEED_PRESETS:
            self.writing_speed = SPEED_PRESETS[speed_name]
            print(f"[OK] Kecepatan: {speed_name} ({self.writing_speed} mm/s)")
        elif speed_mm_s is not None:
            self.writing_speed = max(1.0, min(60.0, speed_mm_s))
            print(f"[OK] Kecepatan: {self.writing_speed} mm/s")
        else:
            print(f"[ERROR] Kecepatan tidak valid")
            print(f"Preset: {', '.join(SPEED_PRESETS.keys())}")
            print(f"Atau masukkan angka (1.0 - 60.0 mm/s)")

    def set_font_size(self, size_mm):
        """
        Atur ukuran huruf.

        Args:
            size_mm: Tinggi huruf dalam milimeter (2.0 - 10.0)
        """
        self.font_size = max(2.0, min(10.0, size_mm))
        # Sesuaikan spacing secara proporsional
        ratio = self.font_size / 4.0
        self.letter_spacing = LETTER_SPACING * ratio
        self.word_spacing = WORD_SPACING * ratio
        self.line_spacing = LINE_SPACING * ratio
        print(f"[OK] Ukuran huruf: {self.font_size}mm")

    def set_margins(self, top=None, bottom=None, left=None, right=None):
        """Atur margin tulisan dalam mm."""
        if top is not None:
            self.margin_top = top
        if bottom is not None:
            self.margin_bottom = bottom
        if left is not None:
            self.margin_left = left
        if right is not None:
            self.margin_right = right
        self._update_writing_area()
        print(f"[OK] Margin: atas={self.margin_top} bawah={self.margin_bottom} "
              f"kiri={self.margin_left} kanan={self.margin_right}mm")

    # ================================================================
    # MENULIS TEKS
    # ================================================================

    def write_text(self, text, continuous=False):
        """
        Tulis teks pada kertas.

        Args:
            text: Teks yang akan ditulis
            continuous: Jika True, tulis tanpa batas (multi-halaman)

        Fitur:
            - Otomatis word-wrap sesuai ukuran kertas
            - Pindah halaman otomatis jika continuous=True
            - Bekerja 100% offline
        """
        if not self.is_connected:
            print("[ERROR] Robot belum terhubung! Panggil connect() terlebih dahulu")
            return

        print(f"\n{'='*50}")
        print(f"MULAI MENULIS")
        print(f"{'='*50}")
        print(f"Teks: {text[:80]}{'...' if len(text) > 80 else ''}")
        print(f"Kertas: {self.paper_name}")
        print(f"Kecepatan: {self.writing_speed} mm/s")
        print(f"Ukuran huruf: {self.font_size}mm")
        print(f"{'='*50}\n")

        start_time = time.time()

        # Konversi teks ke stroke paths
        all_strokes = get_text_strokes(
            text=text,
            font_size=self.font_size,
            letter_spacing=self.letter_spacing,
            word_spacing=self.word_spacing,
            line_spacing=self.line_spacing,
            max_width=self.write_width,
            x_start=self.write_x_start,
            y_start=self.write_y_start
        )

        if not all_strokes:
            print("[PERINGATAN] Tidak ada yang perlu ditulis")
            return

        # Pisahkan strokes per halaman
        page_strokes = self._split_into_pages(all_strokes)

        total_pages = len(page_strokes)
        print(f"[INFO] Total halaman: {total_pages}")

        for page_num, strokes in enumerate(page_strokes, 1):
            if not continuous and page_num > 1:
                print(f"\n[INFO] Halaman berikutnya tersedia. Gunakan continuous=True untuk menulis semua.")
                break

            print(f"\n--- Halaman {page_num}/{total_pages} ---")

            if page_num > 1:
                # Minta user mengganti kertas
                self.pen_up()
                self.move_to(0, 0)
                print("\n[AKSI] Ganti kertas!")
                input("         Tekan ENTER setelah kertas baru dipasang...")

            # Tulis semua stroke di halaman ini
            self._execute_strokes(strokes)
            self.pages_written += 1

        # Selesai
        self.pen_up()
        self.move_to(0, 0)

        elapsed = time.time() - start_time
        self.total_characters += len(text)

        print(f"\n{'='*50}")
        print(f"SELESAI MENULIS")
        print(f"{'='*50}")
        print(f"Karakter ditulis: {len(text)}")
        print(f"Halaman: {min(page_num, total_pages)}")
        print(f"Jarak total pena: {self.total_distance:.1f}mm")
        print(f"Waktu: {elapsed:.1f} detik")
        print(f"{'='*50}\n")

    def write_unlimited(self, text):
        """
        Tulis teks tanpa batas halaman (continuous mode).
        Robot akan meminta ganti kertas otomatis saat halaman habis.

        Args:
            text: Teks yang akan ditulis (bisa sangat panjang)
        """
        self.write_text(text, continuous=True)

    def write_from_file(self, filepath, continuous=True):
        """
        Tulis teks dari file.

        Args:
            filepath: Path ke file teks
            continuous: Menulis tanpa batas halaman
        """
        if not os.path.exists(filepath):
            print(f"[ERROR] File tidak ditemukan: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"[INFO] Membaca file: {filepath}")
        print(f"[INFO] Panjang teks: {len(text)} karakter")
        self.write_text(text, continuous=continuous)

    def _split_into_pages(self, strokes):
        """Pisahkan strokes ke halaman berdasarkan batas area kertas."""
        pages = []
        current_page = []
        page_y_limit = self.write_y_end

        for stroke in strokes:
            # Cek apakah stroke melampaui halaman
            max_y_in_stroke = max(y for _, y in stroke)

            if max_y_in_stroke > page_y_limit and current_page:
                pages.append(current_page)
                current_page = []

                # Offset stroke ke halaman baru (reset Y)
                y_offset = max_y_in_stroke - self.write_y_start
                # Perbaiki: kurangi semua Y dengan offset
                adjusted_stroke = [
                    (x, y - (page_y_limit - self.write_y_start))
                    for x, y in stroke
                ]
                current_page.append(adjusted_stroke)
            else:
                current_page.append(stroke)

        if current_page:
            pages.append(current_page)

        # Jika tidak ada pemisahan, return semua sebagai 1 halaman
        if not pages:
            pages = [strokes]

        return pages

    def _execute_strokes(self, strokes):
        """Eksekusi sekumpulan strokes (angkat pena antar stroke)."""
        for i, stroke in enumerate(strokes):
            if len(stroke) < 2:
                continue

            # Pindah ke titik awal stroke (pen up)
            first_x, first_y = stroke[0]
            self.move_to(first_x, first_y)

            # Tulis stroke (pen down)
            self.pen_down()
            for x, y in stroke[1:]:
                self.draw_to(x, y)

            # Angkat pen setelah stroke selesai
            self.pen_up()

            # Progress
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(strokes)} strokes")

    # ================================================================
    # PREVIEW & SIMULASI
    # ================================================================

    def preview_text(self, text, output_file="preview.svg"):
        """
        Buat preview SVG dari tulisan (tanpa menggerakkan robot).

        Args:
            text: Teks yang akan di-preview
            output_file: Nama file output SVG
        """
        strokes = get_text_strokes(
            text=text,
            font_size=self.font_size,
            letter_spacing=self.letter_spacing,
            word_spacing=self.word_spacing,
            line_spacing=self.line_spacing,
            max_width=self.write_width,
            x_start=self.write_x_start,
            y_start=self.write_y_start
        )

        # Buat SVG
        svg_width = self.paper_width
        svg_height = self.paper_height

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_width}mm" height="{svg_height}mm" '
            f'viewBox="0 0 {svg_width} {svg_height}">',
            f'  <rect width="{svg_width}" height="{svg_height}" '
            f'fill="white" stroke="#ccc" stroke-width="0.5"/>',
            # Margin area
            f'  <rect x="{self.margin_left}" y="{self.margin_top}" '
            f'width="{self.write_width}" height="{self.write_height}" '
            f'fill="none" stroke="#eee" stroke-width="0.3" stroke-dasharray="2,2"/>',
        ]

        # Tambahkan strokes
        for stroke in strokes:
            if len(stroke) < 2:
                continue
            points = ' '.join(f'{x:.2f},{y:.2f}' for x, y in stroke)
            svg_lines.append(
                f'  <polyline points="{points}" '
                f'fill="none" stroke="#333" stroke-width="0.3" '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
            )

        svg_lines.append('</svg>')

        svg_content = '\n'.join(svg_lines)
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        print(f"[OK] Preview disimpan: {filepath}")
        print(f"     Buka file SVG di browser untuk melihat preview tulisan")
        return filepath

    # ================================================================
    # INFO & STATUS
    # ================================================================

    def get_status(self):
        """Tampilkan status robot saat ini."""
        status = {
            "Terhubung": self.is_connected,
            "Mode": "Simulasi" if self.simulate else "Hardware",
            "Port": self.port,
            "Posisi": f"({self.current_x:.1f}, {self.current_y:.1f})mm",
            "Pena": "Turun" if self.pen_is_down else "Naik",
            "Kertas": f"{self.paper_name} ({self.paper_width}x{self.paper_height}mm)",
            "Area Tulis": f"{self.write_width:.1f}x{self.write_height:.1f}mm",
            "Kecepatan": f"{self.writing_speed} mm/s",
            "Ukuran Huruf": f"{self.font_size}mm",
            "Total Karakter": self.total_characters,
            "Total Halaman": self.pages_written,
            "Total Jarak Pena": f"{self.total_distance:.1f}mm",
        }

        print("\n=== STATUS ROBOT PENULIS ===")
        for key, value in status.items():
            print(f"  {key:20s}: {value}")
        print("============================\n")
        return status

    def list_paper_sizes(self):
        """Tampilkan semua ukuran kertas yang tersedia."""
        print("\n=== UKURAN KERTAS TERSEDIA ===")
        for name, (w, h) in PAPER_SIZES.items():
            marker = " ← (aktif)" if name == self.paper_name else ""
            print(f"  {name:15s}: {w:6.1f} x {h:6.1f} mm{marker}")
        print(f"\n  Custom: Gunakan set_paper_size(width=..., height=...)")
        print("==============================\n")

    def list_speeds(self):
        """Tampilkan semua preset kecepatan."""
        print("\n=== PRESET KECEPATAN ===")
        for name, speed in SPEED_PRESETS.items():
            marker = " ← (aktif)" if speed == self.writing_speed else ""
            print(f"  {name:20s}: {speed:5.1f} mm/s{marker}")
        print(f"\n  Custom: Gunakan set_speed(speed_mm_s=...)")
        print("========================\n")


# ================================================================
# MAIN - Contoh penggunaan
# ================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║        ROBOT PENULIS AI - Python Controller      ║
║     100% Offline • Lokal • Tanpa Internet        ║
╚══════════════════════════════════════════════════╝
    """)

    # Buat instance robot (mode simulasi untuk testing)
    robot = WritingRobot(simulate=True)
    robot.connect()

    # Tampilkan info
    robot.get_status()
    robot.list_paper_sizes()
    robot.list_speeds()

    # Contoh: Atur pengaturan
    robot.set_paper_size("Buku Tulis")
    robot.set_speed("normal")
    robot.set_font_size(4.0)

    # Contoh: Preview teks
    sample_text = """Halo Dunia!
Ini adalah robot penulis AI.
Saya bisa menulis teks apapun yang Anda mau.
Robot ini bekerja secara lokal tanpa internet.
Kecepatan menulis bisa diatur sesuai kebutuhan.
Ukuran kertas juga bisa disesuaikan."""

    robot.preview_text(sample_text, "preview_tulisan.svg")

    # Contoh: Tulis teks (mode simulasi)
    robot.write_text(sample_text)

    # Tampilkan status akhir
    robot.get_status()

    print("\n[INFO] Ini adalah mode SIMULASI")
    print("[INFO] Untuk menggunakan hardware, jalankan dengan simulate=False")
    print("[INFO] dan hubungkan Arduino ke port serial yang benar\n")
