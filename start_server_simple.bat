@echo off
title Windows API Server - Simple

echo.
echo ========================================
echo    Windows API 서버 시작 (간단 버전)
echo ========================================
echo.

REM 현재 디렉토리 설정
cd /d "%~dp0"

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python을 설치하세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 필요한 디렉토리 생성
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM 패키지 설치 (조용히)
pip install flask flask-cors loguru requests watchdog --quiet

echo.
echo 🚀 서버 시작 중...
echo 📊 상태 확인: http://localhost:8080/api/health
echo ⚠️ 중지: Ctrl+C
echo.

python windows_api_server.py --host 0.0.0.0 --port 8080

echo.
echo 서버가 종료되었습니다.
pause 