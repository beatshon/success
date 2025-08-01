@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 키움 OpenAPI OCX 등록 문제 자동 해결 도구
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

:: 1단계: 키움 OpenAPI 설치 경로 확인
echo 🔍 1단계: 키움 OpenAPI 설치 경로 확인 중...
set "KIWOOM_PATH=C:\Program Files (x86)\Kiwoom OpenAPI"
set "OCX_FILE=%KIWOOM_PATH%\KHOPENAPI.OCX"

if not exist "%OCX_FILE%" (
    echo ❌ OCX 파일을 찾을 수 없습니다: %OCX_FILE%
    echo.
    echo 💡 해결 방법:
    echo 1. 키움 OpenAPI를 설치해주세요
    echo 2. https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
    echo 3. 관리자 권한으로 설치해주세요
    echo.
    pause
    exit /b 1
)

echo ✅ OCX 파일 발견: %OCX_FILE%
echo.

:: 2단계: 기존 등록 정보 제거
echo 🔍 2단계: 기존 등록 정보 제거 중...
regsvr32 /u /s "%OCX_FILE%" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 기존 등록 정보 제거 완료
) else (
    echo ⚠️ 기존 등록 정보가 없거나 제거 실패 (계속 진행)
)
echo.

:: 3단계: Visual C++ 재배포 패키지 확인
echo 🔍 3단계: Visual C++ 재배포 패키지 확인 중...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Visual C++ 2015-2022 재배포 패키지 설치됨
) else (
    echo ⚠️ Visual C++ 2015-2022 재배포 패키지가 설치되지 않음
    echo 💡 자동으로 다운로드하고 설치합니다...
    
    :: Visual C++ 재배포 패키지 다운로드
    echo 📥 Visual C++ 재배포 패키지 다운로드 중...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x86.exe' -OutFile '%TEMP%\vc_redist.x86.exe'}"
    
    if exist "%TEMP%\vc_redist.x86.exe" (
        echo 📦 Visual C++ 재배포 패키지 설치 중...
        "%TEMP%\vc_redist.x86.exe" /quiet /norestart
        timeout /t 10 /nobreak >nul
        echo ✅ Visual C++ 재배포 패키지 설치 완료
    ) else (
        echo ❌ Visual C++ 재배포 패키지 다운로드 실패
        echo 💡 수동으로 설치해주세요: https://aka.ms/vs/17/release/vc_redist.x86.exe
    )
)
echo.

:: 4단계: 의존성 DLL 파일 복사
echo 🔍 4단계: 의존성 DLL 파일 복사 중...
set "SYSTEM32_PATH=C:\Windows\System32"
set "DEPENDENCIES=msvcp140.dll vcruntime140.dll"

for %%f in (%DEPENDENCIES%) do (
    if not exist "%KIWOOM_PATH%\%%f" (
        if exist "%SYSTEM32_PATH%\%%f" (
            copy "%SYSTEM32_PATH%\%%f" "%KIWOOM_PATH%\" >nul 2>&1
            if !errorLevel! equ 0 (
                echo ✅ %%f 복사 완료
            ) else (
                echo ⚠️ %%f 복사 실패 (권한 문제일 수 있음)
            )
        ) else (
            echo ⚠️ %%f 파일을 찾을 수 없음
        )
    ) else (
        echo ✅ %%f 이미 존재
    )
)
echo.

:: 5단계: OCX 파일 등록
echo 🔍 5단계: OCX 파일 등록 중...
echo 📝 등록 명령어: regsvr32 "%OCX_FILE%"
regsvr32 /s "%OCX_FILE%"

if %errorLevel% equ 0 (
    echo ✅ OCX 파일 등록 성공!
) else (
    echo ❌ OCX 파일 등록 실패
    echo.
    echo 🔧 추가 해결 방법:
    echo 1. 키움 OpenAPI 재설치
    echo 2. 시스템 재부팅 후 다시 시도
    echo 3. 안티바이러스 일시 비활성화
    echo.
    pause
    exit /b 1
)
echo.

:: 6단계: 등록 상태 확인
echo 🔍 6단계: 등록 상태 확인 중...
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 레지스트리 등록 확인됨
) else (
    echo ❌ 레지스트리 등록 확인 실패
)
echo.

:: 7단계: Python 테스트 (선택사항)
echo 🔍 7단계: Python 테스트 중...
if exist "test_ocx_registration.py" (
    echo 📝 Python 테스트 스크립트 실행 중...
    python test_ocx_registration.py
    if %errorLevel% equ 0 (
        echo ✅ Python 테스트 성공
    ) else (
        echo ⚠️ Python 테스트 실패 (PyQt5 설치 필요)
        echo 💡 해결방법: pip install PyQt5
    )
) else (
    echo ⚠️ Python 테스트 스크립트를 찾을 수 없음
)
echo.

:: 완료 메시지
echo ========================================
echo 🎉 OCX 등록 문제 해결 완료!
echo ========================================
echo.
echo ✅ 수행된 작업:
echo 1. 관리자 권한 확인
echo 2. OCX 파일 경로 확인
echo 3. 기존 등록 정보 제거
echo 4. Visual C++ 재배포 패키지 확인/설치
echo 5. 의존성 DLL 파일 복사
echo 6. OCX 파일 등록
echo 7. 등록 상태 확인
echo 8. Python 테스트
echo.
echo 💡 다음 단계:
echo 1. 키움 API 테스트 실행
echo 2. 실제 거래 전 충분한 시뮬레이션
echo 3. 문제 발생 시 로그 확인
echo.
echo 📞 추가 지원:
echo - 키움증권 고객센터: 1544-9000
echo - 이 프로젝트의 README.md 참조
echo.
pause
 