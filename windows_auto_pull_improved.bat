@echo off
REM Windows 자동 풀 스크립트 (개선된 버전)
REM GitHub에서 변경사항을 자동으로 가져옴

title Windows Auto Pull - Improved

echo.
echo ========================================
echo    Windows 자동 풀 시스템 (개선된 버전)
echo ========================================
echo.

cd /d "%~dp0"

:loop
echo.
echo [%date% %time%] 🔄 GitHub에서 변경사항 확인 중...
echo.

REM 현재 상태 저장
git fetch origin
set "current_status="
for /f "tokens=*" %%i in ('git status -uno') do (
    set "current_status=!current_status! %%i"
)

REM 변경사항 확인
if git status -uno | findstr "behind" >nul; then
    echo.
    echo [%date% %time%] 📥 새로운 변경사항 발견!
    echo [%date% %time%] 🔄 변경사항을 가져오는 중...
    echo.
    
    git pull origin main
    
    if errorlevel 1 (
        echo [%date% %time%] ❌ 풀 실패
        echo [%date% %time%] 오류 코드: %errorlevel%
    ) else (
        echo [%date% %time%] ✅ 풀 완료
        echo [%date% %time%] 📋 변경된 파일:
        git diff --name-only HEAD~1 HEAD
        
        echo.
        echo [%date% %time%] 🔄 Windows 서버 재시작 중...
        echo.
        
        REM 서버 재시작 (선택사항)
        REM taskkill /f /im python.exe >nul 2>&1
        REM start /b python windows_api_server.py --host 0.0.0.0 --port 8080
    )
else
    echo [%date% %time%] ✅ 최신 상태입니다.
    echo [%date% %time%] 📊 현재 상태: 최신 커밋과 동기화됨
fi

echo.
echo [%date% %time%] ⏰ 30초 후 다시 확인합니다...
echo ========================================
timeout /t 30 /nobreak >nul

goto loop 