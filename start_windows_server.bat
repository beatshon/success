@echo off
REM Windows API 서버 시작 배치 파일
REM 키움증권 API 자동매매 시스템

title Windows API Server - 키움증권 자동매매

echo.
echo ========================================
echo    Windows API 서버 시작
echo    키움증권 자동매매 시스템
echo ========================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"
echo 📁 현재 디렉토리: %CD%
echo.

REM Python 설치 확인
echo 🔍 Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python이 설치되지 않았습니다.
    echo.
    echo 📥 Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. "Download Python" 클릭
    echo 3. 설치 시 "Add Python to PATH" 체크
    echo.
    echo 설치 후 이 배치 파일을 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% 설치 확인 완료
echo.

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo ✅ 가상환경 활성화 완료
) else (
    echo ⚠️ 가상환경이 없습니다. 시스템 Python을 사용합니다.
    echo.
    echo 💡 가상환경 생성 권장:
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install -r requirements.txt
    echo.
)

echo.

REM 필요한 패키지 설치
echo 📦 필요한 패키지 설치 중...
echo (처음 실행 시 시간이 걸릴 수 있습니다)
echo.

pip install flask flask-cors loguru requests watchdog --quiet
if errorlevel 1 (
    echo.
    echo ❌ 패키지 설치 실패
    echo.
    echo 🔧 해결 방법:
    echo 1. 인터넷 연결 확인
    echo 2. 관리자 권한으로 실행
    echo 3. pip 업그레이드: python -m pip install --upgrade pip
    echo.
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료
echo.

REM 디렉토리 생성
if not exist "logs" (
    echo 📁 로그 디렉토리 생성...
    mkdir logs
)

if not exist "config" (
    echo ⚙️ 설정 디렉토리 생성...
    mkdir config
)

echo.

REM 포트 사용 확인
echo 🔍 포트 8080 사용 확인 중...
netstat -ano | findstr :8080 >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ⚠️ 포트 8080이 이미 사용 중입니다.
    echo.
    echo 🔧 해결 방법:
    echo 1. 기존 서버 프로세스 종료
    echo 2. 다른 포트 사용 (--port 8081)
    echo.
    set /p CONTINUE="계속 진행하시겠습니까? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo 서버 시작을 취소했습니다.
        pause
        exit /b 1
    )
    echo.
)

echo.

REM 서버 시작
echo 🚀 Windows API 서버 시작...
echo.
echo 📊 서버 정보:
echo    호스트: 0.0.0.0 (모든 IP에서 접근 가능)
echo    포트: 8080
echo    상태: http://localhost:8080/api/health
echo.
echo 📝 로그 파일: logs\windows_api_server.log
echo.
echo ⚠️ 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
echo ========================================
echo.

REM 서버 실행
python windows_api_server.py --host 0.0.0.0 --port 8080

echo.
echo ========================================
echo 서버가 종료되었습니다.
echo.
echo 💡 서버가 예기치 않게 종료된 경우:
echo 1. 로그 파일 확인: logs\windows_api_server.log
echo 2. 키움증권 Open API+ 로그인 상태 확인
echo 3. 방화벽 설정 확인
echo.
pause 