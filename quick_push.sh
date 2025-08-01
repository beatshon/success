#!/bin/bash

# 빠른 Git 푸시 스크립트
# 사용법: ./quick_push.sh "커밋 메시지"

if [ $# -eq 0 ]; then
    echo "사용법: $0 \"커밋 메시지\""
    echo "예시: $0 \"API 연동 개선\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "🔄 빠른 Git 푸시 시작..."

# 현재 상태 확인
echo "📊 현재 Git 상태:"
git status --short

# 모든 변경사항 추가
git add .

# 커밋
echo "💾 커밋 중: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# 푸시
echo "🚀 푸시 중..."
git push

if [ $? -eq 0 ]; then
    echo "✅ 푸시 완료!"
    echo "📝 윈도우 서버에서 'git pull' 실행하세요."
else
    echo "❌ 푸시 실패!"
    exit 1
fi 