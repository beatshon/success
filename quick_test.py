#!/usr/bin/env python3
"""
매우 빠른 키움 API 에러 처리 테스트
"""

import os
import time

# 빠른 테스트 환경 설정
os.environ['DISABLE_BACKGROUND_MONITORING'] = '1'
os.environ['DISABLE_AUTO_RECOVERY'] = '1'

def quick_test():
    """매우 빠른 테스트"""
    start_time = time.time()
    
    try:
        # 모듈 import
        from error_handler import ErrorType, ErrorLevel, handle_error
        from system_monitor import record_api_call, get_performance_stats
        
        # 빠른 에러 처리
        handle_error(ErrorType.API, '빠른 테스트', error_level=ErrorLevel.WARNING)
        
        # 빠른 API 호출 기록
        record_api_call('quick_test', 0.001, True)
        
        # 통계 확인
        stats = get_performance_stats()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ 빠른 테스트 완료!")
        print(f"⏱️  실행 시간: {execution_time:.3f}초")
        print(f"📊 API 함수 수: {len(stats['api_stats'])}개")
        print(f"📈 에러 수: {stats.get('error_stats', {}).get('total_errors', 0)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 매우 빠른 키움 API 에러 처리 테스트 시작...")
    success = quick_test()
    
    if success:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("💥 테스트에 실패했습니다.") 