import numpy as np
import pandas as pd
import requests
import json
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
from scipy.optimize import minimize
from scipy.stats import norm, skew, kurtosis
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """뉴스 및 소셜 미디어 감정 분석"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
    def analyze_text_sentiment(self, text: str) -> Dict:
        """텍스트 감정 분석"""
        # VADER 감정 분석
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # TextBlob 감정 분석
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # 종합 감정 점수
        combined_score = (vader_scores['compound'] + textblob_polarity) / 2
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity,
            'combined_score': combined_score,
            'sentiment': self._classify_sentiment(combined_score)
        }
    
    def _classify_sentiment(self, score: float) -> str:
        """감정 분류"""
        if score >= 0.1:
            return 'POSITIVE'
        elif score <= -0.1:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def analyze_news_sentiment(self, news_data: List[Dict]) -> Dict:
        """뉴스 데이터 감정 분석"""
        sentiments = []
        
        for news in news_data:
            title_sentiment = self.analyze_text_sentiment(news.get('title', ''))
            content_sentiment = self.analyze_text_sentiment(news.get('content', ''))
            
            # 가중 평균 (제목에 더 높은 가중치)
            weighted_score = (title_sentiment['combined_score'] * 0.7 + 
                            content_sentiment['combined_score'] * 0.3)
            
            sentiments.append({
                'news_id': news.get('id'),
                'title_sentiment': title_sentiment,
                'content_sentiment': content_sentiment,
                'weighted_score': weighted_score,
                'timestamp': news.get('timestamp')
            })
        
        # 전체 감정 요약
        if sentiments:
            avg_score = np.mean([s['weighted_score'] for s in sentiments])
            positive_count = sum(1 for s in sentiments if s['weighted_score'] > 0.1)
            negative_count = sum(1 for s in sentiments if s['weighted_score'] < -0.1)
            neutral_count = len(sentiments) - positive_count - negative_count
            
            return {
                'overall_sentiment': self._classify_sentiment(avg_score),
                'average_score': avg_score,
                'positive_ratio': positive_count / len(sentiments),
                'negative_ratio': negative_count / len(sentiments),
                'neutral_ratio': neutral_count / len(sentiments),
                'total_news': len(sentiments),
                'detailed_sentiments': sentiments
            }
        
        return {}

class MarketPsychologyAnalyzer:
    """시장 심리 분석"""
    
    def __init__(self):
        self.fear_greed_indicators = {}
        
    def calculate_fear_greed_index(self, market_data: pd.DataFrame) -> Dict:
        """공포/탐욕 지수 계산"""
        indicators = {}
        
        # 변동성 지수 (VIX 대용)
        returns = market_data['close'].pct_change()
        volatility = returns.rolling(window=20).std() * np.sqrt(252)
        indicators['volatility'] = volatility.iloc[-1]
        
        # 모멘텀 지수
        momentum = (market_data['close'].iloc[-1] / market_data['close'].iloc[-25] - 1) * 100
        indicators['momentum'] = momentum
        
        # 거래량 지수
        volume_ma = market_data['volume'].rolling(window=20).mean()
        volume_ratio = market_data['volume'].iloc[-1] / volume_ma.iloc[-1]
        indicators['volume'] = volume_ratio
        
        # RSI 지수
        delta = market_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = rsi.iloc[-1]
        
        # 종합 공포/탐욕 지수 계산
        fear_greed_score = self._calculate_composite_score(indicators)
        
        return {
            'fear_greed_score': fear_greed_score,
            'sentiment': self._classify_market_sentiment(fear_greed_score),
            'indicators': indicators
        }
    
    def _calculate_composite_score(self, indicators: Dict) -> float:
        """종합 점수 계산"""
        # 각 지표를 0-100 스케일로 정규화
        volatility_score = max(0, min(100, (1 - indicators['volatility']) * 100))
        momentum_score = max(0, min(100, (indicators['momentum'] + 20) * 2.5))
        volume_score = max(0, min(100, indicators['volume'] * 50))
        rsi_score = indicators['rsi']
        
        # 가중 평균
        composite_score = (
            volatility_score * 0.25 +
            momentum_score * 0.25 +
            volume_score * 0.25 +
            rsi_score * 0.25
        )
        
        return composite_score
    
    def _classify_market_sentiment(self, score: float) -> str:
        """시장 심리 분류"""
        if score >= 80:
            return 'EXTREME_GREED'
        elif score >= 60:
            return 'GREED'
        elif score >= 40:
            return 'NEUTRAL'
        elif score >= 20:
            return 'FEAR'
        else:
            return 'EXTREME_FEAR'
    
    def analyze_market_regime(self, market_data: pd.DataFrame) -> Dict:
        """시장 체제 분석"""
        returns = market_data['close'].pct_change().dropna()
        
        # 통계적 특성
        mean_return = returns.mean()
        volatility = returns.std()
        skewness = skew(returns)
        kurtosis_val = kurtosis(returns)
        
        # VaR 계산
        var_95 = norm.ppf(0.05, mean_return, volatility)
        var_99 = norm.ppf(0.01, mean_return, volatility)
        
        # 시장 체제 분류
        if volatility > returns.rolling(window=252).std().mean() * 1.5:
            regime = 'HIGH_VOLATILITY'
        elif volatility < returns.rolling(window=252).std().mean() * 0.5:
            regime = 'LOW_VOLATILITY'
        else:
            regime = 'NORMAL_VOLATILITY'
        
        return {
            'regime': regime,
            'mean_return': mean_return,
            'volatility': volatility,
            'skewness': skewness,
            'kurtosis': kurtosis_val,
            'var_95': var_95,
            'var_99': var_99,
            'sharpe_ratio': mean_return / volatility if volatility > 0 else 0
        }

class PortfolioOptimizer:
    """포트폴리오 최적화"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        
    def calculate_portfolio_metrics(self, returns: pd.DataFrame, weights: np.ndarray) -> Dict:
        """포트폴리오 지표 계산"""
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio
        }
    
    def optimize_portfolio(self, returns: pd.DataFrame, method: str = 'sharpe', 
                          constraints: Dict = None) -> Dict:
        """포트폴리오 최적화"""
        n_assets = len(returns.columns)
        
        # 기본 제약조건
        if constraints is None:
            constraints = {
                'min_weight': 0.0,
                'max_weight': 1.0,
                'target_return': None
            }
        
        # 목적 함수 정의
        def objective(weights):
            if method == 'sharpe':
                portfolio_return = np.sum(returns.mean() * weights) * 252
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
                return -((portfolio_return - self.risk_free_rate) / portfolio_volatility)
            elif method == 'min_variance':
                return np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
            else:
                return np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        
        # 제약조건 설정
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 가중치 합 = 1
        ]
        
        if constraints.get('target_return'):
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.sum(returns.mean() * x) * 252 - constraints['target_return']
            })
        
        # 경계 조건
        bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
        
        # 최적화 실행
        initial_weights = np.array([1/n_assets] * n_assets)
        result = minimize(objective, initial_weights, method='SLSQP',
                         bounds=bounds, constraints=constraints_list)
        
        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(returns, optimal_weights)
            
            return {
                'weights': optimal_weights,
                'assets': returns.columns.tolist(),
                'metrics': metrics,
                'optimization_success': True
            }
        else:
            return {
                'optimization_success': False,
                'error': result.message
            }
    
    def efficient_frontier(self, returns: pd.DataFrame, n_portfolios: int = 100) -> pd.DataFrame:
        """효율적 프론티어 생성"""
        n_assets = len(returns.columns)
        
        # 목표 수익률 범위
        min_return = returns.mean().min() * 252
        max_return = returns.mean().max() * 252
        target_returns = np.linspace(min_return, max_return, n_portfolios)
        
        efficient_portfolios = []
        
        for target_return in target_returns:
            result = self.optimize_portfolio(
                returns, 
                method='min_variance',
                constraints={'target_return': target_return, 'min_weight': 0.0, 'max_weight': 1.0}
            )
            
            if result['optimization_success']:
                efficient_portfolios.append({
                    'target_return': target_return,
                    'actual_return': result['metrics']['return'],
                    'volatility': result['metrics']['volatility'],
                    'sharpe_ratio': result['metrics']['sharpe_ratio'],
                    'weights': result['weights']
                })
        
        return pd.DataFrame(efficient_portfolios)

class RiskManager:
    """리스크 관리 시스템"""
    
    def __init__(self, max_position_size: float = 0.1, max_portfolio_risk: float = 0.02):
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        
    def calculate_position_size(self, price: float, stop_loss: float, 
                               account_value: float) -> int:
        """포지션 크기 계산"""
        risk_per_share = abs(price - stop_loss)
        max_risk_amount = account_value * self.max_portfolio_risk
        position_size = int(max_risk_amount / risk_per_share)
        
        # 최대 포지션 크기 제한
        max_shares = int(account_value * self.max_position_size / price)
        position_size = min(position_size, max_shares)
        
        return position_size
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Value at Risk 계산"""
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def calculate_expected_shortfall(self, returns: pd.Series, 
                                   confidence_level: float = 0.95) -> float:
        """Expected Shortfall (Conditional VaR) 계산"""
        var = self.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def stress_test_portfolio(self, portfolio: Dict, 
                            stress_scenarios: List[Dict]) -> Dict:
        """포트폴리오 스트레스 테스트"""
        results = {}
        
        for scenario in stress_scenarios:
            scenario_name = scenario['name']
            price_changes = scenario['price_changes']
            
            # 시나리오별 손실 계산
            total_loss = 0
            for asset, change in price_changes.items():
                if asset in portfolio:
                    position_value = portfolio[asset]['quantity'] * portfolio[asset]['price']
                    loss = position_value * change
                    total_loss += loss
            
            results[scenario_name] = {
                'total_loss': total_loss,
                'loss_percentage': total_loss / sum(pos['quantity'] * pos['price'] 
                                                  for pos in portfolio.values())
            }
        
        return results
    
    def generate_risk_report(self, portfolio: Dict, market_data: pd.DataFrame) -> Dict:
        """리스크 리포트 생성"""
        # 포트폴리오 수익률 계산
        portfolio_returns = []
        for asset, position in portfolio.items():
            if asset in market_data.columns:
                asset_returns = market_data[asset].pct_change().dropna()
                weighted_returns = asset_returns * (position['quantity'] * position['price'] / 
                                                  sum(pos['quantity'] * pos['price'] 
                                                      for pos in portfolio.values()))
                portfolio_returns.append(weighted_returns)
        
        if portfolio_returns:
            portfolio_returns = pd.concat(portfolio_returns, axis=1).sum(axis=1)
            
            # 리스크 지표 계산
            var_95 = self.calculate_var(portfolio_returns, 0.95)
            var_99 = self.calculate_var(portfolio_returns, 0.99)
            es_95 = self.expected_shortfall(portfolio_returns, 0.95)
            
            return {
                'portfolio_value': sum(pos['quantity'] * pos['price'] for pos in portfolio.values()),
                'var_95': var_95,
                'var_99': var_99,
                'expected_shortfall_95': es_95,
                'volatility': portfolio_returns.std() * np.sqrt(252),
                'max_drawdown': self.calculate_max_drawdown(portfolio_returns),
                'sharpe_ratio': portfolio_returns.mean() / portfolio_returns.std() if portfolio_returns.std() > 0 else 0
            }
        
        return {}
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

class AdvancedAnalyticsSystem:
    """고급 분석 시스템 통합 클래스"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.market_psychology = MarketPsychologyAnalyzer()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_manager = RiskManager()
        
    def comprehensive_analysis(self, market_data: pd.DataFrame, 
                             news_data: List[Dict] = None,
                             portfolio: Dict = None) -> Dict:
        """종합 분석 수행"""
        analysis_results = {}
        
        # 시장 심리 분석
        fear_greed = self.market_psychology.calculate_fear_greed_index(market_data)
        market_regime = self.market_psychology.analyze_market_regime(market_data)
        
        analysis_results['market_psychology'] = {
            'fear_greed': fear_greed,
            'market_regime': market_regime
        }
        
        # 뉴스 감정 분석
        if news_data:
            sentiment_analysis = self.sentiment_analyzer.analyze_news_sentiment(news_data)
            analysis_results['sentiment_analysis'] = sentiment_analysis
        
        # 포트폴리오 분석
        if portfolio and len(market_data.columns) > 1:
            returns = market_data.pct_change().dropna()
            
            # 포트폴리오 최적화
            optimal_portfolio = self.portfolio_optimizer.optimize_portfolio(returns)
            efficient_frontier = self.portfolio_optimizer.efficient_frontier(returns)
            
            # 리스크 분석
            risk_report = self.risk_manager.generate_risk_report(portfolio, market_data)
            
            analysis_results['portfolio_analysis'] = {
                'optimal_portfolio': optimal_portfolio,
                'efficient_frontier': efficient_frontier.to_dict('records'),
                'risk_report': risk_report
            }
        
        return analysis_results
    
    def generate_trading_signals(self, analysis_results: Dict) -> Dict:
        """트레이딩 신호 생성"""
        signals = {}
        
        # 시장 심리 기반 신호
        fear_greed = analysis_results.get('market_psychology', {}).get('fear_greed', {})
        if fear_greed:
            score = fear_greed.get('fear_greed_score', 50)
            if score < 20:
                signals['market_sentiment'] = 'BUY'  # 극도의 공포
            elif score > 80:
                signals['market_sentiment'] = 'SELL'  # 극도의 탐욕
            else:
                signals['market_sentiment'] = 'HOLD'
        
        # 감정 분석 기반 신호
        sentiment = analysis_results.get('sentiment_analysis', {})
        if sentiment:
            avg_score = sentiment.get('average_score', 0)
            if avg_score > 0.2:
                signals['news_sentiment'] = 'BUY'
            elif avg_score < -0.2:
                signals['news_sentiment'] = 'SELL'
            else:
                signals['news_sentiment'] = 'HOLD'
        
        # 종합 신호
        buy_signals = sum(1 for signal in signals.values() if signal == 'BUY')
        sell_signals = sum(1 for signal in signals.values() if signal == 'SELL')
        
        if buy_signals > sell_signals:
            signals['composite_signal'] = 'BUY'
        elif sell_signals > buy_signals:
            signals['composite_signal'] = 'SELL'
        else:
            signals['composite_signal'] = 'HOLD'
        
        return signals

def create_sample_analysis_data():
    """샘플 분석 데이터 생성"""
    # 샘플 시장 데이터
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    np.random.seed(42)
    
    market_data = pd.DataFrame({
        'AAPL': np.random.normal(0.001, 0.02, 252).cumsum() + 150,
        'GOOGL': np.random.normal(0.001, 0.025, 252).cumsum() + 2500,
        'MSFT': np.random.normal(0.001, 0.018, 252).cumsum() + 300,
        'TSLA': np.random.normal(0.002, 0.04, 252).cumsum() + 200,
        'volume': np.random.randint(1000000, 10000000, 252)
    }, index=dates)
    
    # 샘플 뉴스 데이터
    news_data = [
        {
            'id': 1,
            'title': 'Apple reports strong quarterly earnings',
            'content': 'Apple Inc. reported better-than-expected quarterly results...',
            'timestamp': '2023-12-01T10:00:00Z'
        },
        {
            'id': 2,
            'title': 'Market volatility increases due to economic uncertainty',
            'content': 'Investors are concerned about inflation and interest rates...',
            'timestamp': '2023-12-01T11:00:00Z'
        }
    ]
    
    # 샘플 포트폴리오
    portfolio = {
        'AAPL': {'quantity': 100, 'price': 150},
        'GOOGL': {'quantity': 50, 'price': 2500},
        'MSFT': {'quantity': 75, 'price': 300}
    }
    
    return market_data, news_data, portfolio

if __name__ == "__main__":
    # 샘플 데이터 생성
    market_data, news_data, portfolio = create_sample_analysis_data()
    print("샘플 데이터 생성 완료")
    
    # 고급 분석 시스템 초기화
    analytics_system = AdvancedAnalyticsSystem()
    
    # 종합 분석 수행
    print("\n=== 종합 분석 수행 ===")
    analysis_results = analytics_system.comprehensive_analysis(
        market_data, news_data, portfolio
    )
    
    # 분석 결과 출력
    print("\n시장 심리 분석:")
    fear_greed = analysis_results['market_psychology']['fear_greed']
    print(f"  공포/탐욕 지수: {fear_greed['fear_greed_score']:.2f}")
    print(f"  시장 심리: {fear_greed['sentiment']}")
    
    print("\n감정 분석:")
    sentiment = analysis_results['sentiment_analysis']
    print(f"  평균 감정 점수: {sentiment['average_score']:.3f}")
    print(f"  전체 감정: {sentiment['overall_sentiment']}")
    
    print("\n포트폴리오 분석:")
    portfolio_analysis = analysis_results['portfolio_analysis']
    risk_report = portfolio_analysis['risk_report']
    print(f"  포트폴리오 가치: ${risk_report['portfolio_value']:,.2f}")
    print(f"  VaR (95%): {risk_report['var_95']:.2%}")
    print(f"  변동성: {risk_report['volatility']:.2%}")
    
    # 트레이딩 신호 생성
    print("\n=== 트레이딩 신호 생성 ===")
    signals = analytics_system.generate_trading_signals(analysis_results)
    
    print("생성된 신호:")
    for signal_type, signal in signals.items():
        print(f"  {signal_type}: {signal}")
    
    print("\n고급 분석 시스템 테스트 완료!") 