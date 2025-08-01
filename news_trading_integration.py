#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스 분석 기반 주식 거래 통합 시스템
네이버 뉴스 분석 결과를 키움 API와 연동하여 자동 거래를 수행하는 시스템
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import pandas as pd

# 로컬 모듈 임포트
from news_collector import NaverNewsCollector, NewsItem
from stock_news_analyzer import StockNewsAnalyzer, StockAnalysis
from kiwoom_api import KiwoomAPI

@dataclass
class TradingSignal:
    """거래 신호 데이터 클래스"""
    stock_code: str
    stock_name: str
    signal_type: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 ~ 1.0
    reason: str
    target_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

class NewsTradingIntegration:
    """뉴스 분석 기반 주식 거래 통합 시스템"""
    
    def __init__(self, config_file: str = "config/news_trading_config.json"):
        """
        통합 시스템 초기화
        
        Args:
            config_file: 설정 파일 경로
        """
        self.config = self._load_config(config_file)
        self.news_collector = None
        self.news_analyzer = StockNewsAnalyzer()
        self.kiwoom_api = None
        
        # 로그 설정
        self._setup_logging()
        
        logger.info("뉴스 거래 통합 시스템 초기화 완료")
    
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
                    "kiwoom_api": {
                        "auto_login": True,
                        "real_data": True,
                        "order_confirm": True
                    },
                    "trading": {
                        "enabled": False,
                        "max_position_per_stock": 1000000,  # 100만원
                        "max_total_position": 5000000,      # 500만원
                        "min_confidence": 0.7,
                        "stop_loss_ratio": 0.05,           # 5%
                        "take_profit_ratio": 0.15,         # 15%
                        "max_holdings": 5
                    },
                    "analysis": {
                        "keywords": [
                            "주식", "증시", "코스피", "코스닥", "투자",
                            "삼성전자", "SK하이닉스", "네이버", "카카오",
                            "LG화학", "현대자동차", "기아", "포스코"
                        ],
                        "min_news_count": 3,
                        "sentiment_threshold": 0.3
                    },
                    "scheduling": {
                        "auto_run": False,
                        "run_times": ["09:00", "12:00", "15:00"],
                        "run_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    }
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
        log_file = f"{log_dir}/news_trading_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 기존 핸들러 제거
        logger.remove()
        
        # 콘솔 출력
        logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        
        # 파일 출력
        logger.add(log_file, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", rotation="1 day", retention="30 days")
    
    def initialize_components(self):
        """컴포넌트 초기화"""
        try:
            # 뉴스 수집기 초기화
            client_id = self.config.get("naver_api", {}).get("client_id")
            client_secret = self.config.get("naver_api", {}).get("client_secret")
            
            if client_id == "your_naver_client_id" or client_secret == "your_naver_client_secret":
                logger.error("네이버 API 키가 설정되지 않았습니다.")
                logger.info("NAVER_API_SETUP_GUIDE.md 파일을 참고하여 API 키를 설정하세요.")
                return False
            
            self.news_collector = NaverNewsCollector(client_id, client_secret)
            logger.info("뉴스 수집기 초기화 완료")
            
            # 키움 API 초기화
            if self.config.get("trading", {}).get("enabled", False):
                self.kiwoom_api = KiwoomAPI()
                if not self.kiwoom_api.connect():
                    logger.error("키움 API 연결에 실패했습니다.")
                    return False
                logger.info("키움 API 초기화 완료")
            
            return True
            
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")
            return False
    
    def collect_and_analyze_news(self) -> Dict[str, StockAnalysis]:
        """뉴스 수집 및 분석"""
        try:
            keywords = self.config.get("analysis", {}).get("keywords", [])
            logger.info(f"뉴스 수집 시작 - 키워드: {len(keywords)}개")
            
            # 뉴스 수집
            news_items = self.news_collector.collect_daily_news(keywords)
            logger.info(f"뉴스 수집 완료 - {len(news_items)}개")
            
            # 뉴스 분석
            stock_analysis = self.news_analyzer.analyze_stock_news(news_items)
            logger.info(f"뉴스 분석 완료 - {len(stock_analysis)}개 종목")
            
            return stock_analysis
            
        except Exception as e:
            logger.error(f"뉴스 수집 및 분석 실패: {e}")
            return {}
    
    def generate_trading_signals(self, stock_analysis: Dict[str, StockAnalysis]) -> List[TradingSignal]:
        """거래 신호 생성"""
        signals = []
        trading_config = self.config.get("trading", {})
        min_confidence = trading_config.get("min_confidence", 0.7)
        min_news_count = self.config.get("analysis", {}).get("min_news_count", 3)
        
        for stock_code, analysis in stock_analysis.items():
            # 최소 뉴스 개수 확인
            if analysis.news_count < min_news_count:
                continue
            
            # 투자 점수 기반 신호 생성
            confidence = analysis.investment_score / 100.0
            
            if confidence >= min_confidence:
                if analysis.recommendation in ["강력 매수", "매수"]:
                    signal_type = "BUY"
                elif analysis.recommendation in ["매도"]:
                    signal_type = "SELL"
                else:
                    signal_type = "HOLD"
                
                # 현재가 조회 (키움 API 사용)
                current_price = 0.0
                if self.kiwoom_api:
                    current_price = self.kiwoom_api.get_current_price(stock_code)
                
                # 목표가 및 손절가 계산
                target_price = current_price * (1 + trading_config.get("take_profit_ratio", 0.15))
                stop_loss = current_price * (1 - trading_config.get("stop_loss_ratio", 0.05))
                
                signal = TradingSignal(
                    stock_code=stock_code,
                    stock_name=analysis.stock_name,
                    signal_type=signal_type,
                    confidence=confidence,
                    reason=f"뉴스 분석: {analysis.recommendation} (점수: {analysis.investment_score:.1f})",
                    target_price=target_price,
                    stop_loss=stop_loss,
                    take_profit=target_price
                )
                
                signals.append(signal)
        
        # 신뢰도 순으로 정렬
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"거래 신호 생성 완료 - {len(signals)}개")
        return signals
    
    def execute_trading_signals(self, signals: List[TradingSignal]) -> Dict[str, str]:
        """거래 신호 실행"""
        results = {}
        
        if not self.kiwoom_api:
            logger.warning("키움 API가 초기화되지 않아 거래를 건너뜁니다.")
            return results
        
        trading_config = self.config.get("trading", {})
        max_holdings = trading_config.get("max_holdings", 5)
        max_position_per_stock = trading_config.get("max_position_per_stock", 1000000)
        
        # 현재 보유 종목 확인
        holdings = self.kiwoom_api.get_holdings()
        current_holdings = len(holdings)
        
        for signal in signals:
            if current_holdings >= max_holdings:
                logger.info(f"최대 보유 종목 수({max_holdings})에 도달하여 추가 매수를 중단합니다.")
                break
            
            try:
                if signal.signal_type == "BUY":
                    # 매수 실행
                    result = self.kiwoom_api.buy_stock(
                        stock_code=signal.stock_code,
                        quantity=1,  # 1주씩 매수
                        price=0,     # 시장가
                        order_type="시장가매수"
                    )
                    
                    if result.get("success"):
                        results[signal.stock_code] = f"매수 성공: {signal.stock_name}"
                        current_holdings += 1
                        logger.info(f"매수 성공: {signal.stock_name} ({signal.stock_code})")
                    else:
                        results[signal.stock_code] = f"매수 실패: {result.get('message', '알 수 없는 오류')}"
                        logger.error(f"매수 실패: {signal.stock_name} - {result.get('message')}")
                
                elif signal.signal_type == "SELL":
                    # 보유 종목인지 확인
                    if signal.stock_code in holdings:
                        # 매도 실행
                        result = self.kiwoom_api.sell_stock(
                            stock_code=signal.stock_code,
                            quantity=holdings[signal.stock_code]["quantity"],
                            price=0,
                            order_type="시장가매도"
                        )
                        
                        if result.get("success"):
                            results[signal.stock_code] = f"매도 성공: {signal.stock_name}"
                            logger.info(f"매도 성공: {signal.stock_name} ({signal.stock_code})")
                        else:
                            results[signal.stock_code] = f"매도 실패: {result.get('message', '알 수 없는 오류')}"
                            logger.error(f"매도 실패: {signal.stock_name} - {result.get('message')}")
                
                # 거래 간격
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"거래 실행 중 오류: {signal.stock_code} - {e}")
                results[signal.stock_code] = f"거래 오류: {str(e)}"
        
        return results
    
    def save_trading_results(self, signals: List[TradingSignal], results: Dict[str, str]):
        """거래 결과 저장"""
        try:
            # 결과 디렉토리 생성
            output_dir = "data/trading_results"
            os.makedirs(output_dir, exist_ok=True)
            
            # 거래 신호 저장
            signals_data = []
            for signal in signals:
                signals_data.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "stock_code": signal.stock_code,
                    "stock_name": signal.stock_name,
                    "signal_type": signal.signal_type,
                    "confidence": signal.confidence,
                    "reason": signal.reason,
                    "target_price": signal.target_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "result": results.get(signal.stock_code, "미실행")
                })
            
            # CSV 파일로 저장
            df = pd.DataFrame(signals_data)
            filename = f"{output_dir}/trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"거래 결과 저장 완료: {filename}")
            
        except Exception as e:
            logger.error(f"거래 결과 저장 실패: {e}")
    
    def print_trading_summary(self, signals: List[TradingSignal], results: Dict[str, str]):
        """거래 요약 출력"""
        print("\n" + "="*60)
        print("📊 뉴스 기반 거래 신호 요약")
        print("="*60)
        
        if not signals:
            print("❌ 생성된 거래 신호가 없습니다.")
            return
        
        print(f"📈 총 거래 신호: {len(signals)}개")
        print(f"💰 거래 실행: {len([r for r in results.values() if '성공' in r])}개")
        print()
        
        for signal in signals[:10]:  # 상위 10개만 출력
            result = results.get(signal.stock_code, "미실행")
            status_icon = "✅" if "성공" in result else "❌" if "실패" in result else "⏳"
            
            print(f"{status_icon} {signal.stock_name} ({signal.stock_code})")
            print(f"   신호: {signal.signal_type} | 신뢰도: {signal.confidence:.1%}")
            print(f"   사유: {signal.reason}")
            print(f"   결과: {result}")
            print()
    
    def run_full_trading_cycle(self):
        """전체 거래 사이클 실행"""
        try:
            logger.info("뉴스 기반 거래 사이클 시작")
            
            # 1. 뉴스 수집 및 분석
            stock_analysis = self.collect_and_analyze_news()
            if not stock_analysis:
                logger.error("뉴스 분석 결과가 없어 거래를 중단합니다.")
                return
            
            # 2. 거래 신호 생성
            signals = self.generate_trading_signals(stock_analysis)
            if not signals:
                logger.info("생성된 거래 신호가 없습니다.")
                return
            
            # 3. 거래 실행 (설정이 활성화된 경우)
            results = {}
            if self.config.get("trading", {}).get("enabled", False):
                results = self.execute_trading_signals(signals)
            else:
                logger.info("거래 기능이 비활성화되어 있습니다. 신호만 생성합니다.")
                results = {signal.stock_code: "거래 비활성화" for signal in signals}
            
            # 4. 결과 저장
            self.save_trading_results(signals, results)
            
            # 5. 요약 출력
            self.print_trading_summary(signals, results)
            
            logger.info("뉴스 기반 거래 사이클 완료")
            
        except Exception as e:
            logger.error(f"거래 사이클 실행 중 오류: {e}")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="뉴스 기반 주식 거래 시스템")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    parser.add_argument("--enable-trading", action="store_true", help="실제 거래 활성화")
    parser.add_argument("--config", default="config/news_trading_config.json", help="설정 파일 경로")
    
    args = parser.parse_args()
    
    # 시스템 초기화
    system = NewsTradingIntegration(args.config)
    
    # 테스트 모드 설정
    if args.test:
        system.config["trading"]["enabled"] = False
        logger.info("테스트 모드로 실행합니다. 실제 거래는 수행되지 않습니다.")
    
    # 거래 활성화
    if args.enable_trading:
        system.config["trading"]["enabled"] = True
        logger.info("실제 거래가 활성화되었습니다.")
    
    # 컴포넌트 초기화
    if not system.initialize_components():
        logger.error("시스템 초기화에 실패했습니다.")
        return
    
    # 거래 사이클 실행
    system.run_full_trading_cycle()

if __name__ == "__main__":
    main() 