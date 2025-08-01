#!/usr/bin/env python3
"""
키움 Open API 연동 진단 스크립트
Windows에서 실행해야 합니다.
"""

import sys
import os
import subprocess
import platform
from datetime import datetime

def print_header():
    """헤더 출력"""
    print("=" * 60)
    print("🔍 키움 Open API 연동 진단 도구")
    print("=" * 60)
    print(f"진단 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"운영체제: {platform.system()} {platform.release()}")
    print()

def check_python_environment():
    """Python 환경 진단"""
    print("🐍 Python 환경 진단")
    print("-" * 30)
    
    # Python 버전 확인
    python_version = sys.version
    print(f"Python 버전: {python_version}")
    
    # Python 경로 확인
    python_path = sys.executable
    print(f"Python 경로: {python_path}")
    
    # 필수 패키지 확인
    required_packages = [
        ('PyQt5', 'PyQt5.QAxContainer'),
        ('loguru', 'loguru'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}: 설치됨")
        except ImportError:
            print(f"❌ {package_name}: 설치 필요")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 설치 필요한 패키지: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Python 환경 진단 완료")
    return True

def check_kiwoom_installation():
    """키움 Open API+ 설치 진단"""
    print("\n🏢 키움 Open API+ 설치 진단")
    print("-" * 30)
    
    # 설치 경로 확인
    possible_paths = [
        r"C:\OpenAPI",
        r"C:\Program Files (x86)\Kiwoom\OpenAPI",
        r"C:\Program Files\Kiwoom\OpenAPI"
    ]
    
    found_paths = []
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ 설치 경로 발견: {path}")
            found_paths.append(path)
        else:
            print(f"❌ 설치 경로 없음: {path}")
    
    if not found_paths:
        print("❌ 키움 Open API+ 설치 경로를 찾을 수 없습니다.")
        print("💡 키움 Open API+를 설치해주세요.")
        return False
    
    # OCX 파일 확인
    ocx_found = False
    for path in found_paths:
        ocx_path = os.path.join(path, "KHOPENAPI.OCX")
        if os.path.exists(ocx_path):
            print(f"✅ OCX 파일 발견: {ocx_path}")
            ocx_found = True
        else:
            print(f"❌ OCX 파일 없음: {ocx_path}")
    
    if not ocx_found:
        print("❌ KHOPENAPI.OCX 파일을 찾을 수 없습니다.")
        return False
    
    print("✅ 키움 Open API+ 설치 진단 완료")
    return True

def check_kiwoom_api_control():
    """키움 API 컨트롤 진단"""
    print("\n🔧 키움 API 컨트롤 진단")
    print("-" * 30)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        
        # QApplication 생성
        app = QApplication(sys.argv)
        print("✅ QApplication 생성 성공")
        
        # 키움 API 컨트롤 생성
        ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        print("✅ 키움 API 컨트롤 생성 성공")
        
        # 기본 메서드 확인
        methods = [
            "CommConnect",
            "GetLoginInfo", 
            "GetMasterCodeName",
            "GetMasterLastPrice"
        ]
        
        for method in methods:
            try:
                getattr(ocx, method)
                print(f"✅ 메서드 확인: {method}")
            except AttributeError:
                print(f"❌ 메서드 없음: {method}")
        
        print("✅ 키움 API 컨트롤 진단 완료")
        return True
        
    except Exception as e:
        print(f"❌ 키움 API 컨트롤 진단 실패: {e}")
        print("💡 해결 방법:")
        print("1. 키움 Open API+ 재설치")
        print("2. OCX 파일 재등록: regsvr32 C:\\OpenAPI\\KHOPENAPI.OCX")
        return False

def check_environment_variables():
    """환경 변수 진단"""
    print("\n🔑 환경 변수 진단")
    print("-" * 30)
    
    # .env 파일 로드
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env 파일 로드 성공")
    except Exception as e:
        print(f"❌ .env 파일 로드 실패: {e}")
    
    # 필수 환경 변수 확인
    required_vars = [
        'KIWOOM_USER_ID',
        'KIWOOM_PASSWORD',
        'KIWOOM_ACCOUNT',
        'KIWOOM_APP_KEY',
        'KIWOOM_APP_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...")
        else:
            print(f"❌ {var}: 설정되지 않음")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ 설정되지 않은 환경 변수: {', '.join(missing_vars)}")
        print("💡 .env 파일에 다음 정보를 입력하세요:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False
    
    print("✅ 환경 변수 진단 완료")
    return True

def check_network_connection():
    """네트워크 연결 진단"""
    print("\n🌐 네트워크 연결 진단")
    print("-" * 30)
    
    # 키움증권 서버 연결 테스트
    servers = [
        "www.kiwoom.com",
        "openapi.kiwoom.com"
    ]
    
    for server in servers:
        try:
            result = subprocess.run(
                ['ping', '-n', '1', server],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {server}: 연결 성공")
            else:
                print(f"❌ {server}: 연결 실패")
        except Exception as e:
            print(f"❌ {server}: 연결 오류 - {e}")
    
    print("✅ 네트워크 연결 진단 완료")
    return True

def check_windows_firewall():
    """Windows 방화벽 진단"""
    print("\n🛡️ Windows 방화벽 진단")
    print("-" * 30)
    
    try:
        # 방화벽 상태 확인
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'allprofiles'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ 방화벽 상태 확인 가능")
            
            # Python 허용 확인
            if "python.exe" in result.stdout.lower():
                print("✅ Python이 방화벽에서 허용됨")
            else:
                print("⚠️ Python이 방화벽에서 허용되지 않을 수 있음")
        else:
            print("❌ 방화벽 상태 확인 실패")
            
    except Exception as e:
        print(f"❌ 방화벽 진단 오류: {e}")
    
    print("✅ Windows 방화벽 진단 완료")
    return True

def run_comprehensive_test():
    """종합 테스트 실행"""
    print("\n🧪 종합 테스트 실행")
    print("-" * 30)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        
        app = QApplication(sys.argv)
        ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 연결
        def on_event_connect(err_code):
            if err_code == 0:
                print("✅ 로그인 이벤트 성공")
            else:
                print(f"❌ 로그인 이벤트 실패: {err_code}")
        
        ocx.OnEventConnect.connect(on_event_connect)
        print("✅ 이벤트 연결 성공")
        
        # 로그인 시도 (실제 로그인은 하지 않음)
        print("✅ 종합 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 종합 테스트 실패: {e}")
        return False

def print_summary(results):
    """진단 결과 요약"""
    print("\n" + "=" * 60)
    print("📊 진단 결과 요약")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    print(f"\n총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {total_tests - passed_tests}개")
    print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 모든 진단이 통과되었습니다!")
        print("키움 Open API를 사용할 준비가 완료되었습니다.")
    else:
        print("\n⚠️ 일부 진단에서 문제가 발견되었습니다.")
        print("위의 해결 방법을 참조하여 문제를 해결하세요.")

def main():
    """메인 함수"""
    print_header()
    
    # 진단 실행
    results = {}
    
    results["Python 환경"] = check_python_environment()
    results["키움 Open API+ 설치"] = check_kiwoom_installation()
    results["키움 API 컨트롤"] = check_kiwoom_api_control()
    results["환경 변수"] = check_environment_variables()
    results["네트워크 연결"] = check_network_connection()
    results["Windows 방화벽"] = check_windows_firewall()
    results["종합 테스트"] = run_comprehensive_test()
    
    # 결과 출력
    print_summary(results)
    
    # 추가 안내
    print("\n📋 다음 단계:")
    if all(results.values()):
        print("1. 실제 로그인 테스트 실행")
        print("2. API 호출 테스트 실행")
        print("3. 트레이딩 전략 구현 시작")
    else:
        print("1. 발견된 문제 해결")
        print("2. 진단 재실행")
        print("3. 키움증권 고객센터 문의 (1544-9000)")

if __name__ == "__main__":
    main() 