@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🧹 키움 OpenAPI 완전 제거 및 정리
echo ========================================
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 관리자 권한이 필요합니다.
    echo 💡 이 파일을 우클릭하고 "관리자 권한으로 실행"을 선택해주세요.
    pause
    exit /b 1
)

echo ✅ 관리자 권한 확인됨
echo.

:: 1단계: 프로그램 제거
echo 🔍 1단계: 프로그램 제거 중...
echo.

echo 📋 제거할 프로그램 목록:
wmic product where "name like 'Kiwoom%'" get name,version /format:list
wmic product where "name like 'OpenAPI%'" get name,version /format:list

echo.
echo 🗑️ 프로그램 제거 중...
wmic product where "name like 'Kiwoom%'" call uninstall /nointeractive
wmic product where "name like 'OpenAPI%'" call uninstall /nointeractive

echo ✅ 프로그램 제거 완료
echo.

:: 2단계: 파일 삭제
echo 🔍 2단계: 파일 삭제 중...
echo.

set "PATHS_TO_REMOVE=C:\Program Files (x86)\Kiwoom OpenAPI C:\Program Files\Kiwoom OpenAPI %APPDATA%\Kiwoom %LOCALAPPDATA%\Kiwoom %TEMP%\Kiwoom*"

for %%p in (%PATHS_TO_REMOVE%) do (
    if exist "%%p" (
        echo 🗑️ 삭제 중: %%p
        rmdir /s /q "%%p" 2>nul
        if !errorLevel! equ 0 (
            echo ✅ 삭제 완료: %%p
        ) else (
            echo ⚠️ 삭제 실패: %%p (권한 문제일 수 있음)
        )
    ) else (
        echo ⚠️ 경로 없음: %%p
    )
)

echo.

:: 3단계: 레지스트리 정리
echo 🔍 3단계: 레지스트리 정리 중...
echo.

echo 📝 레지스트리 키 삭제 중...

:: 레지스트리 키 삭제
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI.OCX" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Kiwoom" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Kiwoom" /f >nul 2>&1

echo ✅ 레지스트리 정리 완료
echo.

:: 4단계: 임시 파일 정리
echo 🔍 4단계: 임시 파일 정리 중...
echo.

echo 🗑️ 임시 파일 삭제 중...
del /q /f %TEMP%\*.* >nul 2>&1
del /q /f %TMP%\*.* >nul 2>&1

echo ✅ 임시 파일 정리 완료
echo.

:: 5단계: 시스템 정리
echo 🔍 5단계: 시스템 정리 중...
echo.

echo 🧹 Windows 임시 파일 정리 중...
cleanmgr /sagerun:1 >nul 2>&1

echo ✅ 시스템 정리 완료
echo.

:: 완료 메시지
echo ========================================
echo 🎉 키움 OpenAPI 완전 제거 및 정리 완료!
echo ========================================
echo.
echo ✅ 수행된 작업:
echo 1. 프로그램 제거
echo 2. 파일 삭제
echo 3. 레지스트리 정리
echo 4. 임시 파일 정리
echo 5. 시스템 정리
echo.
echo 💡 다음 단계:
echo 1. 시스템 재부팅
echo 2. 키움 OpenAPI 새로 설치
echo 3. 관리자 권한으로 설치
echo.
echo 🔄 시스템을 재부팅하시겠습니까? (Y/N)
set /p reboot_choice=

if /i "%reboot_choice%"=="Y" (
    echo 🔄 시스템 재부팅 중...
    shutdown /r /t 10 /c "키움 OpenAPI 재설치를 위해 시스템을 재부팅합니다."
) else (
    echo 💡 수동으로 재부팅 후 키움 OpenAPI를 새로 설치해주세요.
)

echo.
pause 