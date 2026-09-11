@echo off
python make_icon.py
python -m PyInstaller --noconfirm --onefile --noconsole --name AZ-Overlay --icon assets\icon.ico ^
  --add-data "config.json;." --add-data "profiles;profiles" --add-data "assets;assets" ^
  --hidden-import pygame._sdl2.controller overlay.py
echo Built dist\AZ-Overlay.exe  (settings live in %%APPDATA%%z-overlay, untouched by rebuilds)
