@echo off
chcp 65001 >nul
title SparRadar - Abruf vom PC entfernen
echo.
echo   Entfernt den SparRadar-Abruf von diesem PC: Autostart, Programm und gespeicherten Schlüssel.
choice /c JN /n /m "  Wirklich entfernen? [J/N] "
if errorlevel 2 exit /b 0
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*SparRadar*start.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SparRadar Abruf.lnk" 2>nul
rmdir /s /q "%LOCALAPPDATA%\SparRadar" 2>nul
echo.
echo   Entfernt. Den GitHub-Schlüssel bitte zusätzlich auf github.com unter
echo   Settings - Developer settings - Fine-grained tokens löschen.
pause
