@echo off
REM 네트워크 공유 폴더 기반 자동 동기화 설정

title 네트워크 공유 폴더 동기화 설정

echo.
echo ========================================
echo    네트워크 공유 폴더 동기화 설정
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

echo 🔧 네트워크 공유 폴더 설정 중...
echo.

REM 현재 폴더를 네트워크 공유로 설정
echo 📁 현재 폴더를 네트워크 공유로 설정 중...
net share KiwoomTrading="%CD%" /GRANT:Everyone,FULL /REMARK:"Kiwoom Trading Project"

if errorlevel 1 (
    echo ❌ 네트워크 공유 설정 실패
    pause
    exit /b 1
)

echo ✅ 네트워크 공유 설정 완료!
echo.

REM Windows 방화벽 설정
echo 🔥 Windows 방화벽 설정 중...
netsh advfirewall firewall add rule name="Kiwoom Trading Sync" dir=in action=allow protocol=TCP localport=445

echo ✅ 방화벽 설정 완료!
echo.

REM 파일 감시 서비스 설정
echo 🔧 파일 감시 서비스 설정 중...

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 필요한 패키지 설치
echo 📦 Python 패키지 설치 중...
pip install watchdog

echo.
echo ✅ 네트워크 공유 폴더 동기화 설정 완료!
echo.
echo 📋 사용 방법:
echo 1. 맥에서 네트워크 드라이브 연결: smb://[윈도우_IP]/KiwoomTrading
echo 2. 맥에서 파일을 수정하면 자동으로 윈도우에 반영됩니다
echo 3. 윈도우에서 파일 감시 서비스 실행: python windows_sync_manager.py auto
echo.

REM 파일 감시 서비스 시작 여부 확인
set /p start_watch="파일 감시 서비스를 지금 시작하시겠습니까? (y/n): "
if /i "%start_watch%"=="y" (
    echo.
    echo 🚀 파일 감시 서비스 시작 중...
    start /b python windows_sync_manager.py auto
    echo ✅ 파일 감시 서비스 시작 완료!
    echo.
    echo 🔄 이제 맥에서 네트워크 공유 폴더의 파일을 수정하면
    echo    윈도우에서 자동으로 감지하고 동기화합니다.
)

echo.
echo 📋 네트워크 공유 정보:
echo   공유 이름: KiwoomTrading
echo   경로: %CD%
echo   접근 권한: 모든 사용자 (읽기/쓰기)
echo.

pause 