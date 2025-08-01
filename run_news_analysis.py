#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스 수집 및 분석 통합 실행 스크립트
네이버 뉴스를 수집하고 종목별 투자 분석을 수행하는 메인 프로그램
"""

import os
import sys
from datetime import datetime
from typing import List, Dict
import argparse
from loguru import logger
import json

# 로컬 모듈 임포트
from news_collector import NaverNewsCollector, NewsItem
from stock_news_analyzer import StockNewsAnalyzer, StockAnalysis

class NewsAnalysisSystem:
    """뉴스 수집 및 분석 통합 시스템"""
    
    def __init__(self, config_file: str = "config/news_config.json"):
        """
        시스템 초기화
        
        Args:
            config_file: 설정 파일 경로
        """
        self.config = self._load_config(config_file)
        self.collector = None
        self.analyzer = StockNewsAnalyzer()
        
        # 로그 설정
        self._setup_logging()
        
        logger.info("뉴스 분석 시스템 초기화 완료")
    
    def _load_config(self, config_file: str) -> Dict:
        """설정 파일 로드"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"설정 파일 로드 완료: {config_file}")
            else:
                # 기본 설정
                config = {
                    "naver_api": {
                        "client_id": "your_naver_client_id",
                        "client_secret": "your_naver_client_secret"
                    },
                    "keywords": [
                        "주식", "증시", "코스피", "코스닥", "투자",
                        "삼성전자", "SK하이닉스", "네이버", "카카오",
                        "LG화학", "현대자동차", "기아", "포스코",
                        "셀트리온", "카카오뱅크", "배터리", "반도체"
                    ],
                    "output_dir": "data/news_analysis",
                    "max_news_per_keyword": 50
                }
                
                # 설정 파일 생성
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"기본 설정 파일 생성: {config_file}")
            
            return config
            
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    def _setup_logging(self):
        """로깅 설정"""
        # 로그 디렉토리 생성
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일 설정
        log_file = f"{log_dir}/news_analysis_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 기존 핸들러 제거
        logger.remove()
        
        # 콘솔 출력
        logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        
        # 파일 출력
        logger.add(log_file, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", rotation="1 day", retention="30 days")
    
    def initialize_collector(self):
        """뉴스 수집기 초기화"""
        try:
            client_id = self.config.get("naver_api", {}).get("client_id")
            client_secret = self.config.get("naver_api", {}).get("client_secret")
            
            if client_id == "your_naver_client_id" or client_secret == "your_naver_client_secret":
                logger.error("네이버 API 키가 설정되지 않았습니다. config/news_config.json 파일을 수정해주세요.")
                return False
            
            self.collector = NaverNewsCollector(client_id, client_secret)
            logger.info("뉴스 수집기 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"뉴스 수집기 초기화 실패: {e}")
            return False
    
    def collect_news(self, keywords: List[str] = None) -> List[NewsItem]:
        """
        뉴스 수집
        
        Args:
            keywords: 검색할 키워드 리스트 (None이면 설정 파일의 키워드 사용)
            
        Returns:
            수집된 뉴스 아이템 리스트
        """
        if not self.collector:
            logger.error("뉴스 수집기가 초기화되지 않았습니다.")
            return []
        
        if keywords is None:
            keywords = self.config.get("keywords", [])
        
        logger.info(f"뉴스 수집 시작 - 키워드 {len(keywords)}개")
        
        try:
            news_items = self.collector.collect_daily_news(keywords)
            logger.info(f"뉴스 수집 완료 - {len(news_items)}개 수집")
            return news_items
            
        except Exception as e:
            logger.error(f"뉴스 수집 실패: {e}")
            return []
    
    def analyze_news(self, news_items: List[NewsItem]) -> Dict[str, StockAnalysis]:
        """
        뉴스 분석
        
        Args:
            news_items: 분석할 뉴스 아이템 리스트
            
        Returns:
            종목별 분석 결과
        """
        logger.info("뉴스 분석 시작")
        
        try:
            stock_analysis = self.analyzer.analyze_stock_news(news_items)
            logger.info(f"뉴스 분석 완료 - {len(stock_analysis)}개 종목 분석")
            return stock_analysis
            
        except Exception as e:
            logger.error(f"뉴스 분석 실패: {e}")
            return {}
    
    def save_results(self, news_items: List[NewsItem], 
                    stock_analysis: Dict[str, StockAnalysis]):
        """결과 저장"""
        try:
            # 출력 디렉토리 생성
            output_dir = self.config.get("output_dir", "data/news_analysis")
            os.makedirs(output_dir, exist_ok=True)
            
            today = datetime.now().strftime("%Y%m%d")
            
            # 뉴스 데이터 저장
            if self.collector and news_items:
                news_file = f"{output_dir}/news_{today}.csv"
                self.collector.save_news_to_csv(news_items, news_file)
            
            # 분석 결과 저장
            if stock_analysis:
                # CSV 저장
                analysis_file = f"{output_dir}/stock_analysis_{today}.csv"
                self.analyzer.save_analysis_to_csv(stock_analysis, analysis_file)
                
                # 리포트 생성
                report_file = f"{output_dir}/stock_analysis_report_{today}.txt"
                self.analyzer.generate_report(stock_analysis, report_file)
            
            logger.info(f"결과 저장 완료: {output_dir}")
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    def print_summary(self, news_items: List[NewsItem], 
                     stock_analysis: Dict[str, StockAnalysis]):
        """결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 뉴스 분석 결과 요약")
        print("="*60)
        
        print(f"📰 수집된 뉴스: {len(news_items)}개")
        print(f"📈 분석된 종목: {len(stock_analysis)}개")
        
        if stock_analysis:
            # 상위 종목
            top_stocks = self.analyzer.get_top_stocks(stock_analysis, 5)
            print(f"\n🏆 투자 점수 상위 5종목:")
            for i, stock in enumerate(top_stocks, 1):
                print(f"  {i}. {stock.stock_name} ({stock.stock_code}) - {stock.investment_score:.1f}점")
            
            # 위험 종목
            high_risk_stocks = self.analyzer.get_high_risk_stocks(stock_analysis)
            if high_risk_stocks:
                print(f"\n⚠️  위험도 높은 종목 ({len(high_risk_stocks)}개):")
                for stock in high_risk_stocks:
                    print(f"  • {stock.stock_name} ({stock.stock_code}) - {stock.recommendation}")
        
        print("\n" + "="*60)
    
    def run_full_analysis(self, keywords: List[str] = None):
        """전체 분석 실행"""
        logger.info("전체 뉴스 분석 시작")
        
        # 1단계: 뉴스 수집
        news_items = self.collect_news(keywords)
        if not news_items:
            logger.error("뉴스 수집에 실패했습니다.")
            return
        
        # 2단계: 뉴스 분석
        stock_analysis = self.analyze_news(news_items)
        if not stock_analysis:
            logger.error("뉴스 분석에 실패했습니다.")
            return
        
        # 3단계: 결과 저장
        self.save_results(news_items, stock_analysis)
        
        # 4단계: 요약 출력
        self.print_summary(news_items, stock_analysis)
        
        logger.info("전체 뉴스 분석 완료")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="뉴스 수집 및 분석 시스템")
    parser.add_argument("--config", default="config/news_config.json", 
                       help="설정 파일 경로")
    parser.add_argument("--keywords", nargs="+", 
                       help="검색할 키워드 리스트")
    parser.add_argument("--test", action="store_true", 
                       help="테스트 모드 실행")
    
    args = parser.parse_args()
    
    # 시스템 초기화
    system = NewsAnalysisSystem(args.config)
    
    if args.test:
        # 테스트 모드
        print("🧪 테스트 모드 실행")
        system.run_full_analysis(["삼성전자", "SK하이닉스"])
    else:
        # 실제 실행
        if not system.initialize_collector():
            print("❌ 네이버 API 키 설정이 필요합니다.")
            print("💡 config/news_config.json 파일에서 API 키를 설정해주세요.")
            return
        
        system.run_full_analysis(args.keywords)

if __name__ == "__main__":
    main() 