# README — AFM (JPK) minimal toolkit

This repository provides a **minimal, Windows-friendly** workflow for working with JPK `*.jpk-force-map` files:

- Creating and using a **virtual environment (venv)** on Windows
- Reading **metadata** from a map (`afm_read_metadata.py`)
- Exporting **time–force** and **time–indentation** for a **single curve** (`export_one_curve.py`)
- Visualising exported **CSV** in four complementary plots (`plot_curve_csv.py`)

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
.\venv\Scripts\python.exe afm_read_metadata.py
```

---

### B) `export_one_curve.py`
Exports **time–force** and **time–indentation** for one curve.

**Usage:**
```powershell
# by index
.\venv\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --idx 45 --units nm-nN --out curve_045.csv

# by grid row/col
.\venv\Scripts\python.exe export_one_curve.py ".\map.jpk-force-map" --row 3 --col 5 --units SI --out curve_r3_c5.csv
```

---

### C) `plot_curve_csv.py`
Creates **four plots** from an exported curve CSV:

1. Time vs force (segments colored)  
2. Time vs indentation (segments colored)  
3. Hold-only (segment==1) with dual Y axes (force + indentation)  
4. Force vs indentation (segments colored)  

**Usage:**
```powershell
# Show interactively
.\venv\Scripts\python.exe plot_curve_csv.py .\curve_045.csv

# Save all four PNGs with prefix
.\venv\Scripts\python.exe plot_curve_csv.py .\curve_045.csv --save-prefix .\curve_045
```

This will produce files like:
```
curve_045_time_vs_force.png
curve_045_time_vs_indentation.png
curve_045_hold_dualy.png
curve_045_force_vs_indentation.png
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
