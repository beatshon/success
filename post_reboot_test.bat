@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🔄 재부팅 후 키움 OpenAPI 테스트
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

:: 1단계: OCX 파일 존재 확인
echo 🔍 1단계: OCX 파일 존재 확인 중...
set "OCX_FILE=C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

if exist "%OCX_FILE%" (
    echo ✅ OCX 파일 존재: %OCX_FILE%
    for %%A in ("%OCX_FILE%") do (
        echo 📊 파일 크기: %%~zA bytes
        echo 📅 수정 날짜: %%~tA
    )
) else (
    echo ❌ OCX 파일 없음: %OCX_FILE%
    echo 💡 키움 OpenAPI를 재설치해주세요
    pause
    exit /b 1
)
echo.

:: 2단계: 레지스트리 등록 확인
echo 🔍 2단계: 레지스트리 등록 확인 중...
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 레지스트리에 등록됨
) else (
    echo ❌ 레지스트리에 등록되지 않음
    echo 💡 OCX 파일을 다시 등록합니다...
    
    regsvr32 /s "%OCX_FILE%"
    if !errorLevel! equ 0 (
        echo ✅ OCX 파일 등록 성공
    ) else (
        echo ❌ OCX 파일 등록 실패
        pause
        exit /b 1
    )
)
echo.

:: 3단계: 의존성 파일 확인
echo 🔍 3단계: 의존성 파일 확인 중...
set "KIWOOM_PATH=C:\Program Files (x86)\Kiwoom OpenAPI"
set "DEPENDENCIES=msvcp140.dll vcruntime140.dll KHOPENAPI.dll"

for %%f in (%DEPENDENCIES%) do (
    if exist "%KIWOOM_PATH%\%%f" (
        echo ✅ %%f
    ) else (
        echo ❌ %%f (누락)
    )
)
echo.

:: 4단계: Visual C++ 재배포 패키지 확인
echo 🔍 4단계: Visual C++ 재배포 패키지 확인 중...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Visual C++ 2015-2022 재배포 패키지 설치됨
) else (
    echo ❌ Visual C++ 2015-2022 재배포 패키지 없음
    echo 💡 https://aka.ms/vs/17/release/vc_redist.x86.exe 에서 다운로드
)
echo.

:: 5단계: Python 테스트
echo 🔍 5단계: Python 테스트 중...
if exist "test_ocx_registration.py" (
    echo 📝 Python 테스트 스크립트 실행 중...
    python test_ocx_registration.py
    if %errorLevel% equ 0 (
        echo ✅ Python 테스트 성공
    ) else (
        echo ❌ Python 테스트 실패
        echo 💡 PyQt5 설치 필요: pip install PyQt5
    )
) else (
    echo ⚠️ Python 테스트 스크립트를 찾을 수 없음
)
echo.

:: 6단계: 키움 API 연결 테스트
echo 🔍 6단계: 키움 API 연결 테스트 중...
if exist "test_kiwoom_connection.py" (
    echo 📝 키움 API 연결 테스트 중...
    python test_kiwoom_connection.py
    if %errorLevel% equ 0 (
        echo ✅ 키움 API 연결 성공
    ) else (
        echo ❌ 키움 API 연결 실패
        echo 💡 키움증권 로그인 및 API 사용 신청 확인
    )
) else (
    echo ⚠️ 키움 API 연결 테스트 스크립트를 찾을 수 없음
)
echo.

:: 결과 요약
echo ========================================
echo 📊 재부팅 후 테스트 결과 요약
echo ========================================
echo.

echo ✅ 성공한 항목:
if exist "%OCX_FILE%" echo - OCX 파일 존재
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1 && echo - 레지스트리 등록
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86" >nul 2>&1 && echo - Visual C++ 재배포 패키지

echo.
echo 💡 다음 단계:
echo 1. 키움증권 로그인 및 API 사용 신청
echo 2. 실제 거래 전 시뮬레이션 테스트
echo 3. 자동매매 시스템 실행

echo.
echo 🎉 재부팅 후 테스트가 완료되었습니다!
echo.

pause 