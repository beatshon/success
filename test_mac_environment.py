#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
맥 전용 테스트 스크립트
모든 기능을 맥에서 테스트
"""

import requests
import json
import time
from datetime import datetime
from loguru import logger

def test_mac_server():
    """맥 서버 테스트"""
    base_url = "http://localhost:8081"
    
    logger.info("맥 전용 서버 테스트 시작")
    
    try:
        # 1. 서버 상태 확인
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            status = response.json()
            logger.info(f"✓ 서버 상태: {status}")
        else:
            logger.error("✗ 서버 상태 확인 실패")
            return False
        
        # 2. 가상 데이터 시작
        response = requests.post(f"{base_url}/api/start-virtual-data")
        if response.status_code == 200:
            logger.info("✓ 가상 데이터 시작 성공")
        else:
            logger.error("✗ 가상 데이터 시작 실패")
        
        # 3. 주식 데이터 확인
        response = requests.get(f"{base_url}/api/stock-data")
        if response.status_code == 200:
            stock_data = response.json()
            logger.info(f"✓ 주식 데이터: {len(stock_data)}개 종목")
        else:
            logger.error("✗ 주식 데이터 조회 실패")
        
        # 4. 포트폴리오 데이터 확인
        response = requests.get(f"{base_url}/api/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            logger.info(f"✓ 포트폴리오: 총 자산 {portfolio['total_value']:,}원")
        else:
            logger.error("✗ 포트폴리오 데이터 조회 실패")
        
        # 5. 투자 신호 확인
        response = requests.get(f"{base_url}/api/signals")
        if response.status_code == 200:
            signals = response.json()
            logger.info(f"✓ 투자 신호: {len(signals)}개")
        else:
            logger.error("✗ 투자 신호 조회 실패")
        
        # 6. 뉴스 데이터 확인
        response = requests.get(f"{base_url}/api/news")
        if response.status_code == 200:
            news = response.json()
            logger.info(f"✓ 뉴스 데이터: {len(news)}개")
        else:
            logger.error("✗ 뉴스 데이터 조회 실패")
        
        logger.info("맥 전용 서버 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        return False

def test_data_generation():
    """데이터 생성 테스트"""
    logger.info("데이터 생성 테스트 시작")
    
    # 가상 데이터 생성 테스트
    import random
    import pandas as pd
    
    # 주식 데이터 생성
    stock_codes = ["005930", "000660", "035420", "051910", "006400"]
    data = {}
    
    for code in stock_codes:
        prices = []
        for i in range(100):
            if i == 0:
                price = random.uniform(50000, 200000)
            else:
                change = random.uniform(-0.02, 0.02)
                price = prices[-1] * (1 + change)
            prices.append(price)
        
        data[code] = prices
    
    df = pd.DataFrame(data)
    logger.info(f"✓ 가상 주가 데이터 생성: {df.shape}")
    
    # 포트폴리오 데이터 생성
    portfolio = {
        "total_value": 10000000,
        "positions": []
    }
    
    for code in stock_codes[:3]:
        position = {
            "code": code,
            "quantity": random.randint(1, 10),
            "avg_price": random.uniform(50000, 200000),
            "current_price": random.uniform(50000, 200000)
        }
        position["profit"] = (position["current_price"] - position["avg_price"]) * position["quantity"]
        portfolio["positions"].append(position)
    
    portfolio["total_profit"] = sum(pos["profit"] for pos in portfolio["positions"])
    portfolio["profit_rate"] = portfolio["total_profit"] / portfolio["total_value"]
    
    logger.info(f"✓ 포트폴리오 데이터 생성: 수익률 {portfolio['profit_rate']:.2%}")
    
    return True

if __name__ == "__main__":
    logger.info("맥 전용 테스트 시작")
    
    # 데이터 생성 테스트
    test_data_generation()
    
    # 서버 테스트 (서버가 실행 중일 때)
    try:
        test_mac_server()
    except requests.exceptions.ConnectionError:
        logger.warning("서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요.")
        logger.info("서버 시작 명령어: python mac_real_time_server.py")
    
    logger.info("맥 전용 테스트 완료")
