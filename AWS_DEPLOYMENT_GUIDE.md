# 🚀 AWS EC2 클라우드 배포 가이드

## 📋 개요

이 가이드는 키움 트레이딩 시스템을 AWS EC2에 배포하는 방법을 설명합니다.

## 🎯 배포 목표

- **24시간 운영**: 서버가 항상 켜져있음
- **안정성**: 전용 서버로 안정적 운영
- **확장성**: 필요시 성능 확장 가능
- **접근성**: 어디서든 웹으로 접근 가능

## 📦 배포 파일들

생성된 파일들:
- `Dockerfile`: Docker 컨테이너 설정
- `docker-compose.yml`: 컨테이너 오케스트레이션
- `requirements_aws.txt`: AWS 배포용 Python 패키지
- `deploy.sh`: 배포 스크립트

## 🚀 배포 단계

### 1단계: AWS EC2 인스턴스 생성

#### AWS 콘솔에서 생성
1. AWS 콘솔 로그인
2. EC2 서비스 선택
3. "인스턴스 시작" 클릭
4. 설정:
   - **AMI**: Ubuntu 20.04 LTS
   - **인스턴스 타입**: t3.medium (2vCPU, 4GB RAM)
   - **스토리지**: 20GB GP3
   - **보안 그룹**: SSH(22), HTTP(80), HTTPS(443) 허용

#### AWS CLI로 생성
```bash
# AWS CLI 설치 (맥)
brew install awscli

# AWS 설정
aws configure

# EC2 인스턴스 생성
aws ec2 run-instances \
    --image-id ami-0c9c942bd7bf113a2 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx
```

### 2단계: 프로젝트 파일 업로드

#### SCP로 업로드
```bash
# 프로젝트 압축
tar -czf kiwoom-trading.tar.gz .

# EC2로 업로드
scp -i your-key.pem kiwoom-trading.tar.gz ubuntu@your-ec2-ip:/home/ubuntu/

# EC2에서 압축 해제
ssh -i your-key.pem ubuntu@your-ec2-ip
cd /home/ubuntu
sudo mkdir -p /opt/kiwoom-trading
sudo tar -xzf kiwoom-trading.tar.gz -C /opt/kiwoom-trading
sudo chown -R ubuntu:ubuntu /opt/kiwoom-trading
```

#### Git 사용
```bash
# EC2에 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# Git 설치 및 프로젝트 클론
sudo apt-get update
sudo apt-get install -y git
sudo mkdir -p /opt/kiwoom-trading
sudo chown ubuntu:ubuntu /opt/kiwoom-trading
cd /opt/kiwoom-trading
git clone https://github.com/your-repo/kiwoom-trading.git .
```

### 3단계: EC2 인스턴스 설정

```bash
# EC2에 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 시스템 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# Docker 설치
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# 재로그인 또는 그룹 적용
newgrp docker
```

### 4단계: 애플리케이션 배포

```bash
# 프로젝트 디렉토리로 이동
cd /opt/kiwoom-trading

# 배포 스크립트 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

### 5단계: 웹 대시보드 접속

배포 완료 후 웹 브라우저에서 접속:
```
http://your-ec2-public-ip:8080
```

## 📊 모니터링

### 시스템 상태 확인
```bash
# Docker 컨테이너 상태
docker ps

# 애플리케이션 로그
docker-compose logs -f kiwoom-trading

# 시스템 리소스
htop
df -h
free -h
```

### 자동 모니터링 스크립트
```bash
# 모니터링 스크립트 생성
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== 시스템 상태 ==="
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')"
echo "메모리: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "디스크: $(df -h / | awk 'NR==2 {print $5}')"
echo "=== 컨테이너 상태 ==="
docker ps
echo "=== 최근 로그 ==="
docker-compose logs --tail=10
EOF

chmod +x monitor.sh
./monitor.sh
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8080

# 기존 프로세스 종료
sudo kill -9 <PID>
```

#### 2. 메모리 부족
```bash
# Docker 정리
docker system prune -a

# 불필요한 이미지 제거
docker image prune -a
```

#### 3. 디스크 공간 부족
```bash
# 디스크 사용량 확인
df -h

# Docker 정리
docker system prune -a --volumes
```

### 로그 확인
```bash
# 애플리케이션 로그
docker-compose logs kiwoom-trading

# 실시간 로그 모니터링
docker-compose logs -f kiwoom-trading

# 특정 시간대 로그
docker-compose logs --since="2024-01-01T00:00:00" kiwoom-trading
```

## 🔒 보안 설정

### 1. 방화벽 설정
```bash
# UFW 방화벽 활성화
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8080
```

### 2. SSL 인증서 설정 (선택사항)
```bash
# Certbot 설치
sudo apt-get install -y certbot python3-certbot-nginx

# SSL 인증서 발급 (도메인이 있는 경우)
sudo certbot --nginx -d your-domain.com
```

### 3. 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 환경변수 편집
nano .env
```

## 💰 비용 최적화

### 예상 월 비용 (t3.medium)
- **EC2 인스턴스**: $30-50
- **데이터 전송**: $5-10
- **스토리지**: $5-10
- **총 예상 비용**: $40-70/월

### 비용 절약 팁
1. **Spot Instance 사용**: 60-90% 비용 절약
2. **Reserved Instance**: 장기 사용시 할인
3. **Auto Scaling**: 필요시에만 확장
4. **S3 Intelligent Tiering**: 스토리지 비용 절약

## 🔄 자동화

### 자동 배포 설정
```bash
# GitHub Actions 워크플로우 생성
mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to AWS EC2

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to EC2
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/kiwoom-trading
          git pull origin main
          ./deploy.sh
EOF
```

### 자동 백업 설정
```bash
# 백업 스크립트 생성
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
mkdir -p $BACKUP_DIR

# 데이터 백업
tar -czf $BACKUP_DIR/kiwoom-trading_$DATE.tar.gz /opt/kiwoom-trading/data

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# 크론 작업 추가 (매일 새벽 2시)
crontab -e
# 0 2 * * * /opt/kiwoom-trading/backup.sh
```

## 📞 지원

### 문제 발생시 확인사항
1. **로그 확인**: `docker-compose logs`
2. **시스템 리소스**: `htop`, `df -h`
3. **네트워크 연결**: `curl localhost:8080/api/status`
4. **Docker 상태**: `docker ps`, `docker system df`

### 연락처
- **GitHub Issues**: 프로젝트 저장소
- **AWS Support**: AWS 콘솔에서 지원 티켓 생성

## ✅ 배포 완료 체크리스트

- [ ] EC2 인스턴스 생성 완료
- [ ] 프로젝트 파일 업로드 완료
- [ ] Docker 설치 및 설정 완료
- [ ] 애플리케이션 배포 완료
- [ ] 웹 대시보드 접속 확인
- [ ] 모니터링 설정 완료
- [ ] 보안 설정 완료
- [ ] 자동화 설정 완료

---

**🎉 축하합니다! AWS EC2 클라우드 배포가 완료되었습니다!**

이제 24시간 운영되는 키움 트레이딩 시스템을 사용할 수 있습니다. 