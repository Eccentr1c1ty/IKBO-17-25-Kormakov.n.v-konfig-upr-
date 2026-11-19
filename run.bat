@echo off
cd /d "%~dp0"
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    python -m src.main %*
) else (
    "%USERPROFILE%\.local\bin\uv.exe" run --no-project --python 3.15 -m src.main %*
)
