#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EC2로 프로젝트 파일 업로드 스크립트
생성된 EC2 인스턴스로 키움 트레이딩 시스템 파일들을 업로드합니다.
"""

import json
import os
import subprocess
import tarfile
from pathlib import Path
from loguru import logger

class EC2Uploader:
    """EC2 파일 업로드 클래스"""
    
    def __init__(self):
        self.connection_info = self.load_connection_info()
        
    def load_connection_info(self):
        """연결 정보 로드"""
        try:
            with open('ec2_connection_info.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("ec2_connection_info.json 파일을 찾을 수 없습니다.")
            logger.error("먼저 create_ec2_instance.py를 실행하여 EC2 인스턴스를 생성하세요.")
            return None
    
    def create_project_archive(self):
        """프로젝트 파일 압축"""
        logger.info("프로젝트 파일 압축 중...")
        
        # 압축할 파일/폴더 목록
        include_patterns = [
            '*.py',
            '*.md',
            '*.txt',
            '*.json',
            '*.yml',
            '*.yaml',
            '*.sh',
            'templates/',
            'config/',
            'logs/',
            'data/',
            'Dockerfile',
            'docker-compose.yml',
            'requirements_aws.txt',
            'deploy.sh'
        ]
        
        # 제외할 파일/폴더
        exclude_patterns = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.env',
            'venv',
            'node_modules',
            '*.log',
            '*.tmp',
            '.DS_Store'
        ]
        
        archive_name = 'kiwoom-trading-project.tar.gz'
        
        with tarfile.open(archive_name, 'w:gz') as tar:
            for pattern in include_patterns:
                if os.path.exists(pattern):
                    if os.path.isfile(pattern):
                        tar.add(pattern)
                    elif os.path.isdir(pattern):
                        for root, dirs, files in os.walk(pattern):
                            # 제외할 디렉토리 제거
                            dirs[:] = [d for d in dirs if d not in exclude_patterns]
                            
                            for file in files:
                                if not any(exclude in file for exclude in exclude_patterns):
                                    file_path = os.path.join(root, file)
                                    tar.add(file_path)
        
        logger.info(f"프로젝트 압축 완료: {archive_name}")
        return archive_name
    
    def upload_to_ec2(self, archive_name):
        """EC2로 파일 업로드"""
        if not self.connection_info:
            return False
        
        try:
            logger.info("EC2로 파일 업로드 중...")
            
            # SCP 명령어 구성
            scp_command = [
                'scp',
                '-i', self.connection_info['key_file'],
                '-o', 'StrictHostKeyChecking=no',
                archive_name,
                f"{self.connection_info['username']}@{self.connection_info['public_ip']}:/home/ubuntu/"
            ]
            
            # SCP 실행
            result = subprocess.run(scp_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("파일 업로드 완료!")
                return True
            else:
                logger.error(f"파일 업로드 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"업로드 중 오류 발생: {e}")
            return False
    
    def setup_ec2_environment(self):
        """EC2 환경 설정"""
        if not self.connection_info:
            return False
        
        try:
            logger.info("EC2 환경 설정 중...")
            
            # SSH 명령어 구성
            ssh_commands = [
                # 프로젝트 디렉토리 생성 및 파일 압축 해제
                "sudo mkdir -p /opt/kiwoom-trading",
                "sudo chown ubuntu:ubuntu /opt/kiwoom-trading",
                "cd /opt/kiwoom-trading",
                "tar -xzf /home/ubuntu/kiwoom-trading-project.tar.gz",
                "chmod +x deploy.sh",
                
                # 시스템 업데이트 및 Docker 설치
                "sudo apt-get update",
                "sudo apt-get install -y docker.io docker-compose",
                "sudo systemctl start docker",
                "sudo systemctl enable docker",
                
                # Docker 그룹 생성 및 사용자 추가
                "sudo groupadd docker 2>/dev/null || true",
                "sudo usermod -aG docker ubuntu",
                
                # 프로젝트 파일 정리
                "rm /home/ubuntu/kiwoom-trading-project.tar.gz",
                
                # 배포 준비 완료 메시지
                "echo 'EC2 환경 설정 완료!'"
            ]
            
            # SSH로 명령어 실행
            ssh_command = [
                'ssh',
                '-i', self.connection_info['key_file'],
                '-o', 'StrictHostKeyChecking=no',
                f"{self.connection_info['username']}@{self.connection_info['public_ip']}",
                ' && '.join(ssh_commands)
            ]
            
            result = subprocess.run(ssh_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("EC2 환경 설정 완료!")
                return True
            else:
                logger.error(f"EC2 환경 설정 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"환경 설정 중 오류 발생: {e}")
            return False
    
    def deploy_application(self):
        """애플리케이션 배포"""
        if not self.connection_info:
            return False
        
        try:
            logger.info("애플리케이션 배포 중...")
            
            # 배포 명령어
            deploy_commands = [
                "cd /opt/kiwoom-trading",
                "./deploy.sh"
            ]
            
            # SSH로 배포 실행
            ssh_command = [
                'ssh',
                '-i', self.connection_info['key_file'],
                '-o', 'StrictHostKeyChecking=no',
                f"{self.connection_info['username']}@{self.connection_info['public_ip']}",
                ' && '.join(deploy_commands)
            ]
            
            result = subprocess.run(ssh_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("애플리케이션 배포 완료!")
                return True
            else:
                logger.error(f"배포 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"배포 중 오류 발생: {e}")
            return False
    
    def check_deployment_status(self):
        """배포 상태 확인"""
        if not self.connection_info:
            return False
        
        try:
            logger.info("배포 상태 확인 중...")
            
            # 상태 확인 명령어
            status_commands = [
                "cd /opt/kiwoom-trading",
                "docker ps",
                "curl -f http://localhost:8080/api/status || echo '서비스가 아직 시작되지 않았습니다.'"
            ]
            
            # SSH로 상태 확인
            ssh_command = [
                'ssh',
                '-i', self.connection_info['key_file'],
                '-o', 'StrictHostKeyChecking=no',
                f"{self.connection_info['username']}@{self.connection_info['public_ip']}",
                ' && '.join(status_commands)
            ]
            
            result = subprocess.run(ssh_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("배포 상태 확인 완료!")
                logger.info("출력:")
                print(result.stdout)
                return True
            else:
                logger.error(f"상태 확인 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"상태 확인 중 오류 발생: {e}")
            return False
    
    def upload_and_deploy(self):
        """전체 업로드 및 배포 프로세스"""
        logger.info("🚀 EC2 업로드 및 배포 시작")
        
        # 1. 프로젝트 파일 압축
        logger.info("1단계: 프로젝트 파일 압축")
        archive_name = self.create_project_archive()
        
        # 2. EC2로 파일 업로드
        logger.info("2단계: EC2로 파일 업로드")
        if not self.upload_to_ec2(archive_name):
            return False
        
        # 3. EC2 환경 설정
        logger.info("3단계: EC2 환경 설정")
        if not self.setup_ec2_environment():
            return False
        
        # 4. 애플리케이션 배포
        logger.info("4단계: 애플리케이션 배포")
        if not self.deploy_application():
            return False
        
        # 5. 배포 상태 확인
        logger.info("5단계: 배포 상태 확인")
        self.check_deployment_status()
        
        # 6. 로컬 압축 파일 정리
        if os.path.exists(archive_name):
            os.remove(archive_name)
            logger.info(f"로컬 압축 파일 정리: {archive_name}")
        
        logger.info("✅ EC2 업로드 및 배포 완료!")
        return True

def main():
    """메인 실행 함수"""
    uploader = EC2Uploader()
    
    if uploader.connection_info:
        print("\n" + "="*50)
        print("📤 EC2 업로드 및 배포")
        print("="*50)
        print(f"인스턴스 IP: {uploader.connection_info['public_ip']}")
        print(f"키 파일: {uploader.connection_info['key_file']}")
        print("="*50)
        
        success = uploader.upload_and_deploy()
        
        if success:
            print("\n" + "="*50)
            print("🎉 배포 완료!")
            print("="*50)
            print(f"웹 대시보드: {uploader.connection_info['web_url']}")
            print(f"SSH 연결: {uploader.connection_info['ssh_command']}")
            print("\n다음 단계:")
            print("1. 웹 브라우저에서 대시보드 접속")
            print("2. 시스템 모니터링")
            print("3. 로그 확인")
            print("="*50)
        else:
            print("\n❌ 배포 실패")
    else:
        print("❌ 연결 정보를 찾을 수 없습니다.")
        print("먼저 create_ec2_instance.py를 실행하여 EC2 인스턴스를 생성하세요.")

if __name__ == "__main__":
    main() 