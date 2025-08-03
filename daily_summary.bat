@echo off
chcp 65001 >nul
echo ========================================
echo 📊 일일 요약 리포트 자동 실행
echo ========================================
echo 실행 시간: %date% %time%
echo.

cd /d "%~dp0"

:: 가상환경 활성화 (경로는 실제 환경에 맞게 수정)
call venv\Scripts\activate.bat

:: 일일 요약 실행
python cross_platform_trader.py --daily-summary

:: 실행 결과 확인
if %errorlevel% equ 0 (
    echo ✅ 일일 요약 실행 완료
) else (
    echo ❌ 일일 요약 실행 실패 (오류 코드: %errorlevel%)
)

:: 가상환경 비활성화
deactivate

echo.
echo ========================================
echo 📊 일일 요약 실행 종료
echo ========================================
pause 