"""
Konfigurasi Robot Penulis AI
============================
Semua pengaturan ukuran kertas, kecepatan, dan koneksi serial.
Sesuaikan nilai-nilai ini dengan kebutuhan Anda.
"""

# ============================================================
# PENGATURAN SERIAL (koneksi ke Arduino)
# ============================================================
SERIAL_PORT = "COM3"          # Ganti sesuai port Arduino Anda
SERIAL_BAUDRATE = 115200      # Baud rate komunikasi serial
SERIAL_TIMEOUT = 2            # Timeout koneksi (detik)

# ============================================================
# UKURAN AREA KERJA ROBOT (dalam milimeter)
# ============================================================
# Dimensi fisik maksimum robot: 400mm x 300mm
# Area kerja efektif sedikit lebih kecil karena margin mekanis
ROBOT_MAX_X = 380.0           # Lebar maksimum area kerja (mm)
ROBOT_MAX_Y = 280.0           # Tinggi maksimum area kerja (mm)

# ============================================================
# PRESET UKURAN KERTAS (dalam mm) - [lebar, tinggi]
# ============================================================
PAPER_SIZES = {
    "A4":         (210.0, 297.0),
    "A5":         (148.0, 210.0),
    "A3":         (297.0, 420.0),   # Hanya jika robot cukup besar
    "Letter":     (215.9, 279.4),
    "Legal":      (215.9, 355.6),
    "B5":         (176.0, 250.0),
    "Folio":      (215.0, 330.0),
    "Buku Tulis": (165.0, 210.0),   # Ukuran buku tulis standar Indonesia
    "Custom":     (200.0, 250.0),   # Bisa diubah sesuai kebutuhan
}

# Ukuran kertas default
DEFAULT_PAPER_SIZE = "A4"

# ============================================================
# MARGIN TULISAN (dalam mm dari tepi kertas)
# ============================================================
MARGIN_TOP = 15.0
MARGIN_BOTTOM = 15.0
MARGIN_LEFT = 15.0
MARGIN_RIGHT = 15.0

# ============================================================
# PENGATURAN TULISAN
# ============================================================
# Ukuran huruf dalam mm (tinggi karakter)
FONT_SIZE = 4.0               # Tinggi huruf (mm), range: 2.0 - 10.0
LETTER_SPACING = 0.8          # Jarak antar huruf (mm)
WORD_SPACING = 3.0            # Jarak antar kata (mm)
LINE_SPACING = 7.0            # Jarak antar baris (mm)

# ============================================================
# PENGATURAN KECEPATAN (mm/detik)
# ============================================================
SPEED_PRESETS = {
    "sangat_lambat": 5.0,     # Untuk tulisan sangat rapi
    "lambat":        10.0,    # Tulisan rapi
    "normal":        20.0,    # Kecepatan normal
    "cepat":         35.0,    # Kecepatan tinggi
    "sangat_cepat":  50.0,    # Kecepatan maksimum
}

DEFAULT_SPEED = "normal"

# Kecepatan pergerakan tanpa menulis (pen up)
TRAVEL_SPEED = 60.0           # mm/detik

# ============================================================
# PENGATURAN PEN (PENA / PULPEN)
# ============================================================
PEN_UP_ANGLE = 70             # Sudut servo saat pena diangkat (derajat)
PEN_DOWN_ANGLE = 40           # Sudut servo saat pena menyentuh kertas
PEN_DELAY = 150               # Delay setelah gerakan pen up/down (ms)

# ============================================================
# PENGATURAN MOTOR STEPPER
# ============================================================
STEPS_PER_MM = 80.0           # Langkah per milimeter (tergantung mekanik)
                               # GT2 belt + 20T pulley + 1/16 microstepping:
                               # 200 steps * 16 / (20 * 2mm) = 80 steps/mm

# ============================================================
# DIMENSI FISIK ROBOT
# ============================================================
ROBOT_DIMENSIONS = {
    "panjang_frame":  450,    # mm - Panjang kerangka luar
    "lebar_frame":    350,    # mm - Lebar kerangka luar
    "tinggi_total":   80,     # mm - Tinggi total robot
    "diameter_basis": 450,    # mm - Diameter basis jika bentuk lingkaran
    "berat_estimasi": "~1.5 kg",
}
