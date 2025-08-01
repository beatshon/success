# 윈도우 서버 앱키 설정 문제 해결 가이드

## 🚨 문제 상황
윈도우 서버에서 `setup_kiwoom_appkey.bat` 파일을 찾을 수 없는 오류가 발생했습니다.

## 🔧 해결 방법

### 방법 1: 올바른 디렉토리로 이동

```cmd
# 1. 프로젝트 디렉토리로 이동
cd C:\path\to\kiwoom_trading

# 2. 파일 존재 확인
dir setup_kiwoom_appkey.bat

# 3. 파일이 있으면 실행
setup_kiwoom_appkey.bat
```

### 방법 2: 자동 동기화 대기

파일이 아직 동기화되지 않았을 수 있습니다:

```cmd
# 1. 현재 디렉토리 확인
cd
dir

# 2. 30초 대기 후 다시 확인
timeout /t 30
dir setup_kiwoom_appkey.bat

# 3. 파일이 나타나면 실행
setup_kiwoom_appkey.bat
```

### 방법 3: 수동으로 파일 확인 및 실행

```cmd
# 1. 모든 배치 파일 확인
dir *.bat

# 2. 키움 관련 파일 확인
dir *kiwoom*.bat
dir *appkey*.bat

# 3. Python 스크립트 직접 실행
python test_kiwoom_with_appkey.py
```

### 방법 4: 파일이 없는 경우 수동 설정

```cmd
# 1. 환경 변수 파일 생성
copy env_example.txt .env

# 2. .env 파일 편집
notepad .env

# 3. 앱키 정보 입력 후 저장

# 4. 테스트 실행
python test_kiwoom_with_appkey.py
```

## 📋 단계별 해결 과정

### 1단계: 현재 상황 확인
```cmd
# 현재 디렉토리 확인
cd
echo 현재 디렉토리: %CD%

# 파일 목록 확인
dir
```

### 2단계: 프로젝트 디렉토리 찾기
```cmd
# 키움 프로젝트 디렉토리 찾기
dir /s /b *kiwoom*
```

### 3단계: 올바른 디렉토리로 이동
```cmd
# 찾은 디렉토리로 이동
cd C:\found\kiwoom\directory

# 파일 확인
dir setup_kiwoom_appkey.bat
```

### 4단계: 앱키 설정 실행
```cmd
# 배치 파일 실행
setup_kiwoom_appkey.bat

# 또는 Python 스크립트 직접 실행
python test_kiwoom_with_appkey.py
```

## 🛠️ 수동 설정 방법

### 1. .env 파일 생성
```cmd
# 환경 변수 예제 파일 복사
copy env_example.txt .env
```

### 2. .env 파일 편집
메모장으로 `.env` 파일을 열어서 다음 정보를 입력:

```env
# 키움 API 앱키 (실제 발급받은 값으로 변경)
KIWOOM_APP_KEY=your_actual_app_key_here
KIWOOM_APP_SECRET=your_actual_app_secret_here
KIWOOM_ACCESS_TOKEN=your_actual_access_token_here

# 계정 정보
KIWOOM_USER_ID=your_user_id
KIWOOM_PASSWORD=your_password
KIWOOM_ACCOUNT=your_account_number
```

### 3. 테스트 실행
```cmd
# 앱키 설정 테스트
python test_kiwoom_with_appkey.py
```

## 🔍 문제 진단

### 파일이 없는 경우:
1. **자동 동기화 대기**: 30초 후 다시 확인
2. **수동 동기화**: `git pull origin main` 실행
3. **파일 수동 생성**: 위의 수동 설정 방법 사용

### 권한 오류인 경우:
```cmd
# 관리자 권한으로 실행
# 또는 파일 속성에서 권한 확인
```

### Python 오류인 경우:
```cmd
# Python 설치 확인
python --version

# 필요한 패키지 설치
pip install python-dotenv loguru PyQt5
```

## ✅ 성공 확인

설정이 완료되면 다음 메시지가 나타납니다:

```
🔑 앱키 설정 테스트 중...
✅ 앱키 설정 완료
📋 앱키: xxxxxxxxxx...
📋 앱 시크릿: xxxxxxxxxx...
✅ API 연결 테스트 성공
✅ 로그인 성공
✅ 계좌 정보 조회 성공
🎉 모든 앱키 테스트가 성공적으로 완료되었습니다!
```

## 🆘 추가 지원

문제가 지속되면:

1. **로그 확인**: `logs/` 디렉토리의 로그 파일 확인
2. **파일 경로 확인**: 절대 경로로 파일 실행
3. **권한 확인**: 관리자 권한으로 실행
4. **네트워크 확인**: 인터넷 연결 상태 확인

---

**이 가이드를 따라 단계별로 진행하면 앱키 설정 문제를 해결할 수 있습니다!** 🚀 