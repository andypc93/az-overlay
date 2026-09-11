@echo off
python -m PyInstaller --noconfirm --onefile --noconsole --name az-overlay ^
  --add-data "config.json;." --add-data "profiles;profiles" overlay.py
echo Built distz-overlay.exe  (settings live in %%APPDATA%%z-overlay, untouched by rebuilds)
