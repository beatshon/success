@echo off
REM 개선된 동기화 스크립트 시작
REM 윈도우 서버에서 사용

title Kiwoom Trading - Improved Sync

echo.
echo ========================================
echo    키움 트레이딩 - 개선된 동기화 시스템
echo ========================================
echo.

cd /d "%~dp0"

echo 🔍 현재 상태 확인 중...
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 📥 Python을 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 필요한 패키지 확인
echo 📦 필요한 패키지 확인 중...
python -c "import loguru" >nul 2>&1
if errorlevel 1 (
    echo 📥 loguru 패키지 설치 중...
    pip install loguru
)

echo.
echo 🚀 개선된 동기화 스크립트 시작...
echo.

REM 개선된 Python 스크립트 실행
python windows_sync_monitor.py

echo.
echo 🛑 동기화 스크립트가 종료되었습니다.
pause 