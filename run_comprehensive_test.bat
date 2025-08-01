@echo off
chcp 65001 >nul
title 키움 자동매매 시스템 종합 테스트

echo ========================================
echo 키움 자동매매 시스템 종합 테스트
echo ========================================
echo.

echo 현재 시간: %date% %time%
echo.

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

REM 필요한 패키지 설치 확인
echo 📦 패키지 설치 확인 중...
pip install -r requirements.txt

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

echo.
echo 🚀 종합 테스트 시작...
echo.

REM 종합 테스트 실행
python comprehensive_test.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ 종합 테스트가 성공적으로 완료되었습니다!
    echo.
    echo 다음 단계:
    echo 1. 키움 영웅문을 실행하고 로그인하세요
    echo 2. start_trading.bat를 실행하여 자동매매를 시작하세요
    echo.
) else (
    echo.
    echo ❌ 종합 테스트 중 오류가 발생했습니다.
    echo logs 폴더의 테스트 리포트를 확인해주세요.
    echo.
)

echo 테스트 결과를 확인하려면 logs 폴더를 열어주세요.
echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul 