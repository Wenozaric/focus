@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo Запускаю Focus Nanny (vision отключен пока не скачаешь модель)...
py -u "%~dp0focus_nanny.py"
pause
