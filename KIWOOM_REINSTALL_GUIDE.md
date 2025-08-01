# 키움 OpenAPI 재설치 완전 가이드

## 🚨 현재 상황
RegSvr32에서 OCX 파일을 찾을 수 없다는 오류가 발생하고 있습니다. 이는 키움 OpenAPI가 제대로 설치되지 않았거나 파일이 손상되었음을 의미합니다.

## 🔧 완전 재설치 과정

### 1단계: 기존 설치 완전 제거

#### 1.1 제어판에서 제거
1. **Windows 키 + R** → `appwiz.cpl` 입력 → Enter
2. **프로그램 및 기능**에서 다음 항목들을 찾아 제거:
   - 키움 Open API+
   - 키움 OpenAPI
   - Kiwoom Open API+
   - Kiwoom OpenAPI

#### 1.2 명령어로 제거
```cmd
# 관리자 권한으로 명령 프롬프트 실행
wmic product where "name like 'Kiwoom%'" call uninstall /nointeractive
wmic product where "name like 'OpenAPI%'" call uninstall /nointeractive
```

#### 1.3 레지스트리 정리
```cmd
# 레지스트리 편집기 실행
regedit

# 다음 경로에서 키움 관련 항목 삭제:
HKEY_CLASSES_ROOT\KHOPENAPI
HKEY_CLASSES_ROOT\KHOPENAPI.OCX
HKEY_LOCAL_MACHINE\SOFTWARE\Kiwoom
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Kiwoom
```

#### 1.4 파일 수동 삭제
```cmd
# 관리자 권한으로 명령 프롬프트 실행
rmdir /s /q "C:\Program Files (x86)\Kiwoom OpenAPI"
rmdir /s /q "C:\Program Files\Kiwoom OpenAPI"
rmdir /s /q "%APPDATA%\Kiwoom"
rmdir /s /q "%LOCALAPPDATA%\Kiwoom"
```

### 2단계: 시스템 정리

#### 2.1 임시 파일 정리
```cmd
# 임시 파일 삭제
del /q /f %TEMP%\*.*
del /q /f %TMP%\*.*

# Windows 임시 파일 정리
cleanmgr /sagerun:1
```

#### 2.2 시스템 재부팅
```cmd
# 시스템 재부팅
shutdown /r /t 0
```

### 3단계: 새로 설치

#### 3.1 키움 OpenAPI 다운로드
1. **키움증권 공식 사이트 방문**
   - https://www1.kiwoom.com/h/customer/download/VOpenApiInfoView
   - 최신 버전 다운로드

#### 3.2 관리자 권한으로 설치
1. **다운로드한 설치 파일을 우클릭**
2. **"관리자 권한으로 실행" 선택**
3. **설치 과정에서 모든 기본 설정 유지**

#### 3.3 설치 경로 확인
```cmd
# 설치 후 파일 존재 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.dll"
```

### 4단계: OCX 파일 등록

#### 4.1 관리자 권한으로 등록
```cmd
# 관리자 권한으로 명령 프롬프트 실행
regsvr32 "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
```

#### 4.2 성공 메시지 확인
```
DllRegisterServer in C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX succeeded.
```

### 5단계: 의존성 패키지 설치

#### 5.1 Visual C++ 재배포 패키지
1. **Microsoft Visual C++ 2015-2022 재배포 패키지**
   - https://aka.ms/vs/17/release/vc_redist.x86.exe (32비트)
   - https://aka.ms/vs/17/release/vc_redist.x64.exe (64비트)

2. **관리자 권한으로 설치**

#### 5.2 .NET Framework 확인
```cmd
# .NET Framework 버전 확인
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP" /s
```

### 6단계: 테스트 및 확인

#### 6.1 파일 존재 확인
```cmd
# OCX 파일 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"

# 전체 파일 목록 확인
dir "C:\Program Files (x86)\Kiwoom OpenAPI\"
```

#### 6.2 레지스트리 등록 확인
```cmd
# 레지스트리 등록 확인
reg query "HKEY_CLASSES_ROOT\KHOPENAPI.KHOpenAPICtrl.1"
```

#### 6.3 Python 테스트
```cmd
# Python 테스트 실행
python test_ocx_registration.py
```

## 🧪 설치 확인 스크립트

### 자동 확인 배치 파일
```cmd
# check_kiwoom_files.bat 실행
check_kiwoom_files.bat
```

### Python 확인 스크립트
```cmd
# test_ocx_registration.py 실행
python test_ocx_registration.py
```

## ⚠️ 주의사항

### 설치 전 확인사항
1. **관리자 권한 필수**: 모든 작업은 관리자 권한으로 실행
2. **안티바이러스 비활성화**: 설치 중 일시적으로 비활성화
3. **방화벽 설정**: 키움 API 접근 허용
4. **네트워크 연결**: 인터넷 연결 필수

### 설치 후 확인사항
1. **키움증권 로그인**: Open API+ 사용 신청 및 승인
2. **계좌 정보**: 계좌번호, 비밀번호 확인
3. **API 키**: 앱키, 앱시크릿, 액세스 토큰 발급

## 🆘 문제 해결

### 설치 실패 시
1. **시스템 요구사항 확인**: Windows 10/11, 관리자 권한
2. **다른 경로에 설치**: C:\KiwoomOpenAPI 등
3. **가상머신 사용**: 깨끗한 환경에서 테스트

### 등록 실패 시
1. **의존성 파일 복사**: System32에서 DLL 파일 복사
2. **레지스트리 수동 등록**: regedit에서 직접 등록
3. **시스템 재부팅**: 완전한 재부팅 후 재시도

### 연결 실패 시
1. **키움증권 로그인**: 웹사이트에서 로그인 확인
2. **API 사용 신청**: Open API+ 사용 신청 상태 확인
3. **네트워크 설정**: 방화벽, 프록시 설정 확인

## 📞 추가 지원

### 키움증권 지원
- **고객센터**: 1544-9000
- **Open API+ 문의**: 키움증권 홈페이지 > 고객센터 > Open API+

### 기술 지원
- **Microsoft Visual C++**: https://support.microsoft.com/
- **Windows 시스템 오류**: 이벤트 뷰어에서 오류 확인

---

**이 가이드를 단계별로 따라하면 키움 OpenAPI를 완전히 재설치할 수 있습니다!** 🚀 