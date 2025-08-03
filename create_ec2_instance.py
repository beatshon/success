#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWS EC2 인스턴스 생성 스크립트
키움 트레이딩 시스템을 위한 EC2 인스턴스를 자동으로 생성합니다.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
from loguru import logger

class EC2InstanceCreator:
    """EC2 인스턴스 생성 클래스"""
    
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.ec2_resource = boto3.resource('ec2')
        
    def create_security_group(self, group_name="kiwoom-trading-sg"):
        """보안 그룹 생성"""
        try:
            # 기존 보안 그룹 확인
            response = self.ec2_client.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [group_name]}]
            )
            
            if response['SecurityGroups']:
                logger.info(f"기존 보안 그룹 사용: {group_name}")
                return response['SecurityGroups'][0]['GroupId']
            
            # 새 보안 그룹 생성
            response = self.ec2_client.create_security_group(
                GroupName=group_name,
                Description='Security group for Kiwoom Trading System'
            )
            security_group_id = response['GroupId']
            
            # 인바운드 규칙 추가
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 8080,
                        'ToPort': 8080,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            logger.info(f"보안 그룹 생성 완료: {security_group_id}")
            return security_group_id
            
        except ClientError as e:
            logger.error(f"보안 그룹 생성 실패: {e}")
            return None
    
    def get_latest_ubuntu_ami(self):
        """최신 Ubuntu AMI ID 조회"""
        try:
            response = self.ec2_client.describe_images(
                Owners=['099720109477'],  # Canonical
                Filters=[
                    {'Name': 'name', 'Values': ['ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*']},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            # 최신 AMI 선택
            images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
            if images:
                ami_id = images[0]['ImageId']
                logger.info(f"Ubuntu 20.04 AMI 선택: {ami_id}")
                return ami_id
            
            logger.error("사용 가능한 Ubuntu AMI를 찾을 수 없습니다.")
            return None
            
        except ClientError as e:
            logger.error(f"AMI 조회 실패: {e}")
            return None
    
    def create_key_pair(self, key_name="kiwoom-trading-key"):
        """키 페어 생성"""
        try:
            # 기존 키 페어 확인
            response = self.ec2_client.describe_key_pairs(
                KeyNames=[key_name]
            )
            if response['KeyPairs']:
                logger.info(f"기존 키 페어 사용: {key_name}")
                return key_name
                
        except ClientError:
            pass
        
        try:
            # 새 키 페어 생성
            response = self.ec2_client.create_key_pair(KeyName=key_name)
            
            # 프라이빗 키 저장
            with open(f"{key_name}.pem", "w") as f:
                f.write(response['KeyMaterial'])
            
            # 키 파일 권한 설정
            import os
            os.chmod(f"{key_name}.pem", 0o400)
            
            logger.info(f"키 페어 생성 완료: {key_name}")
            logger.info(f"프라이빗 키 저장: {key_name}.pem")
            return key_name
            
        except ClientError as e:
            logger.error(f"키 페어 생성 실패: {e}")
            return None
    
    def create_ec2_instance(self, instance_type="t3.micro", key_name=None, security_group_id=None):
        """EC2 인스턴스 생성"""
        try:
            # AMI ID 조회
            ami_id = self.get_latest_ubuntu_ami()
            if not ami_id:
                return None
            
            # 인스턴스 생성
            response = self.ec2_client.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                KeyName=key_name,
                SecurityGroupIds=[security_group_id] if security_group_id else [],
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'Kiwoom-Trading-System'},
                            {'Key': 'Project', 'Value': 'Kiwoom-Trading'},
                            {'Key': 'Environment', 'Value': 'Production'}
                        ]
                    }
                ],
                UserData='''#!/bin/bash
# EC2 인스턴스 초기 설정
apt-get update
apt-get install -y docker.io docker-compose git curl
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu
mkdir -p /opt/kiwoom-trading
chown ubuntu:ubuntu /opt/kiwoom-trading
echo "EC2 인스턴스 초기 설정 완료"
'''
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            logger.info(f"EC2 인스턴스 생성 시작: {instance_id}")
            
            # 인스턴스가 실행될 때까지 대기
            logger.info("인스턴스 실행 대기 중...")
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            
            # 퍼블릭 IP 조회
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
            
            logger.info(f"EC2 인스턴스 생성 완료!")
            logger.info(f"인스턴스 ID: {instance_id}")
            logger.info(f"퍼블릭 IP: {public_ip}")
            
            return {
                'instance_id': instance_id,
                'public_ip': public_ip,
                'key_name': key_name
            }
            
        except ClientError as e:
            logger.error(f"EC2 인스턴스 생성 실패: {e}")
            return None
    
    def create_ec2_setup(self):
        """전체 EC2 설정 생성"""
        logger.info("🚀 AWS EC2 인스턴스 생성 시작")
        
        # 1. 키 페어 생성
        logger.info("1단계: 키 페어 생성")
        key_name = self.create_key_pair()
        if not key_name:
            return None
        
        # 2. 보안 그룹 생성
        logger.info("2단계: 보안 그룹 생성")
        security_group_id = self.create_security_group()
        if not security_group_id:
            return None
        
        # 3. EC2 인스턴스 생성
        logger.info("3단계: EC2 인스턴스 생성")
        instance_info = self.create_ec2_instance(
            key_name=key_name,
            security_group_id=security_group_id
        )
        
        if instance_info:
            # 연결 정보 저장
            connection_info = {
                'instance_id': instance_info['instance_id'],
                'public_ip': instance_info['public_ip'],
                'key_file': f"{key_name}.pem",
                'username': 'ubuntu',
                'ssh_command': f"ssh -i {key_name}.pem ubuntu@{instance_info['public_ip']}",
                'web_url': f"http://{instance_info['public_ip']}:8080"
            }
            
            with open('ec2_connection_info.json', 'w') as f:
                json.dump(connection_info, f, indent=2)
            
            logger.info("✅ EC2 인스턴스 생성 완료!")
            logger.info(f"SSH 연결: {connection_info['ssh_command']}")
            logger.info(f"웹 대시보드: {connection_info['web_url']}")
            logger.info("연결 정보가 ec2_connection_info.json에 저장되었습니다.")
            
            return connection_info
        
        return None

def main():
    """메인 실행 함수"""
    creator = EC2InstanceCreator()
    connection_info = creator.create_ec2_setup()
    
    if connection_info:
        print("\n" + "="*50)
        print("🎉 EC2 인스턴스 생성 완료!")
        print("="*50)
        print(f"인스턴스 ID: {connection_info['instance_id']}")
        print(f"퍼블릭 IP: {connection_info['public_ip']}")
        print(f"키 파일: {connection_info['key_file']}")
        print(f"SSH 연결: {connection_info['ssh_command']}")
        print(f"웹 대시보드: {connection_info['web_url']}")
        print("\n다음 단계:")
        print("1. 프로젝트 파일을 EC2로 업로드")
        print("2. EC2에서 배포 스크립트 실행")
        print("3. 웹 대시보드 접속 확인")
        print("="*50)
    else:
        print("❌ EC2 인스턴스 생성 실패")

if __name__ == "__main__":
    main() 