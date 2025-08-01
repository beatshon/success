@echo off
REM Windows 자동 풀 스크립트
REM GitHub에서 변경사항을 자동으로 가져옴

title Windows Auto Pull

echo.
echo ========================================
echo    Windows 자동 풀 시스템
echo ========================================
echo.

cd /d "%~dp0"

:loop
echo.
echo 🔄 GitHub에서 변경사항 확인 중...
echo.

git fetch origin
git status -uno

if git status -uno | findstr "behind" >nul; then
    echo.
    echo 📥 새로운 변경사항 발견!
    echo.
    
    git pull origin main
    
    if errorlevel 1 (
        echo ❌ 풀 실패
    ) else (
        echo ✅ 풀 완료
        echo.
        echo 🔄 Windows 서버 재시작 중...
        echo.
        
        REM 서버 재시작 (선택사항)
        REM taskkill /f /im python.exe >nul 2>&1
        REM start /b python windows_api_server.py --host 0.0.0.0 --port 8080
    )
else
    echo ✅ 최신 상태입니다.
fi

echo.
echo ⏰ 30초 후 다시 확인합니다...
timeout /t 30 /nobreak >nul

goto loop
