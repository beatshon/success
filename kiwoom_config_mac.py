# 키움 자동 주문 설정 파일 (Mac 버전)

# 계좌 정보 (실제 정보로 수정 필요)
ACCOUNT_NO = "YOUR_ACCOUNT_NUMBER"  # 실제 계좌번호
ACCOUNT_PW = "YOUR_ACCOUNT_PASSWORD"  # 실제 계좌비밀번호

# 주문 설정
STOCK_CODE = "005930"      # 삼성전자
ORDER_QTY = 1              # 주문 수량
ORDER_PRICE = 70000        # 주문 가격 (지정가)
ORDER_TYPE = "00"          # 주문 구분 (00: 지정가, 03: 시장가)

# 팝업 감지 설정
POPUP_CHECK_INTERVAL = 2   # 팝업 감지 간격 (초)
LOGIN_WAIT_TIME = 5        # 로그인 대기 시간 (초)

# 로깅 설정
LOG_LEVEL = "INFO"         # 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
LOG_FILE = "logs/kiwoom_auto_order.log"

# Mac 환경 설정
IS_MAC = True
WINDOWS_SERVER_URL = "http://localhost:8080"  # Windows 서버 URL

# 주문 파라미터 설명
ORDER_PARAMS = {
    "rQName": "매수주문",      # 사용자 구분명
    "ScreenNo": "0101",       # 화면번호
    "AccNo": ACCOUNT_NO,      # 계좌번호
    "OrderType": 1,           # 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소)
    "Code": STOCK_CODE,       # 종목코드
    "Qty": ORDER_QTY,         # 주문수량
    "Price": ORDER_PRICE,     # 주문가격
    "HogaGb": ORDER_TYPE,     # 거래구분
    "OrderNo": ""             # 원주문번호
}

# 에러 코드 설명
ERROR_CODES = {
    -10: "실패",
    -100: "사용자정보교환실패",
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
    -306: "주문수량은총발행주수의3%초과오류"
}

def get_error_message(error_code):
    """에러 코드에 대한 설명을 반환"""
    return ERROR_CODES.get(error_code, f"알 수 없는 에러 코드: {error_code}")

def validate_config():
    """설정값 유효성 검사"""
    errors = []
    
    if not ACCOUNT_NO or ACCOUNT_NO == "YOUR_ACCOUNT_NUMBER":
        errors.append("계좌번호를 설정해주세요.")
    
    if not ACCOUNT_PW or ACCOUNT_PW == "YOUR_ACCOUNT_PASSWORD":
        errors.append("계좌비밀번호를 설정해주세요.")
    
    if not STOCK_CODE or len(STOCK_CODE) != 6:
        errors.append("종목코드가 올바르지 않습니다.")
    
    if ORDER_QTY <= 0:
        errors.append("주문수량은 0보다 커야 합니다.")
    
    if ORDER_PRICE <= 0:
        errors.append("주문가격은 0보다 커야 합니다.")
    
    return errors 