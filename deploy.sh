#!/bin/bash
echo "🚀 AWS EC2 배포 시작"
cd /opt/kiwoom-trading
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ 배포 완료"
