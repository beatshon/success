"""
키움증권 API 설정 파일
"""

# 키움 API 설정
KIWOOM_CONFIG = {
    'app_key': 'YOUR_APP_KEY_HERE',  # 발급받은 앱키 입력
    'app_secret': 'YOUR_APP_SECRET_HERE',  # 발급받은 앱시크릿 입력
    'account_no': '',  # 모의투자 계좌번호 (로그인 후 자동으로 설정됨)
    'user_id': '',  # 사용자 ID (로그인 후 자동으로 설정됨)
}

# 거래 설정
TRADING_CONFIG = {
    'default_trade_amount': 100000,  # 기본 거래 금액 (10만원)
    'max_positions': 5,  # 최대 보유 종목 수
    'update_interval': 60,  # 업데이트 주기 (초)
    'enable_real_time': True,  # 실시간 데이터 사용 여부
}

# 로깅 설정
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/kiwoom_trading.log',
    'max_log_size': '10MB',
    'backup_count': 5,
}

# 전략 설정
STRATEGY_CONFIG = {
    'moving_average': {
        'short_period': 5,
        'long_period': 20,
    },
    'rsi': {
        'period': 14,
        'oversold': 30,
        'overbought': 70,
    },
    'bollinger_bands': {
        'period': 20,
        'std_dev': 2.0,
    }
}

# 모니터링 종목 (예시)
WATCH_STOCKS = [
    {'code': '005930', 'name': '삼성전자'},
    {'code': '000660', 'name': 'SK하이닉스'},
    {'code': '035420', 'name': 'NAVER'},
    {'code': '051910', 'name': 'LG화학'},
    {'code': '006400', 'name': '삼성SDI'},
]

# API 제한 설정
API_LIMITS = {
    'tr_request_limit': 4,  # TR 요청 제한 (초당)
    'real_data_limit': 100,  # 실시간 데이터 구독 제한
    'order_limit': 10,  # 주문 제한 (초당)
}

# 에러 코드 정의
ERROR_CODES = {
    -100: "사용자 정보교환실패",
    -101: "서버접속실패",
    -102: "버전처리실패",
    -103: "개인방화벽실패",
    -104: "메모리보호실패",
    -105: "함수입력값오류",
    -106: "통신연결종료",
    -200: "시세조회과부하",
    -201: "전문작성초기화실패",
    -202: "전문작성입력값오류",
    -203: "데이터없음",
    -204: "조회가능한종목수초과",
    -205: "데이터수신실패",
    -206: "조회가능한FID수초과",
    -207: "실시간해제오류",
    -209: "시세조회제한",
    -300: "입력값오류",
    -301: "계좌비밀번호없음",
    -302: "타인계좌사용불가",
    -303: "주문가격이주문착오금액기준초과",
    -304: "주문가격이주문착오금액기준초과",
    -305: "주문수량이총발행주수의1%초과오류",
    -306: "주문수량은총발행주수의3%초과오류",
}

def get_error_message(error_code):
    """에러 코드에 해당하는 메시지 반환"""
    return ERROR_CODES.get(error_code, f"알 수 없는 오류: {error_code}")

def validate_config():
    """설정 유효성 검사"""
    if KIWOOM_CONFIG['app_key'] == 'YOUR_APP_KEY_HERE':
        raise ValueError("API 앱키를 설정해주세요.")
    if KIWOOM_CONFIG['app_secret'] == 'YOUR_APP_SECRET_HERE':
        raise ValueError("API 앱시크릿을 설정해주세요.")
    return True 