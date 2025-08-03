#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWS EC2 클라우드 배포 설정 스크립트
"""

import os
from loguru import logger

def create_dockerfile():
    """Dockerfile 생성"""
    content = '''FROM python:3.9-slim
WORKDIR /app
COPY requirements_aws.txt .
RUN pip install -r requirements_aws.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "mac_real_time_server:app"]
'''
    with open("Dockerfile", "w") as f:
        f.write(content)
    logger.info("Dockerfile 생성 완료")

def create_requirements():
    """requirements_aws.txt 생성"""
    content = '''flask==2.3.3
flask-cors==4.0.0
requests==2.31.0
pandas==2.0.3
numpy==1.24.3
loguru==0.7.0
gunicorn==21.2.0
redis==4.6.0
boto3==1.34.0
python-dotenv==1.0.0
'''
    with open("requirements_aws.txt", "w") as f:
        f.write(content)
    logger.info("requirements_aws.txt 생성 완료")

def create_deploy_script():
    """배포 스크립트 생성"""
    content = '''#!/bin/bash
echo "🚀 AWS EC2 배포 시작"
cd /opt/kiwoom-trading
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ 배포 완료"
'''
    with open("deploy.sh", "w") as f:
        f.write(content)
    os.chmod("deploy.sh", 0o755)
    logger.info("deploy.sh 생성 완료")

def create_docker_compose():
    """docker-compose.yml 생성"""
    content = '''version: '3.8'
services:
  kiwoom-trading:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
'''
    with open("docker-compose.yml", "w") as f:
        f.write(content)
    logger.info("docker-compose.yml 생성 완료")

def main():
    """메인 실행 함수"""
    logger.info("AWS EC2 배포 파일 생성 시작")
    
    create_dockerfile()
    create_requirements()
    create_deploy_script()
    create_docker_compose()
    
    logger.info("✅ AWS EC2 배포 파일 생성 완료!")

if __name__ == "__main__":
    main() 