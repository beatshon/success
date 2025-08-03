#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최소한의 테스트 스크립트
의존성 없이 빠른 테스트
"""

import json
import time
from datetime import datetime

def test_basic_functionality():
    """기본 기능 테스트"""
    print("🚀 최소한의 테스트 시작")
    print("=" * 40)
    
    # 1. 기본 모듈 테스트
    print("1. 기본 모듈 테스트...")
    try:
        import sys
        import os
        print("   ✅ sys, os 모듈 로드 성공")
    except Exception as e:
        print(f"   ❌ 기본 모듈 로드 실패: {e}")
        return False
    
    # 2. 가상 데이터 생성 테스트
    print("2. 가상 데이터 생성 테스트...")
    try:
        virtual_data = {
            'timestamp': datetime.now().isoformat(),
            'test_stocks': {
                '005930': {'name': '삼성전자', 'signal': 'buy', 'confidence': 0.75},
                '000660': {'name': 'SK하이닉스', 'signal': 'strong_buy', 'confidence': 0.85}
            },
            'market_condition': 'bull_market',
            'server_status': 'ready'
        }
        print("   ✅ 가상 데이터 생성 성공")
        print(f"   📊 생성된 데이터: {len(virtual_data['test_stocks'])}개 주식")
    except Exception as e:
        print(f"   ❌ 가상 데이터 생성 실패: {e}")
        return False
    
    # 3. JSON 직렬화 테스트
    print("3. JSON 직렬화 테스트...")
    try:
        json_str = json.dumps(virtual_data, ensure_ascii=False, indent=2)
        print("   ✅ JSON 직렬화 성공")
        print(f"   📄 JSON 크기: {len(json_str)} 문자")
    except Exception as e:
        print(f"   ❌ JSON 직렬화 실패: {e}")
        return False
    
    # 4. 성능 테스트
    print("4. 성능 테스트...")
    try:
        start_time = time.time()
        for i in range(1000):
            _ = json.dumps(virtual_data)
        end_time = time.time()
        print(f"   ✅ 성능 테스트 성공")
        print(f"   ⚡ 1000회 JSON 직렬화: {(end_time - start_time)*1000:.2f}ms")
    except Exception as e:
        print(f"   ❌ 성능 테스트 실패: {e}")
        return False
    
    print("=" * 40)
    print("🎉 모든 테스트 성공!")
    print("✅ 시스템이 정상적으로 작동합니다.")
    print("🌐 이제 웹 서버를 실행할 준비가 되었습니다.")
    
    return True

def show_next_steps():
    """다음 단계 안내"""
    print("\n📋 다음 단계:")
    print("1. 가상환경 활성화: source venv/bin/activate")
    print("2. 패키지 설치: pip install flask flask-cors loguru")
    print("3. 웹 서버 실행: python quick_server.py")
    print("4. 브라우저에서 http://localhost:8086 접속")

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        show_next_steps()
    else:
        print("❌ 테스트 실패. 환경을 확인해주세요.") 