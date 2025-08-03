#!/usr/bin/env python3
"""
키움 API 연동 상태 종합 보고서
현재 시스템의 API 연동 상태를 분석하고 보고합니다.
"""
import os
import sys
import platform
import subprocess
import requests
from datetime import datetime
import config

def check_python_environment():
    """Python 환경 확인"""
    print("🐍 Python 환경 확인")
    print("=" * 40)
    
    print(f"Python 버전: {sys.version}")
    print(f"Python 아키텍처: {platform.architecture()}")
    print(f"Python 경로: {sys.executable}")
    
    # 32비트 확인
    if platform.architecture()[0] == '32bit':
        print("✅ 32비트 Python 사용 중 (키움 API 호환)")
    else:
        print("❌ 64비트 Python 사용 중 (키움 API 비호환)")
    
    return platform.architecture()[0] == '32bit'

def check_required_packages():
    """필요한 패키지 확인"""
    print("\n📦 필요한 패키지 확인")
    print("=" * 40)
    
    required_packages = ['PyQt5', 'requests', 'pandas', 'loguru']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 설치됨")
        except ImportError:
            print(f"❌ {package}: 설치되지 않음")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_kiwoom_installation():
    """키움 설치 상태 확인"""
    print("\n🏢 키움 설치 상태 확인")
    print("=" * 40)
    
    kiwoom_paths = [
        r"C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.OCX",
        r"C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.exe",
        r"C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.dll"
    ]
    
    installed = False
    for path in kiwoom_paths:
        if os.path.exists(path):
            print(f"✅ 발견: {path}")
            installed = True
        else:
            print(f"❌ 없음: {path}")
    
    if not installed:
        print("⚠️ 키움 Open API+가 설치되지 않았습니다.")
        print("   키움증권 홈페이지에서 Open API+를 다운로드하여 설치하세요.")
    
    return installed

def check_registry():
    """레지스트리 확인"""
    print("\n🔧 레지스트리 확인")
    print("=" * 40)
    
    try:
        import winreg
        key_path = r"SOFTWARE\Classes\KHOPENAPI.KHOpenAPICtrl.1"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        print("✅ KHOpenAPI Control 레지스트리 등록됨")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        print("❌ KHOpenAPI Control 레지스트리 등록되지 않음")
        return False
    except Exception as e:
        print(f"❌ 레지스트리 확인 오류: {e}")
        return False

def check_api_config():
    """API 설정 확인"""
    print("\n🔑 API 설정 확인")
    print("=" * 40)
    
    app_key = config.KIWOOM_CONFIG['app_key']
    app_secret = config.KIWOOM_CONFIG['app_secret']
    
    print(f"API 키: {app_key[:10]}...")
    print(f"API 시크릿: {app_secret[:10]}...")
    
    if app_key != 'YOUR_APP_KEY_HERE' and app_secret != 'YOUR_APP_SECRET_HERE':
        print("✅ API 키 설정 완료")
        return True
    else:
        print("❌ API 키가 설정되지 않았습니다.")
        return False

def test_activex_connection():
    """ActiveX 연결 테스트"""
    print("\n🔌 ActiveX 연결 테스트")
    print("=" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        
        app = QApplication(sys.argv)
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        connected = kiwoom.dynamicCall("GetConnectState()")
        print(f"연결 상태: {connected}")
        
        if connected == 1:
            print("✅ ActiveX 연결 성공")
            return True
        else:
            print("⚠️ ActiveX 연결되지 않음 (영웅문 실행 필요)")
            return False
            
    except Exception as e:
        print(f"❌ ActiveX 연결 실패: {e}")
        return False

def test_rest_api():
    """REST API 테스트"""
    print("\n🌐 REST API 테스트")
    print("=" * 40)
    
    try:
        app_key = config.KIWOOM_CONFIG['app_key']
        app_secret = config.KIWOOM_CONFIG['app_secret']
        
        token_url = "https://openapi.kiwoom.com/oauth2/tokenP"
        token_data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ REST API 연결 성공")
            return True
        else:
            print(f"❌ REST API 연결 실패 (상태: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ REST API 테스트 오류: {e}")
        return False

def check_firewall_rules():
    """방화벽 규칙 확인"""
    print("\n🛡️ 방화벽 규칙 확인")
    print("=" * 40)
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-NetFirewallRule -DisplayName "*Kiwoom*"'],
            capture_output=True, text=True, timeout=10
        )
        
        if "Kiwoom" in result.stdout:
            print("✅ 키움 관련 방화벽 규칙 발견")
            return True
        else:
            print("⚠️ 키움 관련 방화벽 규칙 없음")
            return False
            
    except Exception as e:
        print(f"❌ 방화벽 규칙 확인 오류: {e}")
        return False

def generate_recommendations():
    """권장사항 생성"""
    print("\n💡 권장사항")
    print("=" * 40)
    
    recommendations = []
    
    # Python 아키텍처 확인
    if platform.architecture()[0] != '32bit':
        recommendations.append("32비트 Python을 설치하세요.")
    
    # 키움 설치 확인
    kiwoom_path = r"C:\Program Files (x86)\Kiwoom\OpenAPI\KHOPENAPI.OCX"
    if not os.path.exists(kiwoom_path):
        recommendations.append("키움 Open API+를 설치하세요.")
    
    # 영웅문 실행 확인
    recommendations.append("키움 영웅문을 실행하고 로그인하세요.")
    
    # API 승인 확인
    recommendations.append("키움증권 홈페이지에서 Open API+ 신청 및 승인을 받으세요.")
    
    # 관리자 권한 확인
    recommendations.append("Python 스크립트를 관리자 권한으로 실행하세요.")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

def main():
    """메인 함수"""
    print("📊 키움 API 연동 상태 종합 보고서")
    print("=" * 60)
    print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 각 항목 확인
    python_ok = check_python_environment()
    packages_ok = check_required_packages()
    kiwoom_installed = check_kiwoom_installation()
    registry_ok = check_registry()
    api_config_ok = check_api_config()
    activex_ok = test_activex_connection()
    rest_api_ok = test_rest_api()
    firewall_ok = check_firewall_rules()
    
    # 종합 결과
    print("\n📋 종합 결과")
    print("=" * 40)
    
    total_checks = 8
    passed_checks = sum([
        python_ok, packages_ok, kiwoom_installed, registry_ok,
        api_config_ok, activex_ok, rest_api_ok, firewall_ok
    ])
    
    print(f"전체 검사: {total_checks}개")
    print(f"통과: {passed_checks}개")
    print(f"실패: {total_checks - passed_checks}개")
    print(f"성공률: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 모든 검사를 통과했습니다! API 연동이 완료되었습니다.")
    else:
        print("\n⚠️ 일부 검사에서 실패했습니다. 권장사항을 확인하세요.")
        generate_recommendations()
    
    print("\n" + "=" * 60)
    print("✅ 보고서 생성 완료!")

if __name__ == "__main__":
    main() 