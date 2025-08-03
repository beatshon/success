@echo off
REM Git 설치 및 자동 동기화 설정 스크립트

title Git 설치 및 자동 동기화 설정

echo.
echo ========================================
echo    Git 설치 및 자동 동기화 설정
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

echo 🔍 Git 설치 상태 확인 중...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git이 설치되지 않았습니다.
    echo.
    echo 📥 Git을 다운로드하고 설치합니다...
    echo.
    
    REM Git 다운로드 (Chocolatey 사용)
    echo 📦 Chocolatey 패키지 매니저 설치 중...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    echo 📦 Git 설치 중...
    choco install git -y
    
    echo.
    echo ✅ Git 설치 완료!
    echo.
) else (
    echo ✅ Git이 이미 설치되어 있습니다.
    git --version
)

echo.
echo 🔧 자동 동기화 서비스 설치 중...
echo.

REM 필요한 Python 패키지 설치
echo 📦 Python 패키지 설치 중...
pip install pywin32 watchdog

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 서비스 설치
echo 🔧 동기화 서비스 설치 중...
python windows_sync_service.py install

if errorlevel 1 (
    echo ❌ 서비스 설치 실패
    pause
    exit /b 1
)

echo.
echo ✅ 자동 동기화 설정 완료!
echo.
echo 📋 다음 단계:
echo 1. 맥에서 Git 저장소 설정
echo 2. 윈도우에서 Git 저장소 클론
echo 3. 자동 동기화 서비스 시작
echo.

REM 서비스 시작 여부 확인
set /p start_service="자동 동기화 서비스를 지금 시작하시겠습니까? (y/n): "
if /i "%start_service%"=="y" (
    echo.
    echo 🚀 자동 동기화 서비스 시작 중...
    python windows_sync_service.py start
    if errorlevel 1 (
        echo ❌ 서비스 시작 실패
    ) else (
        echo ✅ 자동 동기화 서비스 시작 완료!
        echo.
        echo 🔄 이제 맥에서 코드를 수정하고 GitHub에 푸시하면
        echo    윈도우 서버에서 자동으로 동기화됩니다.
    )
)

echo.
echo 📋 서비스 관리 명령어:
echo   net start KiwoomSyncService    - 서비스 시작
echo   net stop KiwoomSyncService     - 서비스 중지
echo   sc query KiwoomSyncService     - 서비스 상태 확인
echo.

pause 