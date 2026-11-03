@echo off
chcp 65001 >nul
setlocal EnableExtensions
title SparRadar - Abruf vom PC einrichten
set "DIR=%LOCALAPPDATA%\SparRadar"
set "RAW=https://raw.githubusercontent.com/Tiry38/sparradar/main/docs/pc"
echo.
echo   SparRadar - Abruf vom eigenen PC einrichten
echo   ===========================================
echo   Holt bei jedem PC-Start Müller-Angebote und Scheck-In-Prospekt
echo   und lädt sie zu SparRadar hoch. Läuft unsichtbar im Hintergrund.
echo.
if not exist "%DIR%" mkdir "%DIR%"

rem ---- 1. Python suchen, sonst installieren ----
call :findpy
if defined PYW goto :pyok
echo   [1/4] Python fehlt - wird jetzt installiert, ca. 1-2 Minuten ...
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
call :findpy
if defined PYW goto :pyok
echo.
echo   Python konnte nicht automatisch installiert werden.
echo   Bitte im Microsoft Store "Python 3.12" installieren und diese Datei nochmal starten.
pause
exit /b 1
:pyok
set "PY=%PYW:pythonw.exe=python.exe%"
echo   [1/4] Python gefunden: %PY%

rem ---- 2. GitHub-Schlüssel ----
if not exist "%DIR%\token.txt" goto :asktoken
echo.
choice /c JN /n /m "  Ein GitHub-Schlüssel ist schon gespeichert. Neuen eintragen? [J/N] "
if errorlevel 2 goto :tokenok
:asktoken
echo.
rem Schlüssel zuerst aus der Zwischenablage nehmen (Strg+V geht in der versteckten Eingabe nicht, nur Rechtsklick)
powershell -NoProfile -Command "$t=((Get-Clipboard -Raw) + '').Trim(); if($t -notmatch '^(github_pat_|ghp_)[A-Za-z0-9_]+$'){exit 1}; [IO.File]::WriteAllText($env:DIR+'\token.txt',$t); Set-Clipboard -Value ' '"
if not errorlevel 1 (
  echo   [2/4] Schlüssel aus der Zwischenablage übernommen.
  goto :tokenok
)
echo   [2/4] GitHub-Schlüssel auf github.com kopieren und hier mit RECHTSKLICK einfügen, dann Enter.
echo         Man sieht dabei nur Sternchen - das ist richtig so.
powershell -NoProfile -Command "$s=Read-Host '  Schluessel' -AsSecureString; $t=[Net.NetworkCredential]::new('',$s).Password.Trim(); if($t -notmatch '^(github_pat_|ghp_)[A-Za-z0-9_]+$'){exit 1}; [IO.File]::WriteAllText($env:DIR+'\token.txt',$t)"
if errorlevel 1 (
  echo   Das sieht nicht nach einem GitHub-Schlüssel aus - er beginnt mit github_pat_ . Nochmal:
  goto :asktoken
)
:tokenok
echo   [2/4] Schlüssel gespeichert - nur auf diesem PC.

rem ---- 3. Programm laden + Autostart ----
powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing ($env:RAW+'/start.py') -OutFile ($env:DIR+'\start.py')"
if not exist "%DIR%\start.py" (
  echo   Programm konnte nicht geladen werden - Internet da? Datei nochmal starten.
  pause
  exit /b 1
)
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\SparRadar Abruf.lnk'); $s.TargetPath=$env:PYW; $s.Arguments=[char]34+$env:DIR+'\start.py'+[char]34; $s.WorkingDirectory=$env:DIR; $s.Description='SparRadar: Angebote vom PC abrufen'; $s.Save()"
echo   [3/4] Startet ab jetzt automatisch mit Windows.

rem ---- 4. Test ----
echo.
echo   [4/4] Erster Abruf läuft, ca. 2-3 Minuten ...
echo.
"%PY%" "%DIR%\start.py" --jetzt
start "" "%PYW%" "%DIR%\start.py"
echo.
echo   Fertig. Ab jetzt läuft alles von selbst: bei jedem PC-Start und alle 3 Stunden.
echo   Protokoll: %DIR%\protokoll.txt
echo.
pause
exit /b 0

:findpy
set "PYW="
for %%V in (313 312 311 310) do if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe"
for %%V in (313 312 311 310) do if not defined PYW if exist "%ProgramFiles%\Python%%V\pythonw.exe" set "PYW=%ProgramFiles%\Python%%V\pythonw.exe"
if not defined PYW for /f "delims=" %%P in ('py -3 -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do if exist "%%P" set "PYW=%%P"
if not defined PYW for /f "delims=" %%P in ('python -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do if exist "%%P" set "PYW=%%P"
exit /b 0
