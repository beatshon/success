@echo off
REM Windows 동기화 서비스 설치 스크립트

title Windows Sync Service Installer

echo.
echo ========================================
echo    Windows 동기화 서비스 설치
echo ========================================
echo.

cd /d "%~dp0"

REM 관리자 권한 확인
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 관리자 권한이 필요합니다.
    echo 이 스크립트를 관리자 권한으로 실행하세요.
    pause
    exit /b 1
)

REM Python 환경 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python을 설치하고 PATH에 추가하세요.
    pause
    exit /b 1
)

REM 필요한 패키지 설치
echo 📦 필요한 패키지 설치 중...
pip install pywin32 watchdog

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

echo.
echo 🔧 동기화 서비스 설치 중...
echo.

REM 서비스 설치
python windows_sync_service.py install

if errorlevel 1 (
    echo ❌ 서비스 설치 실패
    pause
    exit /b 1
)

echo.
echo ✅ 동기화 서비스 설치 완료!
echo.
echo 사용법:
echo   서비스 시작: python windows_sync_service.py start
echo   서비스 중지: python windows_sync_service.py stop
echo   서비스 제거: python windows_sync_service.py remove
echo   서비스 상태: python windows_sync_service.py status
echo.

REM 서비스 시작 여부 확인
set /p start_service="서비스를 지금 시작하시겠습니까? (y/n): "
if /i "%start_service%"=="y" (
    echo.
    echo 🚀 서비스 시작 중...
    python windows_sync_service.py start
    if errorlevel 1 (
        echo ❌ 서비스 시작 실패
    ) else (
        echo ✅ 서비스 시작 완료
    )
)

echo.
echo 📋 서비스 관리 명령어:
echo   net start KiwoomSyncService    - 서비스 시작
echo   net stop KiwoomSyncService     - 서비스 중지
echo   sc query KiwoomSyncService     - 서비스 상태 확인
echo.

pause 