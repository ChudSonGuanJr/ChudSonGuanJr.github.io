@echo off
rem Double-click to open edit mode. Close this window to stop it.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py tools\edit.py) else (python tools\edit.py)
echo.
echo Edit mode stopped. If there is an error above, send it to me.
pause
