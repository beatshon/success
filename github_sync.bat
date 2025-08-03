@echo off
chcp 65001 >nul
echo ========================================
echo GitHub 동기화 실행 스크립트
echo ========================================
echo.

:: 현재 디렉토리 확인
echo 현재 작업 디렉토리: %CD%
echo.

:: Git 설치 확인
echo Git 설치 확인 중...
git --version
if %errorlevel% neq 0 (
    echo ❌ Git이 설치되지 않았습니다.
    echo Git을 설치해주세요: https://git-scm.com/
    pause
    exit /b 1
)
echo ✅ Git 설치 확인됨
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
echo ✅ Python 설치 확인됨
echo.

:: 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo 가상환경 활성화 완료
    echo.
)

:: logs 디렉토리 생성
if not exist "logs" (
    echo logs 디렉토리 생성 중...
    mkdir logs
)

:: GitHub 동기화 실행
echo GitHub 동기화 시작...
echo ========================================

if "%1"=="push" (
    echo GitHub로 푸시 중...
    python github_sync_manager.py push
) else if "%1"=="pull" (
    echo GitHub에서 풀 중...
    python github_sync_manager.py pull
) else if "%1"=="status" (
    echo Git 상태 확인 중...
    python github_sync_manager.py status
) else if "%1"=="backup" (
    echo 백업 브랜치 생성 중...
    python github_sync_manager.py backup
) else (
    echo 사용법:
    echo   github_sync.bat push   - GitHub로 푸시
    echo   github_sync.bat pull   - GitHub에서 풀
    echo   github_sync.bat status - 상태 확인
    echo   github_sync.bat backup - 백업 브랜치 생성
    echo.
    echo 기본 동기화 (풀 후 푸시)...
    python github_sync_manager.py pull
    python github_sync_manager.py push
)

echo.
echo ========================================
echo GitHub 동기화 완료!
echo.

echo 아무 키나 누르면 종료됩니다...
pause >nul 