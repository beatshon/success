#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
맥과 윈도우 서버 간 동기화 상태 확인 스크립트
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

def get_file_hash(filepath):
    """파일의 MD5 해시값 계산"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_file_info(filepath):
    """파일 정보 가져오기"""
    try:
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'hash': get_file_hash(filepath)
        }
    except:
        return None

def load_config():
    """설정 파일 로드"""
    config_file = Path("config/windows_server.conf")
    if not config_file.exists():
        print("❌ 설정 파일을 찾을 수 없습니다: config/windows_server.conf")
        return None
    
    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"')
    
    return config

def check_remote_file(host, user, path, filepath, ssh_port=22):
    """원격 파일 정보 확인"""
    try:
        remote_path = f"{path}/{filepath}"
        cmd = f"ssh -p {ssh_port} {user}@{host} 'stat -c \"%s %Y\" \"{remote_path}\" 2>/dev/null || echo \"NOT_FOUND\"'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip() == "NOT_FOUND":
            return None
        
        size, mtime = result.stdout.strip().split()
        return {
            'size': int(size),
            'mtime': datetime.fromtimestamp(int(mtime)).isoformat()
        }
    except:
        return None

def compare_files(local_info, remote_info):
    """파일 비교"""
    if not local_info or not remote_info:
        return "missing"
    
    if local_info['size'] != remote_info['size']:
        return "different_size"
    
    # 시간 차이가 5분 이내면 동기화됨으로 간주
    local_time = datetime.fromisoformat(local_info['mtime'])
    remote_time = datetime.fromisoformat(remote_info['mtime'])
    time_diff = abs((local_time - remote_time).total_seconds())
    
    if time_diff <= 300:  # 5분
        return "synced"
    else:
        return "different_time"

def main():
    """메인 함수"""
    print("=" * 60)
    print("맥-윈도우 서버 동기화 상태 확인")
    print("=" * 60)
    
    # 설정 로드
    config = load_config()
    if not config:
        return
    
    print(f"윈도우 서버: {config.get('WINDOWS_HOST', 'N/A')}")
    print(f"사용자: {config.get('WINDOWS_USER', 'N/A')}")
    print(f"경로: {config.get('WINDOWS_PATH', 'N/A')}")
    print()
    
    # 확인할 파일 목록
    files_to_check = [
        "windows_api_test.py",
        "start_windows_api_server.py",
        "integrated_trading_system.py",
        "kiwoom_api.py",
        "config/kiwoom_config.py",
        "requirements_windows.txt",
        "run_windows_api_test.bat",
        "start_windows_api_server.bat"
    ]
    
    print("파일 동기화 상태 확인 중...")
    print("-" * 60)
    
    synced_count = 0
    different_count = 0
    missing_count = 0
    
    for filepath in files_to_check:
        print(f"확인 중: {filepath}")
        
        # 로컬 파일 정보
        local_info = get_file_info(filepath)
        
        # 원격 파일 정보
        remote_info = check_remote_file(
            config['WINDOWS_HOST'],
            config['WINDOWS_USER'],
            config['WINDOWS_PATH'],
            filepath,
            config.get('SSH_PORT', '22')
        )
        
        # 상태 비교
        status = compare_files(local_info, remote_info)
        
        if status == "synced":
            print(f"  ✅ 동기화됨")
            synced_count += 1
        elif status == "missing":
            print(f"  ❌ 파일 없음")
            missing_count += 1
        else:
            print(f"  ⚠️  동기화 필요")
            different_count += 1
        
        # 상세 정보 출력
        if local_info:
            print(f"    로컬: {local_info['size']} bytes, {local_info['mtime']}")
        if remote_info:
            print(f"    원격: {remote_info['size']} bytes, {remote_info['mtime']}")
        print()
    
    # 결과 요약
    print("=" * 60)
    print("동기화 상태 요약:")
    print(f"  ✅ 동기화됨: {synced_count}개")
    print(f"  ⚠️  동기화 필요: {different_count}개")
    print(f"  ❌ 파일 없음: {missing_count}개")
    print()
    
    # 권장사항
    if different_count > 0 or missing_count > 0:
        print("권장사항:")
        print("1. 맥에서 동기화 실행:")
        print("   ./sync_from_mac.sh")
        print("   또는")
        print("   ./quick_sync_to_windows.sh")
        print()
        print("2. 윈도우에서 파일 가져오기:")
        print("   ./pull_from_mac.bat")
    else:
        print("🎉 모든 파일이 동기화되었습니다!")
    
    # 결과를 JSON 파일로 저장
    result = {
        'timestamp': datetime.now().isoformat(),
        'server_info': {
            'host': config.get('WINDOWS_HOST'),
            'user': config.get('WINDOWS_USER'),
            'path': config.get('WINDOWS_PATH')
        },
        'summary': {
            'synced': synced_count,
            'different': different_count,
            'missing': missing_count
        }
    }
    
    os.makedirs('logs', exist_ok=True)
    with open('logs/sync_status.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"상세 결과 저장: logs/sync_status.json")

if __name__ == "__main__":
    main() 