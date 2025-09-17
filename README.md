# README — AFM (JPK) minimal toolkit

This repository provides a **minimal, Windows-friendly** workflow for working with JPK `*.jpk-force-map` files:

- Creating and using a **virtual environment (venv)** on Windows
- Reading **metadata** from a map (`afm_read_metadata.py`)
- Exporting **time–force** and **time–indentation** for a **single curve** (`export_one_curve.py`)
- Plotting exported **CSV** (`plot_curve_csv.py`)

> Designed for “creep-compliance” maps with segments **0=approach, 1=hold, 2=retract**.

---

## 0) Prerequisites

- **Windows 10/11**
- **Python 3.11+** (3.12 tested). Confirm with:
  ```powershell
  python --version
  ```
  If this opens the Microsoft Store or fails, install Python from python.org and tick “Add Python to PATH” during installation, or use the full path to `python.exe`.

---

## 1) Create & use a virtual environment (venv)

### Option A — via batch (recommended)
Use a batch that **never calls** PowerShell’s activation script (avoids execution policy issues):

1. Put this in `setup_virtualenv.bat`:
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

2. Minimal `requirements.txt`:
   ```txt
   afmformats
   pandas
   numpy
   matplotlib
   ```

3. Run in PowerShell:
   ```powershell
   .\setup_virtualenv.bat
   ```

### Option B — manual (PowerShell), without activation
```powershell
py -3 -m venv .\venv
.\venv\Scripts\python.exe -m pip install --upgrade pip wheel
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### (Optional) Activating venv in PowerShell
PowerShell may block `Activate.ps1` by default.

- **Per-session bypass**:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```
- **Per-user (safer default)**:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  .\venv\Scripts\Activate.ps1
  ```

You can **always** run the venv directly without activation:
```powershell
.\venv\Scripts\python.exe your_script.py
```

---

## 2) What’s inside a JPK force map

Typical columns (first curve):
- `time` [s], `force` [N], `height (piezo)` [m], `height (measured)` [m], `segment` (0/1/2)
- **Segments**: `0 = approach`, `1 = hold (creep)`, `2 = retract`
- Indentation: \(\delta = z_{piezo} - (h_{measured} - z_{piezo})\).

---

## 3) Scripts

### A) `afm_read_metadata.py`
Reads metadata and column info from a `.jpk-force-map`.

**Usage:**
```powershell
.\venv\Scripts\python.exe afm_read_metadata.py
```

### B) `export_one_curve.py`
Exports **time–force** and **time–indentation** for one curve.

**Usage:**
```powershell
# by index
.\venv\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --idx 45 --units nm-nN --out curve_045.csv

# by grid row/col
.\venv\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --row 3 --col 5 --units SI --out curve_r3_c5.csv
```

### C) `plot_curve_csv.py`
Plots exported CSV (segments colored).

**Usage:**
```powershell
.\venv\Scripts\python.exe plot_curve_csv.py .\curve_045.csv
.\venv\Scripts\python.exe plot_curve_csv.py .\curve_045.csv --save .\curve_045
```

---

## 4) Troubleshooting

- Always install with the venv’s Python:
  ```powershell
  .\venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

- If VS Code runs the wrong Python, select:
  ```
  .\venv\Scripts\python.exe
  ```

---

## 5) Segment conventions

- `0 = approach`
- `1 = hold`
- `2 = retract`

Use `segment==1` for creep analysis.

---
