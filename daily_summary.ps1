# PowerShell 일일 요약 실행 스크립트
param(
    [switch]$Log,
    [string]$LogFile = "daily_summary.log"
)

# 로그 함수
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    if ($Log) {
        Add-Content -Path $LogFile -Value $logMessage
    }
    Write-Host $logMessage
}

Write-Log "========================================"
Write-Log "📊 일일 요약 리포트 자동 실행"
Write-Log "========================================"
Write-Log "실행 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log ""

# 현재 디렉토리로 이동
Set-Location $PSScriptRoot

try {
    # 가상환경 활성화
    Write-Log "가상환경 활성화 중..."
    & ".\venv\Scripts\Activate.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        throw "가상환경 활성화 실패"
    }
    
    # 일일 요약 실행
    Write-Log "일일 요약 리포트 생성 중..."
    python cross_platform_trader.py --daily-summary
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ 일일 요약 실행 완료"
    } else {
        Write-Log "❌ 일일 요약 실행 실패 (오류 코드: $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Log "❌ 오류 발생: $($_.Exception.Message)"
    exit 1
} finally {
    # 가상환경 비활성화
    deactivate
}

Write-Log ""
Write-Log "========================================"
Write-Log "📊 일일 요약 실행 종료"
Write-Log "========================================" 