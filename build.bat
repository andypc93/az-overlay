@echo off
python make_icon.py
python make_version.py
python -m PyInstaller --noconfirm --onefile --noconsole --name AZ-Overlay --icon assets\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "config.json;." --add-data "profiles;profiles" --add-data "assets;assets" ^
  --hidden-import pygame._sdl2.controller overlay.py
echo Built dist\AZ-Overlay.exe  (settings live in %%APPDATA%%\az-overlay, untouched by rebuilds)
