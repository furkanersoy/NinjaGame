@echo off
setlocal
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onedir --windowed --name NinjaGame --add-data "data;data" game.py
if errorlevel 1 (
    echo Build failed. Check that requirements.txt has been installed.
    exit /b 1
)
echo Build complete: dist\NinjaGame\NinjaGame.exe
