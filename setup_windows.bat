@echo off
title Windows 환경 초기 설정

echo.
echo ========================================
echo    Windows 환경 초기 설정
echo    키움증권 자동매매 시스템
echo ========================================
echo.

REM 현재 디렉토리 설정
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
    echo 📥 Python 설치가 필요합니다:
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. "Download Python" 클릭
    echo 3. 설치 시 "Add Python to PATH" 반드시 체크
    echo.
    echo 설치 후 이 스크립트를 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% 설치 확인 완료
echo.

REM pip 업그레이드
echo 🔄 pip 업그레이드 중...
python -m pip install --upgrade pip --quiet
echo ✅ pip 업그레이드 완료
echo.

REM 가상환경 생성
echo 📦 가상환경 생성 중...
if exist "venv" (
    echo ⚠️ 가상환경이 이미 존재합니다.
    set /p RECREATE="재생성하시겠습니까? (y/n): "
    if /i "%RECREATE%"=="y" (
        echo 기존 가상환경 삭제 중...
        rmdir /s /q venv
        echo ✅ 기존 가상환경 삭제 완료
    ) else (
        echo 기존 가상환경을 사용합니다.
        goto :activate_venv
    )
)

python -m venv venv
if errorlevel 1 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 생성 완료

:activate_venv
REM 가상환경 활성화
echo 📦 가상환경 활성화 중...
call venv\Scripts\activate.bat
echo ✅ 가상환경 활성화 완료
echo.

REM 필요한 디렉토리 생성
echo 📁 필요한 디렉토리 생성 중...
if not exist "logs" mkdir logs
if not exist "config" mkdir config
if not exist "data" mkdir data
echo ✅ 디렉토리 생성 완료
echo.

REM 패키지 설치
echo 📦 패키지 설치 중...
echo (시간이 걸릴 수 있습니다)
echo.

if exist "requirements_windows.txt" (
    pip install -r requirements_windows.txt
) else (
    pip install flask flask-cors loguru requests watchdog pandas numpy python-dateutil
)

if errorlevel 1 (
    echo.
    echo ❌ 패키지 설치 실패
    echo.
    echo 🔧 해결 방법:
    echo 1. 인터넷 연결 확인
    echo 2. 관리자 권한으로 실행
    echo 3. 개별 패키지 설치 시도
    echo.
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료
echo.

REM 기본 설정 파일 생성
echo ⚙️ 기본 설정 파일 생성 중...
if not exist "config\hybrid_config.json" (
    echo {> config\hybrid_config.json
    echo   "windows_server": {>> config\hybrid_config.json
    echo     "host": "localhost",>> config\hybrid_config.json
    echo     "port": 8080,>> config\hybrid_config.json
    echo     "api_key": "your_api_key_here",>> config\hybrid_config.json
    echo     "timeout": 30>> config\hybrid_config.json
    echo   },>> config\hybrid_config.json
    echo   "trading": {>> config\hybrid_config.json
    echo     "max_positions": 5,>> config\hybrid_config.json
    echo     "default_trade_amount": 100000,>> config\hybrid_config.json
    echo     "update_interval": 60>> config\hybrid_config.json
    echo   }>> config\hybrid_config.json
    echo }>> config\hybrid_config.json
    echo ✅ 기본 설정 파일 생성 완료
) else (
    echo ⚙️ 설정 파일이 이미 존재합니다.
)
echo.

REM 키움 API 확인
echo 🔍 키움 API 확인 중...
echo ⚠️ 키움증권 Open API+ 설치가 필요합니다:
echo 1. https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView 접속
echo 2. Open API+ 다운로드 및 설치
echo 3. 키움증권 계정으로 로그인
echo 4. Open API+ 사용 신청
echo.

echo ========================================
echo ✅ Windows 환경 초기 설정 완료!
echo ========================================
echo.
echo 🚀 다음 단계:
echo 1. 키움증권 Open API+ 설치 및 로그인
echo 2. start_windows_server.bat 실행
echo 3. http://localhost:8080/api/health 접속하여 서버 확인
echo.
echo 📝 참고 문서:
echo - WINDOWS_SETUP.md: 상세 설정 가이드
echo - HYBRID_SYSTEM_README.md: 하이브리드 시스템 사용법
echo.
pause 