@echo off
setlocal
REM Project root = folder of this script
set "PROJECT_DIR=%~dp0"
set "VENV=%PROJECT_DIR%venv"
set "REQ=%PROJECT_DIR%requirements.txt"

REM 1) Create venv if missing (uses Windows launcher 'py')
if not exist "%VENV%\Scripts\python.exe" (
  py -3 -m venv "%VENV%"
)

REM 2) Use the venv's Python for all installs (guarantees correct site-packages)
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip wheel
if exist "%REQ%" (
  "%VENV%\Scripts\python.exe" -m pip install -r "%REQ%"
)

echo.
echo Virtual environment ready.
echo Use it like:
echo   "%VENV%\Scripts\python.exe" extract_curves.py
echo Or activate:
echo   %VENV%\Scripts\activate
endlocal
