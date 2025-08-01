@echo off
REM 수동 동기화 배치 파일 (Git 없이 사용)
REM GitHub에서 ZIP 파일을 다운로드하여 사용

title Manual Sync System

echo.
echo ========================================
echo    수동 동기화 시스템
echo ========================================
echo.

echo 📋 현재 상태:
echo - 맥에서 작업한 파일이 GitHub에 업로드됨
echo - Windows에서 ZIP 파일을 다운로드하여 사용
echo.

echo 🔄 동기화 방법:
echo 1. GitHub에서 최신 ZIP 파일 다운로드
echo 2. 기존 폴더 백업
echo 3. 새 파일로 교체
echo.

echo ⚠️  주의사항:
echo - 기존 설정 파일은 백업하세요
echo - config/windows_server.conf 파일은 보존하세요
echo.

pause

echo.
echo ✅ 수동 동기화 가이드 완료
echo.
echo 📞 다음 단계:
echo 1. GitHub에서 ZIP 다운로드
echo 2. 압축 해제 후 파일 교체
echo 3. Windows 서버 시작
echo.

pause 