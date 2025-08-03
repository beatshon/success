#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 서버 실행 스크립트
"""

import sys
import os

def main():
    print("🚀 통합 트렌드-주식 분석 서버 시작")
    print("=" * 50)
    
    try:
        # 현재 디렉토리 확인
        current_dir = os.getcwd()
        print(f"현재 디렉토리: {current_dir}")
        
        # 서버 import
        print("서버 모듈을 import 중...")
        from integrated_trend_stock_server import IntegratedTrendStockServer
        
        # 서버 생성
        print("서버 인스턴스를 생성 중...")
        server = IntegratedTrendStockServer(port=8086)
        
        print("✅ 서버 초기화 완료!")
        print("🌐 웹 브라우저에서 http://localhost:8086 접속하세요")
        print("⏹️  서버를 중지하려면 Ctrl+C를 누르세요")
        print("=" * 50)
        
        # 서버 시작
        server.start()
        
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 