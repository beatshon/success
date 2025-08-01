# ActiveX 컨트롤 설치 문제 해결 완전 가이드

## 🚨 문제 상황
키움 Open API+ ActiveX 컨트롤 설치가 제대로 되지 않아 OCX 파일 등록 오류가 발생하고 있습니다.

## 🔍 문제 원인 분석

### 1. ActiveX 컨트롤 보안 설정 문제
- Internet Explorer 보안 설정이 ActiveX 컨트롤을 차단
- Windows 보안 정책이 OCX 파일 등록을 제한

### 2. 시스템 파일 손상
- Visual C++ 런타임 파일 손상
- 시스템 DLL 파일 누락 또는 손상

### 3. 권한 문제
- 관리자 권한 부족
- 파일 및 레지스트리 접근 권한 제한

### 4. 의존성 문제
- Visual C++ 재배포 패키지 누락
- COM+ 서비스 문제

## 🔧 해결 방법

### 1단계: 문제 진단

#### 1.1 자동 진단 실행
```cmd
# 관리자 권한으로 실행
diagnose_activex_issues.bat
```

#### 1.2 수동 진단
```cmd
# OCX 파일 존재 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 레지스트리 등록 확인
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1"

# Visual C++ 런타임 확인
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"
```

### 2단계: ActiveX 컨트롤 보안 설정 조정

#### 2.1 레지스트리 설정 조정
```cmd
# 관리자 권한으로 명령 프롬프트 실행
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1001 /t REG_DWORD /d 0 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1004 /t REG_DWORD /d 0 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\0" /v 1201 /t REG_DWORD /d 0 /f

reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1001 /t REG_DWORD /d 0 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1004 /t REG_DWORD /d 0 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" /v 1201 /t REG_DWORD /d 0 /f
```

#### 2.2 Internet Explorer 보안 설정
1. **Internet Explorer 실행**
2. **도구** → **인터넷 옵션**
3. **보안** 탭 → **신뢰할 수 있는 사이트**
4. **사이트** 버튼 클릭
5. **https://www1.kiwoom.com** 추가
6. **ActiveX 컨트롤 및 플러그인** → **ActiveX 컨트롤 및 플러그인 실행** → **사용**

### 3단계: 시스템 파일 복구

#### 3.1 시스템 파일 검사
```cmd
# 시스템 파일 무결성 검사
sfc /scannow

# DISM 도구로 시스템 복구
DISM /Online /Cleanup-Image /RestoreHealth
```

#### 3.2 Visual C++ 재배포 패키지 재설치
1. **기존 Visual C++ 제거**
   ```cmd
   wmic product where "name like 'Microsoft Visual C++%'" call uninstall /nointeractive
   ```

2. **새로 설치**
   - https://aka.ms/vs/17/release/vc_redist.x86.exe (32비트)
   - https://aka.ms/vs/17/release/vc_redist.x64.exe (64비트)
   - 관리자 권한으로 설치

### 4단계: 의존성 파일 복사

#### 4.1 필요한 DLL 파일 복사
```cmd
# System32에서 키움 디렉토리로 복사
copy "C:\Windows\System32\msvcp140.dll" "C:\Program Files (x86)\Kiwoom OpenAPI\"
copy "C:\Windows\System32\vcruntime140.dll" "C:\Program Files (x86)\Kiwoom OpenAPI\"
copy "C:\Windows\System32\msvcr140.dll" "C:\Program Files (x86)\Kiwoom OpenAPI\"
```

#### 4.2 파일 권한 설정
```cmd
# 관리자 권한 설정
icacls "C:\Program Files (x86)\Kiwoom OpenAPI" /grant "Administrators:(OI)(CI)F" /T
icacls "C:\Program Files (x86)\Kiwoom OpenAPI" /grant "Users:(OI)(CI)RX" /T
```

### 5단계: 레지스트리 정리 및 재등록

#### 5.1 기존 등록 제거
```cmd
# OCX 등록 제거
regsvr32 /u /s "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 레지스트리 키 삭제
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI" /f
reg delete "HKEY_CLASSES_ROOT\KHOPENAPI.OCX" /f
```

#### 5.2 새로 등록
```cmd
# OCX 파일 등록
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
```

### 6단계: COM+ 서비스 재시작

#### 6.1 서비스 재시작
```cmd
# COM+ 서비스 중지
net stop "COM+ System Application"

# COM+ 서비스 시작
net start "COM+ System Application"
```

#### 6.2 COM+ 구성 확인
1. **Windows 키 + R** → `dcomcnfg` 입력
2. **구성 요소 서비스** → **컴퓨터** → **내 컴퓨터**
3. **DCOM 구성** → **KHOPENAPI.KHOpenAPICtrl.1** 확인

### 7단계: 자동 해결 도구 사용

#### 7.1 완전 자동 해결
```cmd
# 관리자 권한으로 실행
fix_activex_controls.bat
```

#### 7.2 단계별 해결
```cmd
# 1단계: 완전 제거
complete_kiwoom_cleanup.bat

# 2단계: 시스템 재부팅
shutdown /r /t 0

# 3단계: 키움 OpenAPI 새로 설치
# 4단계: ActiveX 컨트롤 해결
fix_activex_controls.bat

# 5단계: 테스트
post_reboot_test.bat
```

## 🧪 테스트 및 확인

### 1. 기본 확인
```cmd
# 파일 존재 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 레지스트리 등록 확인
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1"
```

### 2. Python 테스트
```cmd
# OCX 등록 테스트
python test_ocx_registration.py

# 키움 API 연결 테스트
python test_kiwoom_connection.py
```

### 3. 자동 테스트
```cmd
# 재부팅 후 테스트
post_reboot_test.bat
```

## ⚠️ 주의사항

### 보안 설정 조정 시
1. **임시 조정**: 문제 해결 후 보안 설정 복원 권장
2. **신뢰할 수 있는 사이트만**: 키움증권 사이트만 허용
3. **방화벽 설정**: 키움 API 접근 허용

### 시스템 파일 복구 시
1. **백업 권장**: 중요한 데이터 백업
2. **시간 소요**: 시스템 파일 검사는 시간이 걸림
3. **인터넷 연결**: DISM 도구 사용 시 인터넷 필요

### 권한 설정 시
1. **관리자 권한 필수**: 모든 작업은 관리자 권한으로
2. **보안 균형**: 필요한 최소 권한만 부여
3. **정기 확인**: 권한 설정 상태 정기 확인

## 🆘 추가 지원

### 문제가 지속되는 경우
1. **키움증권 고객센터**: 1544-9000
2. **Microsoft 지원**: Visual C++ 런타임 문제
3. **Windows 시스템 복구**: 시스템 복원 또는 재설치

### 대안 방법
1. **가상머신 사용**: 깨끗한 환경에서 테스트
2. **다른 PC에서 테스트**: 동일한 환경에서 재현 여부 확인
3. **키움 OpenAPI+ 모바일**: 모바일 앱 사용 고려

---

**이 가이드를 단계별로 따라하면 ActiveX 컨트롤 설치 문제를 해결할 수 있습니다!** 🚀 