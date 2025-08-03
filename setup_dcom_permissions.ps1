# DCOM 권한 설정 스크립트
# 관리자 권한으로 실행해야 합니다.

Write-Host "🔧 DCOM 권한 설정 시작..." -ForegroundColor Green

# 1. 현재 사용자 정보 확인
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "현재 사용자: $currentUser" -ForegroundColor Yellow

# 2. DCOM 설정 확인
Write-Host "`n📋 DCOM 설정 확인 중..." -ForegroundColor Cyan

try {
    # KHOpenAPI Control의 CLSID 확인
    $khopenapiPath = "HKLM:\SOFTWARE\Classes\KHOPENAPI.KHOpenAPICtrl.1"
    $clsidPath = Get-ItemProperty -Path $khopenapiPath -Name "CLSID" -ErrorAction SilentlyContinue
    
    if ($clsidPath) {
        Write-Host "✅ KHOpenAPI Control 레지스트리 확인됨" -ForegroundColor Green
        Write-Host "CLSID: $($clsidPath.CLSID)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ KHOpenAPI Control 레지스트리를 찾을 수 없습니다." -ForegroundColor Red
        Write-Host "키움 Open API+가 제대로 설치되지 않았을 수 있습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ DCOM 설정 확인 중 오류: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. DCOM 구성 도구 실행 안내
Write-Host "`n🔧 DCOM 구성 도구 실행 안내:" -ForegroundColor Cyan
Write-Host "1. 'dcomcnfg' 명령어를 실행하세요" -ForegroundColor White
Write-Host "2. 컴퓨터 → 내 컴퓨터 → DCOM 구성 → KHOpenAPI Control 선택" -ForegroundColor White
Write-Host "3. 속성 → 보안 탭 → '액세스 권한'과 '시작 및 활성화 권한'에 다음 계정 추가:" -ForegroundColor White
Write-Host "   - $currentUser" -ForegroundColor Yellow
Write-Host "   - Everyone (테스트용)" -ForegroundColor Yellow

# 4. 방화벽 설정 확인
Write-Host "`n🛡️ 방화벽 설정 확인 중..." -ForegroundColor Cyan

$firewallRules = Get-NetFirewallRule -DisplayName "*Kiwoom*" -ErrorAction SilentlyContinue
if ($firewallRules) {
    Write-Host "✅ 키움 관련 방화벽 규칙 발견:" -ForegroundColor Green
    foreach ($rule in $firewallRules) {
        Write-Host "  - $($rule.DisplayName) (상태: $($rule.Enabled))" -ForegroundColor White
    }
} else {
    Write-Host "⚠️ 키움 관련 방화벽 규칙이 없습니다." -ForegroundColor Yellow
}

# 5. 방화벽 규칙 생성 안내
Write-Host "`n🛡️ 방화벽 규칙 생성 안내:" -ForegroundColor Cyan
Write-Host "다음 프로그램들을 방화벽 예외에 추가하세요:" -ForegroundColor White
Write-Host "- 키움 영웅문 실행파일" -ForegroundColor White
Write-Host "- KHOpenAPI 관련 파일들" -ForegroundColor White
Write-Host "- Python 실행파일 (32비트)" -ForegroundColor White

# 6. 레지스트리 권한 설정
Write-Host "`n🔑 레지스트리 권한 설정 중..." -ForegroundColor Cyan

try {
    # KHOpenAPI Control에 대한 권한 설정
    $acl = Get-Acl "HKLM:\SOFTWARE\Classes\KHOPENAPI.KHOpenAPICtrl.1"
    $accessRule = New-Object System.Security.AccessControl.RegistryAccessRule($currentUser, "FullControl", "Allow")
    $acl.SetAccessRule($accessRule)
    Set-Acl "HKLM:\SOFTWARE\Classes\KHOPENAPI.KHOpenAPICtrl.1" $acl
    Write-Host "✅ 레지스트리 권한 설정 완료" -ForegroundColor Green
} catch {
    Write-Host "❌ 레지스트리 권한 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. COM 보안 설정 확인
Write-Host "`n🔒 COM 보안 설정 확인 중..." -ForegroundColor Cyan

try {
    $comSecurityPath = "HKLM:\SOFTWARE\Microsoft\Rpc\Internet"
    $comSecurity = Get-ItemProperty -Path $comSecurityPath -ErrorAction SilentlyContinue
    
    if ($comSecurity) {
        Write-Host "✅ COM 보안 설정 확인됨" -ForegroundColor Green
    } else {
        Write-Host "⚠️ COM 보안 설정을 확인할 수 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ COM 보안 설정 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n📋 다음 단계:" -ForegroundColor Green
Write-Host "1. 'dcomcnfg' 명령어를 실행하여 DCOM 설정을 수동으로 구성하세요" -ForegroundColor White
Write-Host "2. 키움 영웅문을 관리자 권한으로 실행하세요" -ForegroundColor White
Write-Host "3. Python 스크립트를 관리자 권한으로 실행하세요" -ForegroundColor White
Write-Host "4. 방화벽에서 키움 관련 프로그램들을 허용하세요" -ForegroundColor White

Write-Host "`n✅ DCOM 권한 설정 스크립트 완료!" -ForegroundColor Green 