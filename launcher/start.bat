@echo off
REM ==========================================
REM  ZZZ Stats Launcher - PyInstaller不要版
REM ==========================================

setlocal
cd /d "%~dp0"

REM pythonw.exe があればコンソールなしで起動（綺麗）
where pythonw.exe >nul 2>&1
if %errorlevel% == 0 (
    start "" pythonw.exe "ZZZ_Stats.pyw"
    exit /b 0
)

REM フォールバック: python.exe
where python.exe >nul 2>&1
if %errorlevel% == 0 (
    start "" python.exe "ZZZ_Stats.pyw"
    exit /b 0
)

echo Pythonが見つかりませんでした。
echo  https://www.python.org/downloads/ からインストールしてください。
pause
