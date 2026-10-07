"""
CLI (Command Line Interface) untuk Robot Penulis AI
=====================================================
Antarmuka terminal interaktif untuk mengoperasikan robot.
Tidak memerlukan dependensi tambahan selain Python standard library + pyserial.
"""

import sys
import os

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

from writing_robot import WritingRobot
from config import PAPER_SIZES, SPEED_PRESETS


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           🤖  ROBOT PENULIS AI  ✍️                      ║
║           ─────────────────────────                      ║
║           100% Offline • Lokal • Python                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def print_help():
    print("""
📋 DAFTAR PERINTAH:
═══════════════════

  KONEKSI:
    connect [port]      - Hubungkan ke Arduino (misal: connect COM3)
    simulate            - Jalankan mode simulasi (tanpa hardware)
    disconnect          - Putuskan koneksi

  MENULIS:
    write               - Tulis teks (akan diminta input)
    writefile [path]    - Tulis teks dari file
    unlimited           - Tulis tanpa batas halaman
    preview             - Buat preview SVG

  PENGATURAN:
    paper [nama]        - Atur ukuran kertas (A4, A5, Buku Tulis, dll.)
    paper custom W H    - Atur ukuran custom (dalam mm)
    speed [nama]        - Atur kecepatan (sangat_lambat/lambat/normal/cepat/sangat_cepat)
    speed custom [mm/s] - Atur kecepatan custom
    fontsize [mm]       - Atur ukuran huruf (2.0 - 10.0)
    margin T B L R      - Atur margin (mm)

  INFO:
    status              - Tampilkan status robot
    papers              - Daftar ukuran kertas
    speeds              - Daftar preset kecepatan
    help                - Tampilkan bantuan ini

  LAINNYA:
    clear               - Bersihkan layar
    exit / quit         - Keluar
    """)


def main():
    print_banner()

    robot = WritingRobot(simulate=True)
    print("[INFO] Ketik 'help' untuk melihat daftar perintah")
    print("[INFO] Ketik 'simulate' untuk memulai mode simulasi")
    print("[INFO] Ketik 'connect COM3' untuk menghubungkan hardware\n")

    while True:
        try:
            cmd = input("\n🤖 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Sampai jumpa!")
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0].lower()

        # === KONEKSI ===
        if action == "connect":
            port = parts[1] if len(parts) > 1 else "COM3"
            robot = WritingRobot(port=port, simulate=False)
            robot.connect()

        elif action == "simulate":
            robot = WritingRobot(simulate=True)
            robot.connect()
            print("[OK] Mode simulasi aktif")

        elif action == "disconnect":
            robot.disconnect()

        # === MENULIS ===
        elif action == "write":
            if not robot.is_connected:
                print("[ERROR] Robot belum terhubung!")
                continue
            print("Masukkan teks (ketik 'SELESAI' di baris baru untuk mulai menulis):")
            lines = []
            while True:
                line = input("  | ")
                if line.strip().upper() == "SELESAI":
                    break
                lines.append(line)
            text = '\n'.join(lines)
            if text:
                robot.write_text(text)
            else:
                print("[PERINGATAN] Teks kosong!")

        elif action == "unlimited":
            if not robot.is_connected:
                print("[ERROR] Robot belum terhubung!")
                continue
            print("Masukkan teks (ketik 'SELESAI' di baris baru untuk mulai menulis):")
            lines = []
            while True:
                line = input("  | ")
                if line.strip().upper() == "SELESAI":
                    break
                lines.append(line)
            text = '\n'.join(lines)
            if text:
                robot.write_unlimited(text)

        elif action == "writefile":
            if not robot.is_connected:
                print("[ERROR] Robot belum terhubung!")
                continue
            if len(parts) < 2:
                filepath = input("Path file: ").strip()
            else:
                filepath = ' '.join(parts[1:])
            robot.write_from_file(filepath, continuous=True)

        elif action == "preview":
            print("Masukkan teks untuk preview (ketik 'SELESAI' untuk generate):")
            lines = []
            while True:
                line = input("  | ")
                if line.strip().upper() == "SELESAI":
                    break
                lines.append(line)
            text = '\n'.join(lines)
            if text:
                robot.preview_text(text)

        # === PENGATURAN ===
        elif action == "paper":
            if len(parts) >= 2:
                if parts[1].lower() == "custom" and len(parts) >= 4:
                    try:
                        w = float(parts[2])
                        h = float(parts[3])
                        robot.set_paper_size(width=w, height=h)
                    except ValueError:
                        print("[ERROR] Format: paper custom [lebar] [tinggi]")
                else:
                    name = ' '.join(parts[1:])
                    robot.set_paper_size(name)
            else:
                robot.list_paper_sizes()

        elif action == "speed":
            if len(parts) >= 2:
                if parts[1].lower() == "custom" and len(parts) >= 3:
                    try:
                        speed = float(parts[2])
                        robot.set_speed(speed_mm_s=speed)
                    except ValueError:
                        print("[ERROR] Format: speed custom [mm/s]")
                else:
                    robot.set_speed(parts[1])
            else:
                robot.list_speeds()

        elif action == "fontsize":
            if len(parts) >= 2:
                try:
                    size = float(parts[1])
                    robot.set_font_size(size)
                except ValueError:
                    print("[ERROR] Format: fontsize [ukuran_mm]")
            else:
                print(f"Ukuran huruf saat ini: {robot.font_size}mm")
                print("Range: 2.0 - 10.0 mm")

        elif action == "margin":
            if len(parts) >= 5:
                try:
                    t, b, l, r = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    robot.set_margins(top=t, bottom=b, left=l, right=r)
                except ValueError:
                    print("[ERROR] Format: margin [atas] [bawah] [kiri] [kanan] (dalam mm)")
            else:
                print(f"Margin saat ini: atas={robot.margin_top} bawah={robot.margin_bottom} "
                      f"kiri={robot.margin_left} kanan={robot.margin_right}mm")

        # === INFO ===
        elif action == "status":
            robot.get_status()

        elif action == "papers":
            robot.list_paper_sizes()

        elif action == "speeds":
            robot.list_speeds()

        elif action == "help":
            print_help()

        elif action == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')

        elif action in ("exit", "quit", "q"):
            robot.disconnect()
            print("👋 Sampai jumpa!")
            break

        else:
            print(f"[ERROR] Perintah tidak dikenal: '{action}'")
            print("Ketik 'help' untuk melihat daftar perintah")


if __name__ == "__main__":
    main()
