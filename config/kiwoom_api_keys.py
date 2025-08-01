"""
키움 API 앱키 설정
실제 발급받은 앱키를 입력하세요.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class KiwoomAPIKeys:
    """키움 API 앱키 설정 클래스"""
    
    def __init__(self):
        # API 앱키 (환경 변수에서 로드)
        self.APP_KEY = os.getenv('KIWOOM_APP_KEY', '')
        self.APP_SECRET = os.getenv('KIWOOM_APP_SECRET', '')
        self.ACCESS_TOKEN = os.getenv('KIWOOM_ACCESS_TOKEN', '')
        
        # API 버전 및 설정
        self.API_VERSION = "1.0"
        self.API_BASE_URL = "https://openapi.kiwoom.com"
        
        # 앱키 상태
        self.is_configured = self._check_configuration()
    
    def _check_configuration(self):
        """앱키 설정 상태 확인"""
        if not self.APP_KEY:
            print("⚠️  KIWOOM_APP_KEY가 설정되지 않았습니다.")
            return False
        
        if not self.APP_SECRET:
            print("⚠️  KIWOOM_APP_SECRET이 설정되지 않았습니다.")
            return False
        
        print("✅ 키움 API 앱키 설정 완료")
        return True
    
    def get_app_key(self):
        """앱키 반환"""
        return self.APP_KEY
    
    def get_app_secret(self):
        """앱 시크릿 반환"""
        return self.APP_SECRET
    
    def get_access_token(self):
        """액세스 토큰 반환"""
        return self.ACCESS_TOKEN
    
    def set_access_token(self, token):
        """액세스 토큰 설정"""
        self.ACCESS_TOKEN = token
        # 환경 변수 업데이트
        os.environ['KIWOOM_ACCESS_TOKEN'] = token
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        if not self.ACCESS_TOKEN:
            return {}
        
        return {
            'Authorization': f'Bearer {self.ACCESS_TOKEN}',
            'appKey': self.APP_KEY,
            'appSecret': self.APP_SECRET,
            'Content-Type': 'application/json'
        }
    
    def is_ready(self):
        """API 사용 준비 상태 확인"""
        return self.is_configured and bool(self.ACCESS_TOKEN)

# 전역 앱키 인스턴스
kiwoom_api_keys = KiwoomAPIKeys() 