# 수동 동기화 가이드 (Git 없이)

## 📥 GitHub ZIP 파일 다운로드 방법

### 1단계: GitHub에서 다운로드

1. **GitHub 저장소 접속**
   - https://github.com/beatshon/success
   - 녹색 "Code" 버튼 클릭
   - "Download ZIP" 선택

2. **ZIP 파일 다운로드**
   - `success-main.zip` 파일이 다운로드됨
   - Windows 바탕화면에 저장

### 2단계: Windows에서 압축 해제

1. **ZIP 파일 압축 해제**
   ```cmd
   # 바탕화면에서
   cd C:\Users\Administrator\Desktop
   
   # 압축 해제
   tar -xf success-main.zip
   # 또는 Windows 탐색기에서 우클릭 → "압축 해제"
   ```

2. **폴더명 변경**
   ```cmd
   # 폴더명을 kiwoom_trading으로 변경
   ren success-main kiwoom_trading
   ```

### 3단계: 기존 파일 백업 (선택사항)

```cmd
# 기존 폴더가 있다면 백업
ren kiwoom_trading kiwoom_trading_backup
ren success-main kiwoom_trading
```

### 4단계: 설정 파일 보존

```cmd
# 중요한 설정 파일 복사
copy kiwoom_trading_backup\config\windows_server.conf kiwoom_trading\config\
```

## 🔄 동기화 주기

### 맥에서 작업 후:
1. **자동 커밋**: `./auto_commit_and_push.sh`
2. **GitHub에 업로드 완료**

### Windows에서 업데이트:
1. **GitHub에서 새 ZIP 다운로드**
2. **기존 폴더 백업**
3. **새 파일로 교체**
4. **Windows 서버 재시작**

## 📋 파일 구조

```
kiwoom_trading/
├── windows_api_server.py      # Windows API 서버
├── setup_windows.bat          # 초기 설정
├── start_windows_server.bat   # 서버 시작
├── manual_sync.bat            # 수동 동기화 가이드
├── config/
│   └── windows_server.conf    # 설정 파일 (보존 필요)
└── logs/                      # 로그 파일
```

## ⚠️ 주의사항

1. **설정 파일 보존**: `config/windows_server.conf`는 백업
2. **로그 파일**: `logs/` 폴더는 보존
3. **가상환경**: `venv/` 폴더는 재생성 필요

## 🚀 빠른 시작

```cmd
# 1. 프로젝트 폴더로 이동
cd C:\Users\Administrator\Desktop\kiwoom_trading

# 2. 초기 설정
setup_windows.bat

# 3. 서버 시작
start_windows_server.bat

# 4. 수동 동기화 가이드
manual_sync.bat
```

## 📞 문제 해결

### ZIP 파일 다운로드 실패
- 네트워크 연결 확인
- 브라우저 캐시 삭제
- 다른 브라우저 사용

### 압축 해제 실패
- 디스크 공간 확인
- 바이러스 백신 비활성화
- 관리자 권한으로 실행

### 파일 교체 실패
- 기존 폴더 완전 삭제
- 새로 압축 해제
- 권한 확인

---

**✅ 이제 Git 없이도 GitHub 동기화가 가능합니다!** 