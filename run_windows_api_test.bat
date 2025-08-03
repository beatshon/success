@echo off
chcp 65001 >nul
echo ========================================
echo 윈도우 서버 API 테스트 실행 스크립트
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
python -c "import requests, json, logging" 2>nul
if %errorlevel% neq 0 (
    echo 필요한 패키지 설치 중...
    pip install requests
    echo 패키지 설치 완료
    echo.
)

:: logs 디렉토리 생성
if not exist "logs" (
    echo logs 디렉토리 생성 중...
    mkdir logs
)

:: API 테스트 실행
echo API 테스트 시작...
echo ========================================
python windows_api_test.py

:: 테스트 결과 확인
echo.
echo ========================================
echo 테스트 완료!
echo.
echo 결과 파일 위치:
echo - 로그 파일: logs\windows_api_test.log
echo - 결과 파일: logs\windows_api_test_results_*.json
echo.

:: 최신 결과 파일 표시
for /f "delims=" %%i in ('dir /b /od logs\windows_api_test_results_*.json 2^>nul') do set latest_result=%%i
if defined latest_result (
    echo 최신 결과 파일: %latest_result%
    echo.
    echo 결과 미리보기:
    python -c "import json; data=json.load(open('logs/%latest_result%', 'r', encoding='utf-8')); print('테스트 시간:', data['timestamp']); print('테스트 개수:', len(data['tests']))"
)

echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul 