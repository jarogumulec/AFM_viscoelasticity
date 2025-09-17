@echo off
REM Full path to python.exe
set PYTHON="C:\Users\Jaro-work\AppData\Local\Programs\Python\Python312\python.exe"

%PYTHON% -m venv venv

call venv\Scripts\activate

%PYTHON% -m pip install --upgrade pip wheel
%PYTHON% -m pip install -r requirements.txt

echo.
echo Virtual environment ready. To activate later, run:
echo   venv\Scripts\activate
