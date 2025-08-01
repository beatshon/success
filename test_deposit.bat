@echo off
chcp 65001 >nul
title 키움 예수금 조회 테스트

echo ========================================
echo 키움 예수금 조회 테스트
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
echo 🚀 예수금 조회 테스트 시작...
echo.
echo ⚠️ 주의사항:
echo 1. 키움 영웅문이 실행 중이어야 합니다.
echo 2. 영웅문에 로그인되어 있어야 합니다.
echo 3. 모의투자 계좌가 있어야 합니다.
echo.

REM 예수금 조회 테스트 실행
python test_deposit.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ 예수금 조회 테스트가 성공적으로 완료되었습니다!
    echo.
    echo 이제 자동매매 시스템에서 실제 계좌 정보를 사용할 수 있습니다.
    echo.
) else (
    echo.
    echo ❌ 예수금 조회 테스트 중 오류가 발생했습니다.
    echo.
    echo 문제 해결 방법:
    echo 1. 키움 영웅문이 실행 중인지 확인
    echo 2. 영웅문에 로그인되어 있는지 확인
    echo 3. 모의투자 계좌가 있는지 확인
    echo 4. Open API+ 사용 신청이 승인되었는지 확인
    echo.
)

echo 테스트 결과를 확인하려면 logs 폴더를 열어주세요.
echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul 