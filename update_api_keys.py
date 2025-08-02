#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 API 키 업데이트 스크립트
"""

import json
import os
from loguru import logger

def update_naver_api_keys():
    """네이버 API 키 업데이트"""
    print("🔑 네이버 API 키 설정")
    print("="*50)
    
    # 현재 설정 파일 확인
    config_file = "config/news_config.json"
    
    if not os.path.exists(config_file):
        print("❌ 설정 파일을 찾을 수 없습니다.")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("📝 네이버 개발자 센터에서 발급받은 API 키를 입력하세요.")
        print("   (https://developers.naver.com/ 에서 애플리케이션 등록 후 확인)")
        print()
        
        # API 키 입력
        client_id = input("Client ID를 입력하세요: ").strip()
        client_secret = input("Client Secret을 입력하세요: ").strip()
        
        if not client_id or not client_secret:
            print("❌ API 키가 입력되지 않았습니다.")
            return False
        
        # 설정 업데이트
        config["naver_api"]["client_id"] = client_id
        config["naver_api"]["client_secret"] = client_secret
        
        # 파일 저장
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ API 키가 성공적으로 업데이트되었습니다!")
        print(f"📁 설정 파일: {config_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ API 키 업데이트 중 오류가 발생했습니다: {e}")
        return False

def test_api_connection():
    """API 연결 테스트"""
    print("\n🧪 API 연결 테스트")
    print("="*50)
    
    try:
        from news_collector import NaverNewsCollector
        
        # 설정 파일에서 API 키 읽기
        with open("config/news_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        client_id = config["naver_api"]["client_id"]
        client_secret = config["naver_api"]["client_secret"]
        
        if client_id == "your_naver_client_id" or client_secret == "your_naver_client_secret":
            print("❌ API 키가 설정되지 않았습니다.")
            return False
        
        # 뉴스 수집기 초기화
        collector = NaverNewsCollector(client_id, client_secret)
        
        # 간단한 테스트 (삼성전자 키워드로 1개 뉴스만)
        print("📰 뉴스 수집 테스트 중...")
        news_items = collector.search_news("삼성전자", display=1)
        
        if news_items:
            print(f"✅ API 연결 성공! {len(news_items)}개 뉴스 수집됨")
            print(f"📰 첫 번째 뉴스: {news_items[0].title[:50]}...")
            return True
        else:
            print("❌ 뉴스를 수집할 수 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ API 연결 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 네이버 API 키 설정 및 테스트")
    print("="*60)
    
    # 1. API 키 업데이트
    if update_naver_api_keys():
        print("\n" + "="*60)
        
        # 2. API 연결 테스트
        if test_api_connection():
            print("\n🎉 모든 설정이 완료되었습니다!")
            print("이제 뉴스 분석 시스템을 사용할 수 있습니다.")
        else:
            print("\n⚠️ API 연결 테스트에 실패했습니다.")
            print("API 키를 다시 확인해주세요.")
    else:
        print("\n❌ API 키 설정에 실패했습니다.")

if __name__ == "__main__":
    main() 