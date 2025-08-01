@echo off
chcp 65001 >nul
echo ========================================
echo 키움 자동매매 시스템 Windows 테스트
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

REM 키움 API 테스트 실행
echo 🚀 키움 API 테스트 시작...
python windows_test.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ 테스트가 성공적으로 완료되었습니다!
    echo 이제 자동매매 시스템을 실행할 수 있습니다.
) else (
    echo.
    echo ❌ 테스트 중 오류가 발생했습니다.
    echo 로그를 확인하고 문제를 해결해주세요.
)

echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul 