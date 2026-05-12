@echo off
REM ==========================================
REM  ZZZ Stats - 必要ライブラリのセットアップ
REM  ※すでに入っている場合は実行不要
REM ==========================================

setlocal

echo.
echo ========================================
echo  ZZZ Stats セットアップ
echo ========================================
echo.

echo Pythonの確認中...
python --version
if errorlevel 1 (
    echo Pythonがインストールされていません。
    echo  https://www.python.org/downloads/ からインストールしてください。
    pause
    exit /b 1
)
echo.

echo 必要ライブラリのインストール中...
echo  ※"pip is not recognized" エラー回避のため python -m pip 経由で実行
echo.

python -m pip install --user requests Pillow beautifulsoup4
if errorlevel 1 (
    echo.
    echo ライブラリのインストールに失敗しました。
    echo.
    echo  ネットワーク制限がある場合は、信頼するホストを指定して再実行：
    echo  python -m pip install --user --trusted-host pypi.org --trusted-host files.pythonhosted.org requests Pillow beautifulsoup4
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  セットアップ完了!
echo ========================================
echo.
echo  ZZZ_Stats起動.bat をダブルクリックで起動できます。
echo.
pause
