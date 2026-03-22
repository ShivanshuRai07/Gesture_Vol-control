@echo off
echo Starting web server for mobile access...
echo To access from your phone:
echo 1. Connect your phone to the same Wi-Fi as this PC.
echo 2. Find your PC's IP address (run 'ipconfig').
echo 3. Open http://YOUR-PC-IP:8000 on your phone browser.
echo.
python -m http.server 8000 --directory web_version
pause
