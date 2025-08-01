@echo off
chcp 65001 >nul
REM Windows 환경 설정 스크립트 (수정된 버전)

title Windows Setup - Kiwoom Trading

echo.
echo ========================================
echo    Windows 환경 설정
echo ========================================
echo.

cd /d "%~dp0"

echo 1. Python 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 📥 https://www.python.org/downloads/ 에서 설치하세요.
    pause
    exit /b 1
) else (
    echo ✅ Python 설치 확인됨
    python --version
)

echo.
echo 2. 가상환경 생성 중...
if not exist "venv" (
    python -m venv venv
    echo ✅ 가상환경 생성 완료
) else (
    echo ✅ 가상환경 이미 존재
)

echo.
echo 3. 가상환경 활성화...
call venv\Scripts\activate.bat

echo.
echo 4. 필요한 패키지 설치 중...
pip install --upgrade pip
pip install -r requirements_windows.txt

echo.
echo 5. 설정 파일 확인...
if not exist "config" mkdir config
if not exist "config\windows_server.conf" (
    echo # Windows 서버 설정 > config\windows_server.conf
    echo host = 0.0.0.0 >> config\windows_server.conf
    echo port = 8080 >> config\windows_server.conf
    echo ✅ 기본 설정 파일 생성
) else (
    echo ✅ 설정 파일 이미 존재
)

echo.
echo 6. 로그 폴더 생성...
if not exist "logs" mkdir logs

echo.
echo ========================================
echo    설정 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. 키움증권 Open API+ 설치
echo 2. start_windows_server.bat 실행
echo.
echo 키움증권 API 다운로드:
echo https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
echo.

pause 