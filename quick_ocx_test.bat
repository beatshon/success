@echo off
chcp 65001 >nul

echo 🔍 키움 OpenAPI OCX 등록 상태 빠른 확인
echo ========================================
echo.

:: OCX 파일 존재 확인
if exist "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX" (
    echo ✅ OCX 파일 존재
) else (
    echo ❌ OCX 파일 없음
    echo 💡 키움 OpenAPI를 설치해주세요
    pause
    exit /b 1
)

:: 레지스트리 등록 확인
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 레지스트리 등록됨
) else (
    echo ❌ 레지스트리 등록 안됨
    echo 💡 fix_ocx_registration.bat을 관리자 권한으로 실행하세요
    pause
    exit /b 1
)

:: Python 테스트
if exist "test_ocx_registration.py" (
    echo 📝 Python 테스트 실행 중...
    python test_ocx_registration.py
) else (
    echo ⚠️ Python 테스트 스크립트 없음
)

echo.
echo ✅ OCX 등록 상태 확인 완료!
pause 