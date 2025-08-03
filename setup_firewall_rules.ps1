# 키움 API 방화벽 규칙 설정 스크립트
# 관리자 권한으로 실행해야 합니다.

Write-Host "🛡️ 키움 API 방화벽 규칙 설정 시작..." -ForegroundColor Green

# 1. 기존 키움 관련 방화벽 규칙 확인
Write-Host "`n📋 기존 방화벽 규칙 확인 중..." -ForegroundColor Cyan

$existingRules = Get-NetFirewallRule -DisplayName "*Kiwoom*" -ErrorAction SilentlyContinue
if ($existingRules) {
    Write-Host "✅ 기존 키움 관련 방화벽 규칙 발견:" -ForegroundColor Green
    foreach ($rule in $existingRules) {
        Write-Host "  - $($rule.DisplayName) (상태: $($rule.Enabled))" -ForegroundColor White
    }
} else {
    Write-Host "⚠️ 기존 키움 관련 방화벽 규칙이 없습니다." -ForegroundColor Yellow
}

# 2. 키움 프로그램 경로 확인
Write-Host "`n🔍 키움 프로그램 경로 확인 중..." -ForegroundColor Cyan

$kiwoomPaths = @(
    "C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.OCX",
    "C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.exe",
    "C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.dll"
)

$foundPaths = @()
foreach ($path in $kiwoomPaths) {
    if (Test-Path $path) {
        $foundPaths += $path
        Write-Host "✅ 발견: $path" -ForegroundColor Green
    } else {
        Write-Host "❌ 없음: $path" -ForegroundColor Red
    }
}

# 3. Python 경로 확인
Write-Host "`n🐍 Python 경로 확인 중..." -ForegroundColor Cyan

$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    Write-Host "✅ Python 경로: $pythonPath" -ForegroundColor Green
    $foundPaths += $pythonPath
} else {
    Write-Host "❌ Python을 찾을 수 없습니다." -ForegroundColor Red
}

# 4. 방화벽 규칙 생성
Write-Host "`n🛡️ 방화벽 규칙 생성 중..." -ForegroundColor Cyan

try {
    # 키움 API 인바운드 규칙
    New-NetFirewallRule -DisplayName "Kiwoom API Inbound" `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort Any `
        -Program $foundPaths[0] `
        -Description "키움 API 인바운드 통신 허용" `
        -ErrorAction SilentlyContinue
    
    Write-Host "✅ 키움 API 인바운드 규칙 생성 완료" -ForegroundColor Green
    
    # 키움 API 아웃바운드 규칙
    New-NetFirewallRule -DisplayName "Kiwoom API Outbound" `
        -Direction Outbound `
        -Action Allow `
        -Protocol TCP `
        -RemotePort Any `
        -Program $foundPaths[0] `
        -Description "키움 API 아웃바운드 통신 허용" `
        -ErrorAction SilentlyContinue
    
    Write-Host "✅ 키움 API 아웃바운드 규칙 생성 완료" -ForegroundColor Green
    
    # Python 키움 API 인바운드 규칙
    if ($pythonPath) {
        New-NetFirewallRule -DisplayName "Python Kiwoom API Inbound" `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort Any `
            -Program $pythonPath `
            -Description "Python 키움 API 인바운드 통신 허용" `
            -ErrorAction SilentlyContinue
        
        Write-Host "✅ Python 키움 API 인바운드 규칙 생성 완료" -ForegroundColor Green
        
        # Python 키움 API 아웃바운드 규칙
        New-NetFirewallRule -DisplayName "Python Kiwoom API Outbound" `
            -Direction Outbound `
            -Action Allow `
            -Protocol TCP `
            -RemotePort Any `
            -Program $pythonPath `
            -Description "Python 키움 API 아웃바운드 통신 허용" `
            -ErrorAction SilentlyContinue
        
        Write-Host "✅ Python 키움 API 아웃바운드 규칙 생성 완료" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ 방화벽 규칙 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Windows Defender 예외 추가
Write-Host "`n🛡️ Windows Defender 예외 추가 중..." -ForegroundColor Cyan

try {
    # 키움 폴더를 Windows Defender 예외에 추가
    $kiwoomFolder = "C:\Program Files (x86)\Kiwoom"
    if (Test-Path $kiwoomFolder) {
        Add-MpPreference -ExclusionPath $kiwoomFolder -ErrorAction SilentlyContinue
        Write-Host "✅ Windows Defender 예외 추가 완료: $kiwoomFolder" -ForegroundColor Green
    }
    
    # 현재 프로젝트 폴더도 예외에 추가
    $projectFolder = Get-Location
    Add-MpPreference -ExclusionPath $projectFolder -ErrorAction SilentlyContinue
    Write-Host "✅ Windows Defender 예외 추가 완료: $projectFolder" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Windows Defender 예외 추가 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. COM 보안 설정
Write-Host "`n🔒 COM 보안 설정 중..." -ForegroundColor Cyan

try {
    # COM 보안 설정 레지스트리 수정
    $comSecurityPath = "HKLM:\SOFTWARE\Microsoft\Rpc\Internet"
    
    # COM 보안 설정 확인 및 수정
    if (!(Test-Path $comSecurityPath)) {
        New-Item -Path $comSecurityPath -Force | Out-Null
    }
    
    Set-ItemProperty -Path $comSecurityPath -Name "EnableAuthnLevel" -Value 0 -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $comSecurityPath -Name "EnableAuthnLevelDefault" -Value 0 -ErrorAction SilentlyContinue
    
    Write-Host "✅ COM 보안 설정 완료" -ForegroundColor Green
    
} catch {
    Write-Host "❌ COM 보안 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. 최종 확인
Write-Host "`n📋 생성된 방화벽 규칙 확인:" -ForegroundColor Cyan

$newRules = Get-NetFirewallRule -DisplayName "*Kiwoom*" -ErrorAction SilentlyContinue
if ($newRules) {
    foreach ($rule in $newRules) {
        Write-Host "  - $($rule.DisplayName) (상태: $($rule.Enabled), 방향: $($rule.Direction))" -ForegroundColor White
    }
} else {
    Write-Host "⚠️ 키움 관련 방화벽 규칙을 찾을 수 없습니다." -ForegroundColor Yellow
}

Write-Host "`n📋 다음 단계:" -ForegroundColor Green
Write-Host "1. 키움 영웅문을 관리자 권한으로 실행하세요" -ForegroundColor White
Write-Host "2. Python 스크립트를 관리자 권한으로 실행하세요" -ForegroundColor White
Write-Host "3. API 테스트를 다시 실행해보세요" -ForegroundColor White

Write-Host "`n✅ 방화벽 규칙 설정 완료!" -ForegroundColor Green 