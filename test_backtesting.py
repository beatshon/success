#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백테스팅 시스템 진단 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 백테스팅 시스템 모듈들
from backtesting_system import BacktestingEngine, BacktestConfig, BacktestMode
from real_stock_data_api import StockDataAPI, DataManager

def test_data_loading():
    """데이터 로딩 테스트"""
    logger.info("=== 데이터 로딩 테스트 ===")
    
    try:
        # API 테스트
        api = StockDataAPI(data_source="yahoo")
        
        # 단일 종목 테스트
        code = "005930"  # 삼성전자
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        logger.info(f"종목 {code} 데이터 로딩 테스트...")
        data = api.get_stock_data(code, start_date, end_date)
        
        if data:
            logger.info(f"데이터 로딩 성공: {len(data.data)}개 데이터")
            logger.info(f"최근 종가: {data.data['close'].iloc[-1]:,.0f}원")
            logger.info(f"데이터 범위: {data.data.index[0]} ~ {data.data.index[-1]}")
            
            # 데이터 샘플 출력
            print("\n데이터 샘플:")
            print(data.data.head())
            print("\n데이터 통계:")
            print(data.data.describe())
            
            return True
        else:
            logger.error("데이터 로딩 실패")
            return False
            
    except Exception as e:
        logger.error(f"데이터 로딩 테스트 오류: {e}")
        return False

def test_strategy_signals():
    """전략 신호 생성 테스트"""
    logger.info("\n=== 전략 신호 생성 테스트 ===")
    
    try:
        from trading_strategy import create_default_strategies
        
        # 전략 매니저 생성
        strategy_manager = create_default_strategies()
        
        # 더 많은 샘플 가격 데이터 생성 (최소 50개 이상)
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        prices = []
        
        # 삼성전자와 유사한 가격 패턴 생성 (더 많은 변동성)
        base_price = 70000
        current_price = base_price
        
        for i, date in enumerate(dates):
            if date.weekday() >= 5:  # 주말 제외
                continue
                
            # 더 큰 변동성을 가진 랜덤 워크 + 트렌드
            trend = 0.0002 * i  # 약간의 상승 트렌드
            noise = np.random.normal(0, 0.03)  # 3% 변동성
            change = trend + noise
            current_price *= (1 + change)
            
            # 가격이 너무 낮아지지 않도록 보정
            if current_price < base_price * 0.5:
                current_price = base_price * 0.5
            
            prices.append({
                'date': date,
                'price': current_price
            })
        
        price_df = pd.DataFrame(prices)
        price_df.set_index('date', inplace=True)
        
        logger.info(f"샘플 가격 데이터 생성: {len(price_df)}개")
        logger.info(f"가격 범위: {price_df['price'].min():.0f} ~ {price_df['price'].max():.0f}")
        
        # 전략에 가격 데이터 추가
        logger.info("전략에 가격 데이터 추가 중...")
        for strategy in strategy_manager.strategies.values():
            strategy.price_history = []  # 기존 데이터 초기화
            for date, row in price_df.iterrows():
                strategy.add_price_data(row['price'], date)
            
            logger.info(f"  {strategy.strategy_type.value}: {len(strategy.price_history)}개 데이터 추가")
        
        # 각 전략별로 개별 테스트
        logger.info("\n개별 전략 신호 생성 테스트:")
        for name, strategy in strategy_manager.strategies.items():
            logger.info(f"\n{name} 전략 테스트:")
            logger.info(f"  데이터 수: {len(strategy.price_history)}")
            
            if len(strategy.price_history) > 0:
                logger.info(f"  최근 가격: {strategy.price_history[-1]['price']:.0f}")
                
                # 개별 신호 생성
                signal = strategy.generate_signal()
                if signal:
                    logger.info(f"  ✅ 신호 생성: {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")
                else:
                    logger.info(f"  ❌ 신호 없음")
            else:
                logger.info(f"  ❌ 데이터 없음")
        
        # 전체 신호 생성
        logger.info("\n전체 신호 생성 테스트:")
        signals = strategy_manager.generate_signals()
        
        logger.info(f"생성된 신호 수: {len(signals)}")
        
        if len(signals) > 0:
            for i, signal in enumerate(signals[:5]):  # 처음 5개 신호만 출력
                logger.info(f"신호 {i+1}: {signal.signal_type.value} - {signal.timestamp}")
            
            return True
        else:
            logger.warning("신호가 생성되지 않았습니다. 전략 파라미터를 확인해주세요.")
            
            # 디버깅을 위한 추가 정보
            logger.info("\n디버깅 정보:")
            for name, strategy in strategy_manager.strategies.items():
                if hasattr(strategy, 'short_period'):
                    logger.info(f"  {name} - short_period: {strategy.short_period}, long_period: {strategy.long_period}")
                if hasattr(strategy, 'rsi_period'):
                    logger.info(f"  {name} - rsi_period: {strategy.rsi_period}")
            
            return False
        
    except Exception as e:
        logger.error(f"전략 신호 테스트 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_simple_backtest():
    """간단한 백테스트 테스트"""
    logger.info("\n=== 간단한 백테스트 테스트 ===")
    
    try:
        # 백테스트 설정
        config = BacktestConfig(
            mode=BacktestMode.SINGLE_STOCK,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=10000000,
            max_positions=3,
            position_size_ratio=0.3
        )
        
        # 백테스팅 엔진 생성
        engine = BacktestingEngine(config)
        
        # 샘플 데이터 생성
        logger.info("샘플 데이터 생성...")
        engine._generate_sample_data()
        
        logger.info(f"생성된 데이터: {len(engine.data)}개 종목")
        for code, df in engine.data.items():
            logger.info(f"  {code}: {len(df)}개 데이터")
        
        # 백테스트 실행
        logger.info("백테스트 실행...")
        result = engine.run_backtest()
        
        if result:
            logger.info("백테스트 성공!")
            logger.info(f"총 거래 수: {result.total_trades}")
            logger.info(f"승률: {result.win_rate:.1f}%")
            logger.info(f"총 수익률: {result.total_return:.2%}")
            logger.info(f"샤프 비율: {result.sharpe_ratio:.2f}")
            
            return True
        else:
            logger.error("백테스트 실패")
            return False
            
    except Exception as e:
        logger.error(f"간단한 백테스트 테스트 오류: {e}")
        return False

def test_real_data_backtest():
    """실제 데이터 백테스트 테스트"""
    logger.info("\n=== 실제 데이터 백테스트 테스트 ===")
    
    try:
        # 백테스트 설정
        config = BacktestConfig(
            mode=BacktestMode.SINGLE_STOCK,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=10000000,
            max_positions=3,
            position_size_ratio=0.3
        )
        
        # 백테스팅 엔진 생성
        engine = BacktestingEngine(config)
        
        # 실제 데이터 로드
        codes = ['005930']  # 삼성전자만 테스트
        logger.info(f"실제 데이터 로드: {codes}")
        
        success = engine.load_data(codes=codes, data_source="yahoo")
        
        if success:
            logger.info("실제 데이터 로드 성공")
            logger.info(f"데이터 종목 수: {len(engine.data)}")
            
            # 백테스트 실행
            result = engine.run_backtest()
            
            if result:
                logger.info("실제 데이터 백테스트 성공!")
                logger.info(f"총 거래 수: {result.total_trades}")
                logger.info(f"승률: {result.win_rate:.1f}%")
                logger.info(f"총 수익률: {result.total_return:.2%}")
                
                return True
            else:
                logger.error("실제 데이터 백테스트 실패")
                return False
        else:
            logger.warning("실제 데이터 로드 실패, 샘플 데이터로 테스트")
            return test_simple_backtest()
            
    except Exception as e:
        logger.error(f"실제 데이터 백테스트 테스트 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("백테스팅 시스템 진단 테스트 시작")
    
    # 테스트 실행
    tests = [
        ("데이터 로딩", test_data_loading),
        ("전략 신호 생성", test_strategy_signals),
        ("간단한 백테스트", test_simple_backtest),
        ("실제 데이터 백테스트", test_real_data_backtest)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"{test_name} 테스트 시작")
            logger.info(f"{'='*50}")
            
            success = test_func()
            results[test_name] = success
            
            if success:
                logger.info(f"✅ {test_name} 테스트 성공")
            else:
                logger.error(f"❌ {test_name} 테스트 실패")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 테스트 오류: {e}")
            results[test_name] = False
    
    # 결과 요약
    logger.info(f"\n{'='*50}")
    logger.info("테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    logger.info(f"\n전체 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        logger.info("🎉 모든 테스트 통과!")
    else:
        logger.warning("⚠️ 일부 테스트 실패. 문제를 확인해주세요.")

if __name__ == "__main__":
    main() 