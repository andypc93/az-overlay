@echo off
python -m PyInstaller --noconfirm --onefile --noconsole --name az-overlay overlay.py
copy /Y config.json dist\config.json >nul
echo Built distz-overlay.exe
