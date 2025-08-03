@echo off
REM Windows 서버 동기화 관리자 시작 스크립트

title Windows Sync Manager

echo.
echo ========================================
echo    Windows 서버 동기화 관리자
echo ========================================
echo.

cd /d "%~dp0"

REM Python 환경 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python을 설치하고 PATH에 추가하세요.
    pause
    exit /b 1
)

REM 필요한 패키지 설치 확인
echo 🔍 필요한 패키지 확인 중...
python -c "import watchdog" >nul 2>&1
if errorlevel 1 (
    echo 📦 watchdog 패키지 설치 중...
    pip install watchdog
)

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

echo.
echo 🚀 Windows 서버 동기화 관리자 시작
echo.

REM 동기화 관리자 실행
python windows_sync_manager.py

pause 