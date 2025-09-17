# README — AFM (JPK) minimal toolkit

This repository provides a **minimal, Windows-friendly** workflow for working with JPK `*.jpk-force-map` files:

- Creating and using a **virtual environment (venv)** on Windows
- Reading **metadata** from a map (`afm_read_metadata.py`)
- Exporting **time–force** and **time–indentation** for a **single curve** (`export_one_curve.py`)
- Plotting exported **CSV** (`plot_curve_csv.py`)
- Plotting **only the hold segment** with dual Y axes (force + indentation) (`plot_hold_dualy_csv.py`)

> Designed for “creep-compliance” maps with segments **0=approach, 1=hold, 2=retract**.

---

## 0) Prerequisites

- **Windows 10/11**
- **Python 3.11+** (3.12 tested). Confirm with:
  ```powershell
  python --version
  ```

---

## 1) Create & use a virtual environment (venv)

### Batch script (recommended)
Use `setup_virtualenv.bat`:

```bat
@echo off
setlocal
set "PROJECT_DIR=%~dp0"
set "VENV=%PROJECT_DIR%venv"
set "REQ=%PROJECT_DIR%requirements.txt"

if not exist "%VENV%\Scripts\python.exe" (
  py -3 -m venv "%VENV%"
)

"%VENV%\Scripts\python.exe" -m pip install --upgrade pip wheel
if exist "%REQ%" (
  "%VENV%\Scripts\python.exe" -m pip install -r "%REQ%"
)

echo.
echo Virtual environment ready.
echo Run scripts with:
echo   "%VENV%\Scripts\python.exe" your_script.py
echo Or activate (optional):
echo   %VENV%\Scripts\activate
endlocal
```

Minimal `requirements.txt`:
```txt
afmformats
pandas
numpy
matplotlib
```

Run in PowerShell:
```powershell
.\setup_virtualenv.bat
```

---

## 2) Segment conventions

- `0 = approach`
- `1 = hold`
- `2 = retract`

For creep analysis, use only `segment==1`.

---

## 3) Scripts

### A) `afm_read_metadata.py`
Reads metadata and column info from a `.jpk-force-map`.

**Usage:**
```powershell
.env\Scripts\python.exe afm_read_metadata.py
```

---

### B) `export_one_curve.py`
Exports **time–force** and **time–indentation** for one curve.

**Usage:**
```powershell
# by index
.env\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --idx 45 --units nm-nN --out curve_045.csv

# by grid row/col
.env\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --row 3 --col 5 --units SI --out curve_r3_c5.csv
```

---

### C) `plot_curve_csv.py`
Plots exported CSV (segments colored separately).

**Usage:**
```powershell
.env\Scripts\python.exe plot_curve_csv.py .\curve_045.csv
.env\Scripts\python.exe plot_curve_csv.py .\curve_045.csv --save .\curve_045
```

---

### D) `plot_hold_dualy_csv.py`
Plots **only the hold segment** (`segment==1`) with **dual Y axes**:  
- Left Y: force  
- Right Y: indentation  

If only one variable is present, it is plotted on the main axis.

**Usage:**
```powershell
# Show interactively
.env\Scripts\python.exe plot_hold_dualy_csv.py .\curve_045.csv

# Save PNG
.env\Scripts\python.exe plot_hold_dualy_csv.py .\curve_045.csv --save .\curve_045_hold.png
```

---

## 4) Troubleshooting

- Always install with the venv’s Python:
  ```powershell
  .env\Scripts\python.exe -m pip install -r requirements.txt
  ```

- If VS Code runs the wrong Python, select:
  ```
  .env\Scripts\python.exe
  ```

---
