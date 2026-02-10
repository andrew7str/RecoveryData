# 🔧 Recovery Helper

> **Powerful & Easy-to-Use Data Recovery Tool for Linux/Debian & Windows**

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python: 3.6+](https://img.shields.io/badge/Python-3.6%2B-green.svg)
![Platform: Linux/Windows](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-orange.svg)

## 📋 Overview

**Recovery Helper** adalah aplikasi CLI yang comprehensive untuk recovery data dan partisi dari perangkat penyimpanan seperti USB flash drive, HDD/SSD, dan SD card. Dilengkapi dengan berbagai mode recovery dan alat carving file yang powerful.

---

## ✨ Fitur Unggulan

### 🔄 Device Data Recovery
Recover data dengan 4 mode strategis:

| Mode | Kecepatan | Kualitas | Use Case |
|------|-----------|----------|----------|
| **Quick** | ⚡ Cepat | ⭐ Standar | Media dalam kondisi baik |
| **Normal** | 🚀 Seimbang | ⭐⭐⭐ Optimal | Situasi umum (recommended) |
| **Slow** | 🐌 Lambat | ⭐⭐⭐⭐⭐ Maksimal | Media rusak/bad sectors |
| **Advanced** | ⚙️ Custom | 🎯 Fleksibel | User-defined parameters |

**Fitur Tambahan:**
- 🎯 **Selective File Type Recovery** - Pilih format file spesifik (JPG, PNG, PDF, DOCX, ZIP, dll)
- 🔗 **Chaining Tools** - Otomatis menggunakan `ddrescue` → file-carving (`photorec`, `foremost`, `scalpel`)
- 📊 **Mapfile Generation** - Track progress dengan `.map` file dari ddrescue
- ⚠️ **Error Handling** - Automatic fallback dari `ddrescue` ke `dd` jika diperlukan

### 🗂️ Partition Recovery
Restore partisi yang terhapus atau terformat:

- 📍 **List Partitions** - Visualisasi struktur partisi device
- 🔍 **Scan Lost Partitions** - Deteksi partisi yang hilang menggunakan testdisk
- 🔧 **Recover Deleted Partitions** - Restore partisi terhapus tidak sengaja
- 📂 **Recover Formatted Partitions** - Image + carve files dari partisi terformat

---

## 📦 Requirements

### System Dependencies (Debian/Ubuntu)

**Required:**
- `python3` (3.6+)
- `lsblk` (util-linux)

**Recommended:**
- `gddrescue` - Advanced disk imaging with retry logic
- `testdisk/photorec` - Partition recovery & file carving
- `foremost` - Fast file carving tool
- `scalpel` - Configurable file carving
- `parted` - Partition analysis

### Install Dependencies

```bash
# For Debian/Ubuntu
sudo apt update
sudo apt install -y python3 python3-venv \
  gddrescue testdisk foremost scalpel parted util-linux

# Alternative: minimal installation
sudo apt install -y python3 gddrescue testdisk
```

---

## 🚀 Quick Start

### Linux/Debian

```bash
# Clone & navigate
git clone <repository-url>
cd RecoveryData

# Make script executable
chmod +x run_app.sh

# Run (recommends to use with sudo for device access)
sudo ./run_app.sh
```

### Windows

```cmd
# Navigate to folder
cd RecoveryData

# Run batch file (may require admin prompt)
run_app.bat
```

### Manual Python Run

```bash
# With virtualenv
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
sudo python3 recover.py
```

---

## 📖 Usage Guide

### Main Menu

```
=== Recovery Helper - Main Menu ===
1) Device Data Recovery (Quick/Normal/Slow/Advanced)
2) Partition Recovery (deleted/formatted)
q) Keluar
```

### Device Data Recovery Flow

1. **Select Mode** - Quick/Normal/Slow/Advanced
2. **Choose Device** - Pick target device/USB/SD card
3. **Imaging** - Create disk image with retry logic
4. **File Carving** *(optional)* - Recover specific file types
5. **Output** - Get recovered files in timestamped folder

**Example Session:**
```bash
$ sudo ./run_app.sh

=== Recovery Helper - Main Menu ===
1) Device Data Recovery
2) Partition Recovery
q) Keluar
Pilihan: 1

=== Device Data Recovery Menu ===
1) Quick
2) Normal
3) Slow
4) Advanced
Mode: 2

[Device detection...]
1) /dev/sdb  32GB  SANDISK USB
Pilih device nomor: 1

Imaging /dev/sdb → normal_recovery_20260211_143052/image_normal.img
[Progress...]

Jalankan file-carving pada image? [y/N]: y

Pilih format file untuk recovery:
1) jpg - JPEG images
2) png - PNG images
...
Pilihan: 1,2,3
[Carving files...]
✓ Success!
```

### Partition Recovery Flow

1. **Select Device**
2. **Choose Operation**:
   - List current partitions
   - Scan for lost/deleted partitions (interactive testdisk)
   - Recover deleted partition
   - Recover formatted partition (image + carve)

---

## 📁 Output Structure

Recovery Helper membuat folder terstruktur dengan timestamp:

```
quick_recovery_20260211_143052/
├── image_quick.img          # Disk image
├── ddrescue.map             # Progress/sector map
└── carved/                  # Carved files (if selected)
    ├── jpg/
    ├── png/
    ├── pdf/
    └── ...

normal_recovery_20260211_143500/
├── image_normal.img
├── ddrescue.map
└── carved/
    └── ...
```

---

## ⚙️ Advanced Usage

### Custom ddrescue Parameters

Gunakan mode **Advanced** untuk custom arguments:

```
Advanced mode: Masukkan argumen ddrescue (e.g. -n -r 3):
-r 5 -R  # 5 retries with reverse pass
```

Common ddrescue flags:
- `-n` : no scrape (quick pass only)
- `-r N` : retry bad sectors N times
- `-R` : reverse pass strategy
- `-d` : direct drive access
- `-f` : force overwrite
- `--log-file=FILE` : save log

### File Type Selection

Supported formats dalam carving menu:
- **Images**: jpg, png, gif, bmp
- **Documents**: pdf, doc, docx, xls, xlsx
- **Archives**: zip, rar, 7z, tar
- **Media**: mp3, mp4, mkv, avi
- **Other**: ppt, pptx, txt, dan lebih banyak

---

## 🔒 Security & Safety Notes

⚠️ **Important:**
- Script ini **read-only** untuk device sumber - data tidak akan dihapus
- Namun tetap hati-hati saat memilih device target
- **JANGAN** menulis ke device yang ingin di-recover
- Gunakan with `sudo` untuk akses raw device yang proper
- Test pada file kecil terlebih dahulu sebelum operasi besar

✅ **Best Practices:**
- Backup partition table sebelum recovery: `sudo sfdisk -d /dev/sdX > partition_backup.txt`
- Gunakan external drive untuk output (jangan di device yang sama)
- Monitor disk space sebelum mulai (image bisa sangat besar)
- Preserve power supply untuk critical recovery operations

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Run dengan `sudo` |
| ddrescue not found | Install `gddrescue`: `sudo apt install gddrescue` |
| testdisk not found | Install untuk partition recovery: `sudo apt install testdisk` |
| Device not detected | Ensure device connected & check with `lsblk` |
| No file carving tools | Install `foremost`: `sudo apt install foremost` |
| Out of disk space | Use external drive atau adjust output directory |

### Debug Mode

```bash
# Run with verbose output
python3 -u recover.py  # unbuffered output
```

---

## 📋 File Structure

```
RecoveryData/
├── recover.py              # Main CLI application
├── run_app.sh              # Linux/Debian launcher
├── run_app.bat             # Windows launcher
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .gitignore              # Git ignore patterns
└── .venv/                  # Virtual environment (created at runtime)
```

---

## 🔄 How It Works

```
User Input
    ↓
Device Selection (lsblk)
    ↓
Choose Mode (Quick/Normal/Slow/Advanced)
    ↓
Imaging Phase
    ├─ ddrescue (preferred)
    └─ dd (fallback)
    ↓
File Carving (optional)
    ├─ photorec (interactive)
    ├─ foremost (batch mode)
    └─ scalpel (batch mode)
    ↓
Output Folder (timestamped)
    ├─ image.img
    ├─ ddrescue.map
    └─ carved/
```

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- GUI wrapper using PyQt/Tkinter
- Non-interactive photorec automation
- Cloud/network storage support
- Better error recovery strategies
- Automated test suite

---

## 📄 License

MIT License - See LICENSE file for details

---

## 💡 Tips & Tricks

- **Fastest Recovery**: Use **Quick** mode on healthy media
- **Best Quality**: Use **Slow** mode on damaged/problematic media
- **Targeted Recovery**: Select specific file types untuk faster carving
- **Batch Operations**: Script multiple recovery sessions

---

## 🔗 Related Tools

- [GNU ddrescue](https://www.gnu.org/software/ddrescue/) - Advanced disk imaging
- [TestDisk/PhotoRec](https://www.cgsecurity.org/wiki/TestDisk) - Partition recovery
- [Foremost](https://foremost.sourceforge.net/) - File carving
- [Scalpel](https://github.com/sleuthkit/scalpel) - File carving engine

---

## ❓ FAQ

**Q: Apakah data saya akan hilang?**
A: Tidak. Script ini hanya MEMBACA device. Data tidak akan dihapus.

**Q: Berapa lama proses recovery?**
A: Tergantung ukuran media dan mode yang dipilih. Slow mode bisa memakan waktu berjam-jam.

**Q: Apakah bisa recover 100% data?**
A: Tergantung kondisi media. Media yang rusak parah mungkin hanya recover sebagian.

**Q: Bisa dijalankan di macOS?**
A: Belum ditest. Requirements serupa dengan Linux, tapi mungkin perlu adaptasi.

---

**Made with ❤️ for data recovery enthusiasts**
