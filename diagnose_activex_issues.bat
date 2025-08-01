@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🔍 ActiveX 컨트롤 설치 문제 진단 도구
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

:: 1단계: 시스템 정보 확인
echo 🔍 1단계: 시스템 정보 확인 중...
echo.

echo 📊 운영체제 정보:
ver
echo.

echo 📊 시스템 아키텍처:
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    echo ✅ 64비트 시스템
) else (
    echo ⚠️ 32비트 시스템
)
echo.

:: 2단계: ActiveX 컨트롤 설정 확인
echo 🔍 2단계: ActiveX 컨트롤 설정 확인 중...
echo.

echo 📊 Internet Explorer 보안 설정:
reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1001 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ IE 보안 설정 확인 가능
) else (
    echo ❌ IE 보안 설정 확인 불가
)

echo 📊 ActiveX 컨트롤 다운로드 설정:
reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1001 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ ActiveX 다운로드 설정 확인 가능
) else (
    echo ❌ ActiveX 다운로드 설정 확인 불가
)
echo.

:: 3단계: 키움 OpenAPI 파일 상태 확인
echo 🔍 3단계: 키움 OpenAPI 파일 상태 확인 중...
echo.

set "KIWOOM_PATHS=C:\Program Files (x86)\Kiwoom OpenAPI C:\Program Files\Kiwoom OpenAPI"
set "OCX_FILES=KHOPENAPI.OCX KHOPENAPI.dll"

for %%p in (%KIWOOM_PATHS%) do (
    if exist "%%p" (
        echo ✅ 경로 존재: %%p
        for %%f in (%OCX_FILES%) do (
            if exist "%%p\%%f" (
                echo   ✅ %%f
                for %%A in ("%%p\%%f") do (
                    echo     📊 크기: %%~zA bytes
                    echo     📅 수정일: %%~tA
                )
            ) else (
                echo   ❌ %%f (누락)
            )
        )
    ) else (
        echo ❌ 경로 없음: %%p
    )
)
echo.

:: 4단계: 레지스트리 등록 상태 확인
echo 🔍 4단계: 레지스트리 등록 상태 확인 중...
echo.

echo 📊 OCX 등록 상태:
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ OCX 레지스트리 등록됨
) else (
    echo ❌ OCX 레지스트리 등록 안됨
)

echo 📊 키움 소프트웨어 등록:
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Kiwoom" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 키움 소프트웨어 등록됨
) else (
    echo ❌ 키움 소프트웨어 등록 안됨
)
echo.

:: 5단계: 의존성 파일 확인
echo 🔍 5단계: 의존성 파일 확인 중...
echo.

set "DEPENDENCIES=msvcp140.dll vcruntime140.dll msvcr140.dll"
set "SYSTEM32=C:\Windows\System32"

echo 📊 Visual C++ 런타임 파일:
for %%f in (%DEPENDENCIES%) do (
    if exist "%SYSTEM32%\%%f" (
        echo ✅ %%f (System32)
    ) else (
        echo ❌ %%f (System32에 없음)
    )
)

echo 📊 키움 디렉토리의 의존성 파일:
for %%p in (%KIWOOM_PATHS%) do (
    if exist "%%p" (
        for %%f in (%DEPENDENCIES%) do (
            if exist "%%p\%%f" (
                echo ✅ %%f (%%p)
            ) else (
                echo ❌ %%f (%%p에 없음)
            )
        )
    )
)
echo.

:: 6단계: regsvr32 테스트
echo 🔍 6단계: regsvr32 테스트 중...
echo.

for %%p in (%KIWOOM_PATHS%) do (
    if exist "%%p\KHOPENAPI.OCX" (
        echo 📝 %%p\KHOPENAPI.OCX 등록 테스트:
        regsvr32 /s "%%p\KHOPENAPI.OCX"
        if !errorLevel! equ 0 (
            echo ✅ 등록 성공
        ) else (
            echo ❌ 등록 실패 (오류 코드: !errorLevel!)
        )
    )
)
echo.

:: 7단계: 권한 문제 확인
echo 🔍 7단계: 권한 문제 확인 중...
echo.

echo 📊 현재 사용자 권한:
whoami /groups | findstr "Administrators"
if %errorLevel% equ 0 (
    echo ✅ 관리자 권한 확인됨
) else (
    echo ❌ 관리자 권한 없음
)

echo 📊 파일 권한 확인:
for %%p in (%KIWOOM_PATHS%) do (
    if exist "%%p" (
        echo 📁 %%p 권한:
        icacls "%%p" | findstr "Administrators"
    )
)
echo.

:: 8단계: 문제 해결 방안 제시
echo ========================================
echo 📋 문제 해결 방안
echo ========================================
echo.

echo 🔧 일반적인 해결 방법:
echo 1. 키움 OpenAPI 완전 재설치
echo 2. Visual C++ 재배포 패키지 설치
echo 3. ActiveX 컨트롤 보안 설정 조정
echo 4. 레지스트리 수동 등록
echo 5. 시스템 파일 복구
echo.

echo 🎯 권장 해결 순서:
echo 1단계: complete_kiwoom_cleanup.bat 실행
echo 2단계: 시스템 재부팅
echo 3단계: 키움 OpenAPI 새로 설치
echo 4단계: Visual C++ 재배포 패키지 설치
echo 5단계: OCX 파일 등록
echo 6단계: post_reboot_test.bat 실행
echo.

echo 📞 추가 지원:
echo - 키움증권 고객센터: 1544-9000
echo - Microsoft Visual C++ 지원
echo - Windows 시스템 파일 검사
echo.

pause 