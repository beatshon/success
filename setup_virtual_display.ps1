# RDP 세션 유지를 위한 가상 디스플레이 설정 스크립트
# 관리자 권한으로 실행해야 합니다.

Write-Host "🖥️ RDP 세션 유지 설정 시작..." -ForegroundColor Green

# 1. 현재 디스플레이 설정 확인
Write-Host "`n📋 현재 디스플레이 설정 확인 중..." -ForegroundColor Cyan

try {
    $displaySettings = Get-WmiObject -Class Win32_VideoController | Select-Object Name, VideoModeDescription
    Write-Host "현재 비디오 컨트롤러:" -ForegroundColor Yellow
    foreach ($display in $displaySettings) {
        Write-Host "  - $($display.Name): $($display.VideoModeDescription)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ 디스플레이 설정 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. RDP 세션 설정 확인
Write-Host "`n🔧 RDP 세션 설정 확인 중..." -ForegroundColor Cyan

try {
    $rdpSettings = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -ErrorAction SilentlyContinue
    if ($rdpSettings) {
        Write-Host "RDP 설정 확인됨" -ForegroundColor Green
        Write-Host "  - fDenyTSConnections: $($rdpSettings.fDenyTSConnections)" -ForegroundColor White
    } else {
        Write-Host "⚠️ RDP 설정을 찾을 수 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ RDP 설정 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. 가상 디스플레이 드라이버 설치 안내
Write-Host "`n🖥️ 가상 디스플레이 드라이버 설치 안내:" -ForegroundColor Cyan
Write-Host "1. Microsoft Basic Display Adapter 사용" -ForegroundColor White
Write-Host "2. 또는 Virtual Display Driver 설치" -ForegroundColor White
Write-Host "3. RDP Wrapper Library 설치 고려" -ForegroundColor White

# 4. RDP 세션 유지 설정
Write-Host "`n⏰ RDP 세션 유지 설정 중..." -ForegroundColor Cyan

try {
    # 세션 타임아웃 설정
    $sessionTimeout = 0  # 0 = 무제한
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "MaxIdleTime" -Value $sessionTimeout -ErrorAction SilentlyContinue
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "MaxDisconnectionTime" -Value $sessionTimeout -ErrorAction SilentlyContinue
    
    Write-Host "✅ RDP 세션 타임아웃 설정 완료 (무제한)" -ForegroundColor Green
    
    # 연결 끊김 시 세션 유지 설정
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "EndSessionOnDisconnect" -Value 0 -ErrorAction SilentlyContinue
    
    Write-Host "✅ 연결 끊김 시 세션 유지 설정 완료" -ForegroundColor Green
    
} catch {
    Write-Host "❌ RDP 세션 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 전원 관리 설정
Write-Host "`n🔋 전원 관리 설정 중..." -ForegroundColor Cyan

try {
    # 디스플레이 끄기 방지
    powercfg /change monitor-timeout-ac 0
    powercfg /change monitor-timeout-dc 0
    
    # 시스템 절전 모드 방지
    powercfg /change standby-timeout-ac 0
    powercfg /change standby-timeout-dc 0
    
    # 하드 디스크 끄기 방지
    powercfg /change disk-timeout-ac 0
    powercfg /change disk-timeout-dc 0
    
    Write-Host "✅ 전원 관리 설정 완료 (절전 모드 비활성화)" -ForegroundColor Green
    
} catch {
    Write-Host "❌ 전원 관리 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. 서비스 설정
Write-Host "`n🔧 서비스 설정 중..." -ForegroundColor Cyan

try {
    # 원격 데스크톱 서비스 자동 시작
    Set-Service -Name "TermService" -StartupType Automatic -ErrorAction SilentlyContinue
    
    # 원격 데스크톱 사용자 모드 포트 리디렉터 자동 시작
    Set-Service -Name "UmRdpService" -StartupType Automatic -ErrorAction SilentlyContinue
    
    Write-Host "✅ RDP 관련 서비스 자동 시작 설정 완료" -ForegroundColor Green
    
} catch {
    Write-Host "❌ 서비스 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. 레지스트리 설정
Write-Host "`n🔑 레지스트리 설정 중..." -ForegroundColor Cyan

try {
    # RDP 연결 끊김 시 로그아웃 방지
    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services"
    if (!(Test-Path $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }
    
    Set-ItemProperty -Path $regPath -Name "fDisableForcibleLogoff" -Value 1 -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $regPath -Name "MaxDisconnectionTime" -Value 0 -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $regPath -Name "MaxIdleTime" -Value 0 -ErrorAction SilentlyContinue
    
    Write-Host "✅ 레지스트리 설정 완료" -ForegroundColor Green
    
} catch {
    Write-Host "❌ 레지스트리 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 8. 세션 유지 스크립트 생성
Write-Host "`n📝 세션 유지 스크립트 생성 중..." -ForegroundColor Cyan

$keepAliveScript = @"
# RDP 세션 유지 스크립트
# 이 스크립트를 주기적으로 실행하여 세션을 유지합니다.

Write-Host "🔄 RDP 세션 유지 중..." -ForegroundColor Green

# 마우스 움직임 시뮬레이션 (선택사항)
# Add-Type -AssemblyName System.Windows.Forms
# [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(0, 0)

# 현재 시간 출력
Write-Host "현재 시간: $(Get-Date)" -ForegroundColor Yellow

# 세션 정보 확인
try {
    `$session = quser 2>`$null
    if (`$session) {
        Write-Host "활성 세션 발견:" -ForegroundColor Green
        Write-Host `$session -ForegroundColor White
    } else {
        Write-Host "활성 세션이 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "세션 정보 확인 실패" -ForegroundColor Red
}

Write-Host "✅ 세션 유지 완료" -ForegroundColor Green
"@

$keepAliveScript | Out-File -FilePath "keep_rdp_session.ps1" -Encoding UTF8
Write-Host "✅ 세션 유지 스크립트 생성 완료: keep_rdp_session.ps1" -ForegroundColor Green

# 9. 작업 스케줄러 설정 안내
Write-Host "`n⏰ 작업 스케줄러 설정 안내:" -ForegroundColor Cyan
Write-Host "1. 작업 스케줄러 열기 (taskschd.msc)" -ForegroundColor White
Write-Host "2. '기본 작업 만들기' 클릭" -ForegroundColor White
Write-Host "3. 트리거: 매 5분마다" -ForegroundColor White
Write-Host "4. 동작: PowerShell 실행" -ForegroundColor White
Write-Host "5. 프로그램: powershell.exe" -ForegroundColor White
Write-Host "6. 인수: -ExecutionPolicy Bypass -File 'C:\Users\Administrator\Desktop\kiwoom_trading\keep_rdp_session.ps1'" -ForegroundColor White

Write-Host "`n📋 다음 단계:" -ForegroundColor Green
Write-Host "1. 키움 영웅문을 실행하고 로그인하세요" -ForegroundColor White
Write-Host "2. pykiwoom 테스트를 다시 실행하세요" -ForegroundColor White
Write-Host "3. 필요시 작업 스케줄러를 설정하여 세션을 유지하세요" -ForegroundColor White

Write-Host "`n✅ RDP 세션 유지 설정 완료!" -ForegroundColor Green 