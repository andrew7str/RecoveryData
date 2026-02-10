#!/usr/bin/env python3
"""
Simple data-recovery orchestration CLI.

Modes:
 - Quick: fast imaging (minimal retries)
 - Normal: balanced imaging
 - Slow: thorough imaging (more retries)
 - Advanced: let user pass custom ddrescue args or run file-carving tools

This script is a helper — it shells out to external tools like `ddrescue`,
`dd`, `photorec`, `foremost`, or `scalpel` when available. It avoids
destructive operations by reading devices only; run as root or with
appropriate permissions to access raw devices.
"""

import os
import json
import shutil
import subprocess
import sys
from datetime import datetime


# ANSI Color codes for beautiful CLI output
class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'      # Magenta
    BLUE = '\033[94m'        # Blue
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    ENDC = '\033[0m'         # End color
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline


def print_header(text):
    """Print header with color and formatting"""
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*60}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.CYAN}  {text}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*60}{Color.ENDC}\n")


def print_success(text):
    """Print success message in green"""
    print(f"{Color.GREEN}✓ {text}{Color.ENDC}")


def print_info(text):
    """Print info message in blue"""
    print(f"{Color.BLUE}ℹ {text}{Color.ENDC}")


def print_warning(text):
    """Print warning message in yellow"""
    print(f"{Color.YELLOW}⚠ {text}{Color.ENDC}")


def print_error(text):
    """Print error message in red"""
    print(f"{Color.RED}✗ {text}{Color.ENDC}")


def which(cmd):
    return shutil.which(cmd) is not None


def list_devices():
    # Use lsblk JSON output for nicer parsing
    try:
        out = subprocess.check_output(["lsblk", "-J", "-o", "NAME,SIZE,MODEL,TYPE,MOUNTPOINT,TRAN"], text=True)
        j = json.loads(out)
        devices = []
        for dev in j.get("blockdevices", []):
            if dev.get("type") in ("disk", "part"):
                name = dev.get("name")
                path = f"/dev/{name}"
                devices.append({
                    "path": path,
                    "size": dev.get("size"),
                    "model": dev.get("model") or "",
                    "mount": dev.get("mountpoint") or "",
                    "type": dev.get("type"),
                    "tran": dev.get("tran") or "",
                })
        return devices
    except Exception:
        return []


def choose_device():
    devs = list_devices()
    if not devs:
        print_warning("No block devices found via lsblk. Provide device path manually (e.g. /dev/sdb):")
        path = input(f"{Color.YELLOW}Device: {Color.ENDC}").strip()
        return path
    print_header("DETECTED BLOCK DEVICES")
    for i, d in enumerate(devs, 1):
        mount_info = f"[{d['mount']}]" if d['mount'] else "unmounted"
        print(f"{Color.BOLD}{Color.YELLOW}{i}{Color.ENDC}) {Color.GREEN}{d['path']:<15}{Color.ENDC} {d['size']:<10} {d['model']:<20} {mount_info}")
    choice = input(f"\n{Color.YELLOW}Pilih device nomor (atau ketik path): {Color.ENDC}").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(devs):
        selected = devs[int(choice) - 1]["path"]
        print_success(f"Device terpilih: {selected}")
        return selected
    return choice


def ensure_outdir(prefix="recovery"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"{prefix}_{ts}"
    os.makedirs(out, exist_ok=True)
    return os.path.abspath(out)


def run(cmd, shell=False):
    print_info("Running: " + (" ".join(cmd) if isinstance(cmd, list) else cmd))
    try:
        subprocess.run(cmd, shell=shell, check=False)
    except KeyboardInterrupt:
        print_warning("Interrupted by user")


def image_with_ddrescue(device, outimg, mapfile, quick=False, retries=0, extra_args=None):
    if not which("ddrescue") and not which("gddrescue"):
        print_warning("ddrescue not found. Falling back to dd (no mapfile, no retries).")
        cmd = ["dd", f"if={device}", f"of={outimg}", "bs=4M", "status=progress", "conv=noerror,sync"]
        run(cmd)
        return

    dd = which("ddrescue") and "ddrescue" or "gddrescue"
    cmd = [dd]
    if quick:
        cmd += ["-n"]
    if retries and not quick:
        cmd += ["-r", str(retries)]
    if extra_args:
        cmd += extra_args
    cmd += [device, outimg, mapfile]
    run(cmd)


def choose_file_types():
    options = [
        ("jpg", "JPEG images"),
        ("png", "PNG images"),
        ("gif", "GIF images"),
        ("pdf", "PDF documents"),
        ("doc", "MS Word (.doc)") ,
        ("docx", "MS Word (.docx)"),
        ("xls", "MS Excel"),
        ("xlsx", "MS Excel (x)"),
        ("mp3", "MP3 audio"),
        ("mp4", "MP4 video"),
        ("zip", "ZIP archives"),
        ("rar", "RAR archives"),
        ("all", "All supported types"),
    ]
    print(f"\n{Color.BOLD}{Color.CYAN}Pilih format file untuk recovery (pisahkan dengan koma), atau ketik 'all' untuk semua:{Color.ENDC}")
    for i, (ext, desc) in enumerate(options, 1):
        print(f"{Color.BOLD}{Color.YELLOW}{i:2d}{Color.ENDC}) {Color.GREEN}{ext:<6} {Color.ENDC}- {desc}")
    sel = input(f"{Color.YELLOW}Pilihan (contoh: 1,2,5 atau all): {Color.ENDC}").strip().lower()
    if not sel:
        return []
    if sel == "all":
        return [o[0] for o in options if o[0] != "all"]
    parts = [s.strip() for s in sel.split(",") if s.strip()]
    chosen = []
    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(options):
                ext = options[idx][0]
                if ext != "all":
                    chosen.append(ext)
        else:
            # allow typed extensions like 'jpg' or full words
            for ext, _ in options:
                if p == ext:
                    if ext != "all":
                        chosen.append(ext)
    # dedupe while preserving order
    seen = set()
    out = []
    for e in chosen:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def run_carving(image_path, outdir, types_list=None):
    print_info("Attempting file carving using available tools...")
    if types_list:
        print_success(f"Selected types: {Color.BOLD}{', '.join(types_list)}{Color.ENDC}")
    if which("photorec"):
        print_info("photorec found — launching (interactive). Pilihan tipe akan dipilih di dalam photorec.")
        run(["photorec", image_path])
        return
    if which("foremost"):
        print_info("foremost found — running to output dir")
        cmd = ["foremost"]
        if types_list:
            # foremost accepts -t ext,ext2 (commas)
            cmd += ["-t", ",".join(types_list)]
        cmd += ["-i", image_path, "-o", outdir]
        run(cmd)
        return
    if which("scalpel"):
        print_info("scalpel found — running to output dir (using default config)")
        print_warning("Note: custom scalpel config generation for specific types is not implemented; consider using foremost for type-filtered carving.")
        run(["scalpel", image_path, "-o", outdir])
        return
    print_error("No carving tools found (photorec/foremost/scalpel). Install them or run carving manually on the image.")


def quick_flow(device):
    out = ensure_outdir("quick_recovery")
    img = os.path.join(out, "image_quick.img")
    mapf = os.path.join(out, "ddrescue.map")
    print_info(f"Quick: imaging {device} → {img} (minimal retries)")
    image_with_ddrescue(device, img, mapf, quick=True, retries=0)
    if input(f"{Color.YELLOW}Jalankan file-carving pada image? [y/N]: {Color.ENDC}").lower() == "y":
        types = choose_file_types()
        run_carving(img, os.path.join(out, "carved"), types_list=types)


def normal_flow(device):
    out = ensure_outdir("normal_recovery")
    img = os.path.join(out, "image_normal.img")
    mapf = os.path.join(out, "ddrescue.map")
    print_info(f"Normal: imaging {device} → {img} (balanced retries)")
    image_with_ddrescue(device, img, mapf, quick=False, retries=3)
    if input(f"{Color.YELLOW}Jalankan file-carving pada image? [y/N]: {Color.ENDC}").lower() == "y":
        types = choose_file_types()
        run_carving(img, os.path.join(out, "carved"), types_list=types)


def slow_flow(device):
    out = ensure_outdir("slow_recovery")
    img = os.path.join(out, "image_slow.img")
    mapf = os.path.join(out, "ddrescue.map")
    print_info(f"Slow: imaging {device} → {img} (thorough retries, slow)")
    image_with_ddrescue(device, img, mapf, quick=False, retries=10, extra_args=["-R"]) 
    if input(f"{Color.YELLOW}Jalankan file-carving pada image? [y/N]: {Color.ENDC}").lower() == "y":
        types = choose_file_types()
        run_carving(img, os.path.join(out, "carved"), types_list=types)


def advanced_flow(device):
    out = ensure_outdir("advanced_recovery")
    img = os.path.join(out, "image_advanced.img")
    mapf = os.path.join(out, "ddrescue.map")
    print_header("Advanced Mode")
    print_info("Anda dapat memasukkan argumen custom untuk ddrescue, atau memilih tool carving.")
    if which("ddrescue") or which("gddrescue"):
        custom = input(f"{Color.YELLOW}Masukkan argumen ddrescue (e.g. -n -r 3) atau kosong untuk default: {Color.ENDC}").strip()
        args = custom.split() if custom else None
        image_with_ddrescue(device, img, mapf, quick=False, retries=0, extra_args=args)
    else:
        print_warning("ddrescue tidak ditemukan — fallback ke dd")
        run(["dd", f"if={device}", f"of={img}", "bs=4M", "status=progress", "conv=noerror,sync"]) 

    print_header("Advanced Options")
    print(f"{Color.BOLD}{Color.CYAN}1{Color.ENDC}  Jalankan photorec/foremost/scalpel pada image")
    print(f"{Color.BOLD}{Color.CYAN}2{Color.ENDC}  Jalankan testdisk pada device (interactive)")
    print(f"{Color.BOLD}{Color.RED}3{Color.ENDC}  Selesai")
    c = input(f"\n{Color.YELLOW}Pilihan: {Color.ENDC}").strip()
    if c == "1":
        types = choose_file_types()
        run_carving(img, os.path.join(out, "carved"), types_list=types)
    elif c == "2":
        if which("testdisk"):
            run(["testdisk", device])
        else:
            print_error("testdisk tidak terpasang")


def list_partitions_on_device(device):
    # List partitions on a device using fdisk or parted
    print_info(f"Listing partitions on {device}...")
    if which("parted"):
        run(["parted", "-l", device])
    elif which("fdisk"):
        run(["sudo", "fdisk", "-l", device])
    else:
        print_error("parted atau fdisk tidak ditemukan.")


def scan_lost_partitions(device):
    # Use testdisk to scan for lost/deleted partitions
    print_info(f"Scanning for lost partitions on {device}...")
    print_warning("testdisk has interactive interface. This will launch it.")
    if which("testdisk"):
        print_info("Launching testdisk (interactive)...")
        run(["sudo", "testdisk", device])
    else:
        print_error("testdisk tidak terpasang. Install dengan: sudo apt install testdisk")


def recover_deleted_partition(device):
    # Attempt to recover a deleted partition using testdisk
    print_warning(f"Recovering deleted partition on {device}...")
    if which("testdisk"):
        print_info("Launching testdisk to recover/restore partition...")
        run(["sudo", "testdisk", device])
    else:
        print_error("testdisk tidak terpasang. Install dengan: sudo apt install testdisk")


def recover_formatted_partition(device):
    # For formatted partitions, user selects partition and we image + carve it
    list_partitions_on_device(device)
    partition = input(f"{Color.YELLOW}➤ Masukkan path partisi untuk di-recover (contoh: /dev/sdb1): {Color.ENDC}").strip()
    if not partition:
        print_error("Partisi tidak dipilih.")
        return
    print_info(f"Akan melakukan recovery pada {partition}...")
    
    out = ensure_outdir("formatted_partition_recovery")
    img = os.path.join(out, f"partition_{os.path.basename(partition)}.img")
    mapf = os.path.join(out, "ddrescue.map")
    
    print_info(f"Imaging {partition} → {img}")
    image_with_ddrescue(partition, img, mapf, quick=False, retries=3)
    
    if input(f"{Color.YELLOW}Jalankan file-carving pada image? [y/N]: {Color.ENDC}").lower() == "y":
        types = choose_file_types()
        run_carving(img, os.path.join(out, "carved"), types_list=types)


def partition_recovery_menu():
    # Submenu for partition recovery
    if os.geteuid() != 0:
        print_warning("Operasi partisi memerlukan akses root.")
    device = choose_device()
    if not device:
        print_error("Device tidak dipilih.")
        return
    
    print_header("🗂️  PARTITION RECOVERY MENU")
    print(f"{Color.BOLD}{Color.CYAN}1{Color.ENDC}  📍 List current partitions")
    print(f"{Color.BOLD}{Color.CYAN}2{Color.ENDC}  🔍 Scan for lost/deleted partitions")
    print(f"{Color.BOLD}{Color.CYAN}3{Color.ENDC}  🔧 Recover deleted partition")
    print(f"{Color.BOLD}{Color.CYAN}4{Color.ENDC}  📂 Recover formatted partition (image + carve)")
    print(f"{Color.BOLD}{Color.RED}q{Color.ENDC}  ← Kembali ke menu utama")
    
    choice = input(f"\n{Color.YELLOW}➤ Pilihan: {Color.ENDC}").strip().lower()
    
    if choice == "q":
        return
    elif choice == "1":
        list_partitions_on_device(device)
    elif choice == "2":
        scan_lost_partitions(device)
    elif choice == "3":
        recover_deleted_partition(device)
    elif choice == "4":
        recover_formatted_partition(device)
    else:
        print_error("Pilihan tidak dikenali.")


def device_data_recovery_menu():
    # Original device/data recovery menu (Quick/Normal/Slow/Advanced)
    print_header("⚡ DEVICE DATA RECOVERY MENU")
    print("Pilih mode recovery:")
    print(f"{Color.BOLD}{Color.CYAN}1{Color.ENDC}  ⚡ Quick   - Cepat, retries minimal (media sehat)")
    print(f"{Color.BOLD}{Color.CYAN}2{Color.ENDC}  🚀 Normal - Seimbang, retries moderat (recommended)")
    print(f"{Color.BOLD}{Color.CYAN}3{Color.ENDC}  🐌 Slow   - Lambat, retries banyak (media rusak)")
    print(f"{Color.BOLD}{Color.CYAN}4{Color.ENDC}  ⚙️  Advanced - Custom parameters & tools")
    print(f"{Color.BOLD}{Color.RED}q{Color.ENDC}  ← Kembali ke menu utama")
    choice = input(f"\n{Color.YELLOW}➤ Mode: {Color.ENDC}").strip().lower()
    if choice == "q":
        return
    device = choose_device()
    if not device:
        print_error("Device tidak dipilih. Keluar.")
        return
    if choice == "1" or choice == "quick":
        quick_flow(device)
    elif choice == "2" or choice == "normal":
        normal_flow(device)
    elif choice == "3" or choice == "slow":
        slow_flow(device)
    elif choice == "4" or choice == "advanced":
        advanced_flow(device)
    else:
        print_error("Pilihan tidak dikenali.")


def main():
    if os.geteuid() != 0:
        print_warning("Akses ke device mentah sering membutuhkan root. Jalankan dengan sudo jika perlu.")
    
    # Print banner
    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("╔═══════════════════════════════════════════════════════╗")
    print("║       🔧  RECOVERY HELPER - Data Recovery Tool  🔧    ║")
    print("║   Quick/Normal/Slow/Advanced + Partition Recovery    ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print(f"{Color.ENDC}")
    
    while True:
        print_header("🏠 MAIN MENU")
        print(f"{Color.BOLD}{Color.GREEN}1{Color.ENDC}  ⚡ Device Data Recovery (Quick/Normal/Slow/Advanced)")
        print(f"{Color.BOLD}{Color.GREEN}2{Color.ENDC}  🗂️  Partition Recovery (deleted/formatted)")
        print(f"{Color.BOLD}{Color.RED}q{Color.ENDC}  💪 Keluar")
        choice = input(f"\n{Color.YELLOW}➤ Pilihan: {Color.ENDC}").strip().lower()
        
        if choice == "q":
            print_success("Terima kasih! Semoga data Anda berhasil di-recover 🎉")
            sys.exit(0)
        elif choice == "1":
            device_data_recovery_menu()
        elif choice == "2":
            partition_recovery_menu()
        else:
            print_error("Pilihan tidak dikenali.")


if __name__ == "__main__":
    main()
