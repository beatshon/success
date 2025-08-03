# Windows 작업 스케줄러 설정 가이드

## 📊 일일 요약 리포트 자동 실행 설정

### 1. 작업 스케줄러 열기
1. **Windows 키 + R** → `taskschd.msc` 입력
2. 또는 **제어판** → **관리 도구** → **작업 스케줄러**

### 2. 기본 작업 만들기

#### 2.1 작업 이름 설정
- **이름**: `일일 요약 리포트`
- **설명**: `매일 오후 11:50에 일일 매매 요약 리포트 생성`

#### 2.2 트리거 설정
- **트리거**: `매일`
- **시작**: `오후 11:50`
- **반복**: `매일`

#### 2.3 동작 설정
- **동작**: `프로그램 시작`
- **프로그램/스크립트**: `C:\Windows\System32\cmd.exe`
- **인수 추가**: `/c "C:\path\to\kiwoom_trading\daily_summary.bat"`

### 3. 배치 파일 실행 방법

#### 3.1 기본 배치 파일
```batch
@echo off
cd /d "C:\path\to\kiwoom_trading"
call venv\Scripts\activate.bat
python cross_platform_trader.py --daily-summary
deactivate
```

#### 3.2 PowerShell 스크립트
```powershell
Set-Location "C:\path\to\kiwoom_trading"
.\venv\Scripts\Activate.ps1
python cross_platform_trader.py --daily-summary
deactivate
```

### 4. 명령행 옵션

#### 4.1 일일 요약만 실행
```bash
python cross_platform_trader.py --daily-summary
```

#### 4.2 비상정지 테스트
```bash
python cross_platform_trader.py --emergency-stop
```

#### 4.3 테스트 모드
```bash
python cross_platform_trader.py --test
```

### 5. 로그 설정

#### 5.1 배치 파일 로그
```batch
@echo off
cd /d "C:\path\to\kiwoom_trading"
call venv\Scripts\activate.bat
python cross_platform_trader.py --daily-summary >> daily_summary.log 2>&1
deactivate
```

#### 5.2 PowerShell 로그
```powershell
.\daily_summary.ps1 -Log -LogFile "daily_summary.log"
```

### 6. 오류 처리

#### 6.1 배치 파일 오류 처리
```batch
@echo off
cd /d "C:\path\to\kiwoom_trading"
call venv\Scripts\activate.bat
python cross_platform_trader.py --daily-summary
if %errorlevel% neq 0 (
    echo 오류 발생: %errorlevel% >> error.log
    exit /b %errorlevel%
)
deactivate
```

#### 6.2 PowerShell 오류 처리
```powershell
try {
    .\daily_summary.ps1 -Log
} catch {
    Add-Content -Path "error.log" -Value $_.Exception.Message
    exit 1
}
```

### 7. 테스트 방법

#### 7.1 수동 테스트
```bash
# 현재 시간에 즉시 실행
python cross_platform_trader.py --daily-summary
```

#### 7.2 스케줄러 테스트
1. 작업 스케줄러에서 작업 선택
2. **실행** 버튼 클릭
3. 로그 확인

### 8. 모니터링

#### 8.1 로그 파일 확인
- `daily_summary.log`: 실행 로그
- `error.log`: 오류 로그
- `logs/YYYY-MM-DD/`: 매매 로그

#### 8.2 텔레그램 알림
- 매일 오후 11:50에 자동으로 텔레그램 전송
- 오류 발생 시 즉시 알림

### 9. 문제 해결

#### 9.1 가상환경 문제
```batch
:: 가상환경 경로 확인
dir venv\Scripts\activate.bat
```

#### 9.2 Python 경로 문제
```batch
:: Python 경로 확인
where python
```

#### 9.3 권한 문제
- 작업 스케줄러에서 **최고 수준의 권한으로 실행** 체크
- **사용자 계정**으로 실행

### 10. 고급 설정

#### 10.1 조건부 실행
```batch
@echo off
cd /d "C:\path\to\kiwoom_trading"

:: 주말 제외 (월-금만 실행)
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set day=%%c
if %day%==토 goto :end
if %day%==일 goto :end

call venv\Scripts\activate.bat
python cross_platform_trader.py --daily-summary
deactivate

:end
```

#### 10.2 네트워크 연결 확인
```batch
@echo off
:: 네트워크 연결 확인
ping -n 1 8.8.8.8 >nul
if %errorlevel% neq 0 (
    echo 네트워크 연결 실패 >> error.log
    exit /b 1
)

cd /d "C:\path\to\kiwoom_trading"
call venv\Scripts\activate.bat
python cross_platform_trader.py --daily-summary
deactivate
```

## 🎯 완료!

이제 매일 오후 11:50에 자동으로 일일 요약 리포트가 생성되어 텔레그램으로 전송됩니다! 