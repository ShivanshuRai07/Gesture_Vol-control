@echo off
taskkill /F /IM pythonw.exe /T 2>nul
start pythonw main.py
exit
