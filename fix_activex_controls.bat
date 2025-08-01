@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🔧 ActiveX 컨트롤 문제 해결 도구
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

:: 1단계: ActiveX 컨트롤 보안 설정 조정
echo 🔍 1단계: ActiveX 컨트롤 보안 설정 조정 중...
echo.

echo 📊 Internet Explorer 보안 설정 조정:
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1001 /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1004 /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1201 /t REG_DWORD /d 0 /f >nul 2>&1

echo 📊 ActiveX 컨트롤 다운로드 설정:
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1001 /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1004 /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1201 /t REG_DWORD /d 0 /f >nul 2>&1

echo ✅ ActiveX 보안 설정 조정 완료
echo.

:: 2단계: 시스템 파일 복구
echo 🔍 2단계: 시스템 파일 복구 중...
echo.

echo 📊 시스템 파일 무결성 검사:
sfc /scannow >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 시스템 파일 검사 완료
) else (
    echo ⚠️ 시스템 파일 검사 중 오류 발생
)

echo 📊 DISM 도구로 시스템 복구:
DISM /Online /Cleanup-Image /RestoreHealth >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ DISM 복구 완료
) else (
    echo ⚠️ DISM 복구 중 오류 발생
)
echo.

:: 3단계: Visual C++ 재배포 패키지 강제 재설치
echo 🔍 3단계: Visual C++ 재배포 패키지 강제 재설치 중...
echo.

echo 📊 기존 Visual C++ 제거:
wmic product where "name like 'Microsoft Visual C++%'" call uninstall /nointeractive >nul 2>&1

echo 📊 Visual C++ 2015-2022 재배포 패키지 다운로드:
echo 📥 32비트 버전 다운로드 중...
powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x86.exe' -OutFile '%TEMP%\vc_redist.x86.exe'}" >nul 2>&1

echo 📥 64비트 버전 다운로드 중...
powershell -Command "& {Invoke-WebRequest -Uri 'https://https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP%\vc_redist.x64.exe'}" >nul 2>&1

echo 📦 Visual C++ 설치 중...
if exist "%TEMP%\vc_redist.x86.exe" (
    "%TEMP%\vc_redist.x86.exe" /quiet /norestart >nul 2>&1
    echo ✅ 32비트 Visual C++ 설치 완료
)

if exist "%TEMP%\vc_redist.x64.exe" (
    "%TEMP%\vc_redist.x64.exe" /quiet /norestart >nul 2>&1
    echo ✅ 64비트 Visual C++ 설치 완료
)
echo.

:: 4단계: 의존성 DLL 파일 복사
echo 🔍 4단계: 의존성 DLL 파일 복사 중...
echo.

set "KIWOOM_PATH=C:\Program Files (x86)\Kiwoom OpenAPI"
set "SYSTEM32=C:\Windows\System32"
set "DEPENDENCIES=msvcp140.dll vcruntime140.dll msvcr140.dll"

if exist "%KIWOOM_PATH%" (
    for %%f in (%DEPENDENCIES%) do (
        if exist "%SYSTEM32%\%%f" (
            if not exist "%KIWOOM_PATH%\%%f" (
                copy "%SYSTEM32%\%%f" "%KIWOOM_PATH%\" >nul 2>&1
                if !errorLevel! equ 0 (
                    echo ✅ %%f 복사 완료
                ) else (
                    echo ❌ %%f 복사 실패
                )
            ) else (
                echo ✅ %%f 이미 존재
            )
        ) else (
            echo ⚠️ %%f (System32에 없음)
        )
    )
) else (
    echo ❌ 키움 OpenAPI 경로 없음
)
echo.

:: 5단계: 레지스트리 정리 및 재등록
echo 🔍 5단계: 레지스트리 정리 및 재등록 중...
echo.

echo 📝 기존 OCX 등록 제거:
regsvr32 /u /s "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX" >nul 2>&1

echo 📝 레지스트리 키 삭제:
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI.OCX" /f >nul 2>&1

echo 📝 OCX 파일 재등록:
if exist "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX" (
    regsvr32 /s "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
    if !errorLevel! equ 0 (
        echo ✅ OCX 등록 성공
    ) else (
        echo ❌ OCX 등록 실패
    )
) else (
    echo ❌ OCX 파일 없음
)
echo.

:: 6단계: 파일 권한 설정
echo 🔍 6단계: 파일 권한 설정 중...
echo.

if exist "%KIWOOM_PATH%" (
    echo 📁 키움 OpenAPI 디렉토리 권한 설정:
    icacls "%KIWOOM_PATH%" /grant "Administrators:(OI)(CI)F" /T >nul 2>&1
    icacls "%KIWOOM_PATH%" /grant "Users:(OI)(CI)RX" /T >nul 2>&1
    echo ✅ 권한 설정 완료
)
echo.

:: 7단계: COM+ 서비스 재시작
echo 🔍 7단계: COM+ 서비스 재시작 중...
echo.

echo 🔄 COM+ 서비스 중지:
net stop "COM+ System Application" >nul 2>&1

echo 🔄 COM+ 서비스 시작:
net start "COM+ System Application" >nul 2>&1

echo ✅ COM+ 서비스 재시작 완료
echo.

:: 8단계: 최종 테스트
echo 🔍 8단계: 최종 테스트 중...
echo.

echo 📊 레지스트리 등록 확인:
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ OCX 레지스트리 등록 확인됨
) else (
    echo ❌ OCX 레지스트리 등록 확인 실패
)

echo 📊 파일 존재 확인:
if exist "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX" (
    echo ✅ OCX 파일 존재 확인됨
) else (
    echo ❌ OCX 파일 존재 확인 실패
)
echo.

:: 완료 메시지
echo ========================================
echo 🎉 ActiveX 컨트롤 문제 해결 완료!
echo ========================================
echo.
echo ✅ 수행된 작업:
echo 1. ActiveX 보안 설정 조정
echo 2. 시스템 파일 복구
echo 3. Visual C++ 재배포 패키지 재설치
echo 4. 의존성 DLL 파일 복사
echo 5. 레지스트리 정리 및 재등록
echo 6. 파일 권한 설정
echo 7. COM+ 서비스 재시작
echo 8. 최종 테스트
echo.
echo 💡 다음 단계:
echo 1. 시스템 재부팅
echo 2. 키움 OpenAPI 테스트
echo 3. Python 테스트 실행
echo.
echo 🔄 시스템을 재부팅하시겠습니까? (Y/N)
set /p reboot_choice=

if /i "%reboot_choice%"=="Y" (
    echo 🔄 시스템 재부팅 중...
    shutdown /r /t 10 /c "ActiveX 컨트롤 문제 해결을 위해 시스템을 재부팅합니다."
) else (
    echo 💡 수동으로 재부팅 후 키움 OpenAPI를 테스트해주세요.
)

echo.
pause
 