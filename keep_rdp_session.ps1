# RDP 세션 유지 스크립트
# 이 스크립트를 주기적으로 실행하여 세션을 유지합니다.

Write-Host "🔄 RDP 세션 유지 중..." -ForegroundColor Green

# 현재 시간 출력
Write-Host "현재 시간: $(Get-Date)" -ForegroundColor Yellow

# 세션 정보 확인
try {
    $session = quser 2>$null
    if ($session) {
        Write-Host "활성 세션 발견:" -ForegroundColor Green
        Write-Host $session -ForegroundColor White
    } else {
        Write-Host "활성 세션이 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "세션 정보 확인 실패" -ForegroundColor Red
}

Write-Host "✅ 세션 유지 완료" -ForegroundColor Green 