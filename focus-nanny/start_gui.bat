@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo Запускаю Focus Nanny GUI (окно с барами)...
py -u "%~dp0app_gui.py"
pause
