@echo off
chcp 65001 >nul
echo ========================================
echo 윈도우 서버 API 서버 실행 스크립트
echo ========================================
echo.

:: 현재 디렉토리 확인
echo 현재 작업 디렉토리: %CD%
echo.

:: Python 환경 확인
echo Python 환경 확인 중...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python을 설치해주세요.
    pause
    exit /b 1
)
echo.

:: 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo 가상환경 활성화 완료
    echo.
)

:: 필요한 패키지 설치 확인
echo 필요한 패키지 설치 확인 중...
python -c "import flask, flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo 필요한 패키지 설치 중...
    pip install flask flask-cors
    echo 패키지 설치 완료
    echo.
)

:: logs 디렉토리 생성
if not exist "logs" (
    echo logs 디렉토리 생성 중...
    mkdir logs
)

:: 포트 사용 확인
echo 포트 8080 사용 확인 중...
netstat -an | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo ⚠️ 포트 8080이 이미 사용 중입니다.
    echo 다른 프로세스를 종료하거나 포트를 변경해주세요.
    pause
    exit /b 1
)
echo ✅ 포트 8080 사용 가능
echo.

:: API 서버 시작
echo API 서버 시작 중...
echo ========================================
echo 서버 주소: http://localhost:8080
echo API 문서: http://localhost:8080/status
echo 테스트: http://localhost:8080/api/test/connection
echo ========================================
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

python start_windows_api_server.py

echo.
echo 서버가 종료되었습니다.
pause 