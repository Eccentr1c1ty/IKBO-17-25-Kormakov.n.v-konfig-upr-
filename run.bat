@echo off
cd /d "%~dp0"
where python >nul 2>&1
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    python src\main.py
) else (
    "%USERPROFILE%\.local\bin\uv.exe" run --no-project --python 3.15 src\main.py
)