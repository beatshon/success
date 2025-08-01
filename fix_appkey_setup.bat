@echo off
REM 키움 API 앱키 설정 문제 해결 스크립트
REM 윈도우 서버에서 실행

title Kiwoom AppKey Setup Fix

echo.
echo ========================================
echo    키움 API 앱키 설정 문제 해결
echo ========================================
echo.

echo 🔍 현재 상황 진단 중...
echo.

REM 현재 디렉토리 확인
echo 📁 현재 디렉토리: %CD%
echo.

REM 파일 존재 확인
echo 📋 파일 존재 확인 중...
if exist setup_kiwoom_appkey.bat (
    echo ✅ setup_kiwoom_appkey.bat 파일 발견
    goto :run_setup
) else (
    echo ❌ setup_kiwoom_appkey.bat 파일 없음
)

if exist test_kiwoom_with_appkey.py (
    echo ✅ test_kiwoom_with_appkey.py 파일 발견
    goto :run_python_test
) else (
    echo ❌ test_kiwoom_with_appkey.py 파일 없음
)

if exist env_example.txt (
    echo ✅ env_example.txt 파일 발견
    goto :manual_setup
) else (
    echo ❌ env_example.txt 파일 없음
)

echo.
echo 🚨 문제: 필요한 파일들이 없습니다.
echo 💡 해결 방법: 자동 동기화를 기다리거나 수동으로 설정하세요.
echo.

:wait_sync
echo ⏰ 자동 동기화 대기 중... (30초)
timeout /t 30 /nobreak >nul

echo 🔍 다시 파일 확인 중...
if exist setup_kiwoom_appkey.bat (
    echo ✅ 파일이 동기화되었습니다!
    goto :run_setup
) else (
    echo ❌ 아직 파일이 없습니다.
    goto :manual_setup
)

:run_setup
echo.
echo 🚀 setup_kiwoom_appkey.bat 실행 중...
setup_kiwoom_appkey.bat
goto :end

:run_python_test
echo.
echo 🚀 Python 테스트 실행 중...
python test_kiwoom_with_appkey.py
goto :end

:manual_setup
echo.
echo 🛠️ 수동 설정을 시작합니다.
echo.

REM .env 파일 생성
if not exist .env (
    echo 📝 .env 파일 생성 중...
    copy env_example.txt .env
    echo ✅ .env 파일 생성 완료
) else (
    echo ⚠️ .env 파일이 이미 존재합니다.
)

echo.
echo 📋 다음 단계를 따라 앱키를 설정하세요:
echo.
echo 1. .env 파일을 메모장으로 열어주세요:
echo    notepad .env
echo.
echo 2. 다음 정보를 입력하세요:
echo    KIWOOM_APP_KEY=your_actual_app_key_here
echo    KIWOOM_APP_SECRET=your_actual_app_secret_here
echo    KIWOOM_ACCESS_TOKEN=your_actual_access_token_here
echo.
echo 3. 파일을 저장하고 메모장을 닫으세요.
echo.

set /p continue="앱키 설정이 완료되면 엔터 키를 누르세요..."

echo.
echo 🧪 앱키 설정을 테스트합니다.
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 📥 Python을 설치해주세요.
    goto :end
)

REM 필요한 패키지 설치
echo 📦 필요한 패키지 설치 중...
pip install python-dotenv loguru PyQt5

echo.
echo 🚀 앱키 테스트를 실행합니다.
echo.

REM 간단한 앱키 테스트
python -c "
try:
    from config.kiwoom_api_keys import kiwoom_api_keys
    if kiwoom_api_keys.is_configured:
        print('✅ 앱키 설정이 완료되었습니다!')
        print(f'📋 앱키: {kiwoom_api_keys.get_app_key()[:10]}...')
    else:
        print('❌ 앱키 설정이 완료되지 않았습니다.')
        print('💡 .env 파일을 확인해주세요.')
except Exception as e:
    print(f'❌ 오류 발생: {e}')
"

:end
echo.
echo 🛑 문제 해결이 완료되었습니다.
pause 