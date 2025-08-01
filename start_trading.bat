@echo off
chcp 65001 >nul
title 키움 자동매매 시스템

echo ========================================
echo 키움 자동매매 시스템 시작
echo ========================================
echo.

echo 현재 시간: %date% %time%
echo.

REM 환경 변수 설정
set LANG=ko_KR.UTF-8
set LC_ALL=ko_KR.UTF-8

REM Python 환경 확인
echo 🔍 Python 환경 확인 중...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    pause
    exit /b 1
)

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 🔄 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 키움 API 연결 확인
echo 🔗 키움 API 연결 확인 중...
python windows_test.py
if %errorlevel% neq 0 (
    echo ❌ 키움 API 연결에 실패했습니다.
    echo 키움 영웅문이 실행 중인지 확인해주세요.
    pause
    exit /b 1
)

echo.
echo 🚀 자동매매 시스템 시작 중...
echo.

REM GUI 모드로 실행
echo GUI 모드로 실행합니다...
python gui_trader.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ GUI 모드 실행 실패. 콘솔 모드로 시도합니다...
    echo.
    python auto_trader.py
)

echo.
echo 자동매매 시스템이 종료되었습니다.
echo 아무 키나 누르면 종료됩니다...
pause >nul 