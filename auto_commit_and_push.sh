#!/bin/bash

# 자동 커밋 및 푸시 스크립트
# 파일 변경 시 자동으로 GitHub에 푸시

echo "🔄 자동 커밋 및 푸시 시작"
echo "=========================="

# 변경된 파일 확인
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 변경된 파일이 없습니다."
    exit 0
fi

# 변경된 파일 목록 표시
echo "📋 변경된 파일:"
git status --porcelain

# 커밋 메시지 생성
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
commit_message="Auto sync: $timestamp"

# 변경사항 스테이징
echo "📦 변경사항 스테이징 중..."
git add .

# 커밋
echo "💾 커밋 중..."
git commit -m "$commit_message"

# 푸시
echo "🚀 GitHub에 푸시 중..."
if git push origin main; then
    echo "✅ 푸시 완료"
else
    echo "❌ 푸시 실패"
    exit 1
fi

echo "✅ 자동 동기화 완료"
