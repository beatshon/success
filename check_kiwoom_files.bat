@echo off
chcp 65001 >nul

echo 🔍 키움 OpenAPI 파일 존재 여부 확인
echo ========================================
echo.

:: 기본 설치 경로 확인
set "KIWOOM_PATH=C:\Program Files (x86)\Kiwoom OpenAPI"
set "KIWOOM_PATH_64=C:\Program Files\Kiwoom OpenAPI"

echo 📁 기본 설치 경로 확인:
echo.

:: 32비트 경로 확인
if exist "%KIWOOM_PATH%" (
    echo ✅ 32비트 경로 존재: %KIWOOM_PATH%
    echo.
    echo 📋 파일 목록:
    dir "%KIWOOM_PATH%\*.ocx" /b 2>nul
    dir "%KIWOOM_PATH%\*.dll" /b 2>nul
    dir "%KIWOOM_PATH%\*.exe" /b 2>nul
) else (
    echo ❌ 32비트 경로 없음: %KIWOOM_PATH%
)

echo.

:: 64비트 경로 확인
if exist "%KIWOOM_PATH_64%" (
    echo ✅ 64비트 경로 존재: %KIWOOM_PATH_64%
    echo.
    echo 📋 파일 목록:
    dir "%KIWOOM_PATH_64%\*.ocx" /b 2>nul
    dir "%KIWOOM_PATH_64%\*.dll" /b 2>nul
    dir "%KIWOOM_PATH_64%\*.exe" /b 2>nul
) else (
    echo ❌ 64비트 경로 없음: %KIWOOM_PATH_64%
)

echo.

:: 전체 시스템에서 키움 파일 검색
echo 🔍 전체 시스템에서 키움 파일 검색 중...
echo (시간이 걸릴 수 있습니다)
echo.

for /f "delims=" %%i in ('dir /s /b "C:\*kiwoom*" 2^>nul ^| findstr /i "\.ocx\|\.dll\|\.exe"') do (
    echo 발견: %%i
)

echo.
echo ========================================
echo 📊 검색 완료
echo.

:: 설치 권장사항
echo 💡 설치 권장사항:
echo 1. 키움 OpenAPI가 설치되지 않은 경우:
echo    - https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
echo    - 관리자 권한으로 설치
echo.
echo 2. 파일이 다른 경로에 있는 경우:
echo    - 발견된 경로를 사용하여 regsvr32 실행
echo.
echo 3. 파일이 손상된 경우:
echo    - 키움 OpenAPI 재설치
echo.

pause 