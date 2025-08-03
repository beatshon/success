@echo off
chcp 65001 >nul
echo ========================================
echo 윈도우 서버에서 맥 파일 가져오기
echo ========================================
echo.

:: 현재 디렉토리 확인
echo 현재 작업 디렉토리: %CD%
echo.

:: 설정 파일 확인
if not exist "config\windows_server.conf" (
    echo ❌ 설정 파일을 찾을 수 없습니다: config\windows_server.conf
    echo 맥에서 설정 파일을 먼저 전송해주세요.
    pause
    exit /b 1
)

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

:: 백업 디렉토리 생성
set BACKUP_DIR=backup_windows_files\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
echo 백업 디렉토리 생성: %BACKUP_DIR%
mkdir "%BACKUP_DIR%"
echo.

:: 현재 파일들 백업
echo 현재 파일들 백업 중...
xcopy /E /I /Y *.py "%BACKUP_DIR%\"
xcopy /E /I /Y *.bat "%BACKUP_DIR%\"
xcopy /E /I /Y *.sh "%BACKUP_DIR%\"
xcopy /E /I /Y *.md "%BACKUP_DIR%\"
xcopy /E /I /Y *.txt "%BACKUP_DIR%\"
xcopy /E /I /Y config "%BACKUP_DIR%\config\"
xcopy /E /I /Y templates "%BACKUP_DIR%\templates\"
echo 백업 완료
echo.

:: 맥에서 파일 가져오기 (SSH를 통한 rsync 또는 scp)
echo 맥에서 파일 가져오기 시작...
echo.

:: 설정 파일에서 맥 정보 읽기 (예시)
set MAC_HOST=192.168.1.50
set MAC_USER=macuser
set MAC_PATH=/Users/macuser/Desktop/kiwoom_trading

echo 맥 서버 정보:
echo   호스트: %MAC_HOST%
echo   사용자: %MAC_USER%
echo   경로: %MAC_PATH%
echo.

:: SSH 연결 테스트
echo SSH 연결 테스트 중...
ssh -o ConnectTimeout=10 %MAC_USER%@%MAC_HOST% "echo 'SSH 연결 성공'"
if %errorlevel% neq 0 (
    echo ❌ SSH 연결 실패
    echo 맥 서버 정보를 확인해주세요.
    pause
    exit /b 1
)
echo ✅ SSH 연결 성공
echo.

:: 파일 가져오기
echo 파일 가져오기 시작...
echo ========================================

:: 주요 파일들 가져오기
echo 1. Python 파일들 가져오기...
scp -r %MAC_USER%@%MAC_HOST%:%MAC_PATH%/*.py .

echo 2. 설정 파일들 가져오기...
scp -r %MAC_USER%@%MAC_HOST%:%MAC_PATH%/config .

echo 3. 템플릿 파일들 가져오기...
scp -r %MAC_USER%@%MAC_HOST%:%MAC_PATH%/templates .

echo 4. 요구사항 파일들 가져오기...
scp %MAC_USER%@%MAC_HOST%:%MAC_PATH%/requirements*.txt .

echo 5. 실행 스크립트들 가져오기...
scp %MAC_USER%@%MAC_HOST%:%MAC_PATH%/*.bat .
scp %MAC_USER%@%MAC_HOST%:%MAC_PATH%/*.sh .

echo 6. 문서 파일들 가져오기...
scp %MAC_USER%@%MAC_HOST%:%MAC_PATH%/*.md .

echo.
echo ========================================
echo 파일 가져오기 완료!
echo.

:: 파일 권한 설정
echo 파일 권한 설정 중...
icacls *.bat /grant Everyone:F
icacls *.sh /grant Everyone:F
echo 권한 설정 완료
echo.

:: Python 환경 업데이트
echo Python 환경 업데이트 중...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements_windows.txt
    echo 패키지 업데이트 완료
) else (
    echo 가상환경이 없습니다. 새로 생성하시겠습니까?
    set /p CREATE_VENV="가상환경을 생성하시겠습니까? (y/n): "
    if /i "%CREATE_VENV%"=="y" (
        python -m venv venv
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
        pip install -r requirements_windows.txt
        echo 가상환경 생성 및 패키지 설치 완료
    )
)
echo.

:: 동기화 후 상태 확인
echo 동기화 후 상태 확인...
echo 파일 개수: 
dir /B *.py | find /c /v ""
echo.
echo 최근 수정된 파일들:
forfiles /M *.py /D -1 /C "cmd /c echo @file" 2>nul | head -5
echo.

:: 로그 생성
set LOG_FILE=logs\pull_from_mac_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%
mkdir logs 2>nul
echo 동기화 로그 - %date% %time% > "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo 맥 서버: %MAC_HOST% >> "%LOG_FILE%"
echo 사용자: %MAC_USER% >> "%LOG_FILE%"
echo 경로: %MAC_PATH% >> "%LOG_FILE%"
echo 백업 위치: %BACKUP_DIR% >> "%LOG_FILE%"

echo.
echo ========================================
echo 동기화 완료!
echo.
echo 결과:
echo - 백업 위치: %BACKUP_DIR%
echo - 로그 파일: %LOG_FILE%
echo.
echo 다음 단계:
echo 1. API 서버 실행: start_windows_api_server.bat
echo 2. API 테스트 실행: run_windows_api_test.bat
echo.

echo 아무 키나 누르면 종료됩니다...
pause >nul 