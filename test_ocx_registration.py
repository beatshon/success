#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키움 OpenAPI OCX 파일 등록 상태 테스트 스크립트
"""

import sys
import os
import subprocess
import winreg
from pathlib import Path

def check_ocx_file_exists():
    """OCX 파일 존재 여부 확인"""
    print("🔍 OCX 파일 존재 여부 확인 중...")
    
    ocx_path = r"C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
    if os.path.exists(ocx_path):
        print(f"✅ OCX 파일 존재: {ocx_path}")
        return True
    else:
        print(f"❌ OCX 파일 없음: {ocx_path}")
        return False

def check_registry_registration():
    """레지스트리 등록 상태 확인"""
    print("\n🔍 레지스트리 등록 상태 확인 중...")
    
    try:
        # 레지스트리에서 키움 API 등록 정보 확인
        key_path = r"SOFTWARE\Classes\KHOPENAPI.KHOpenAPICtrl.1"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            print("✅ 레지스트리에 등록됨")
            return True
    except FileNotFoundError:
        print("❌ 레지스트리에 등록되지 않음")
        return False
    except Exception as e:
        print(f"❌ 레지스트리 확인 오류: {e}")
        return False

def test_regsvr32():
    """regsvr32 명령어로 OCX 등록 테스트"""
    print("\n🔍 regsvr32 등록 테스트 중...")
    
    ocx_path = r"C:\Program Files (x86)\Kiwoom OpenAPI\KHOPENAPI.OCX"
    
    try:
        # regsvr32 명령어 실행
        result = subprocess.run(
            ['regsvr32', '/s', ocx_path],  # /s는 무음 모드
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ regsvr32 등록 성공")
            return True
        else:
            print(f"❌ regsvr32 등록 실패: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ regsvr32 실행 시간 초과")
        return False
    except Exception as e:
        print(f"❌ regsvr32 실행 오류: {e}")
        return False

def test_pyqt5_import():
    """PyQt5를 통한 OCX 접근 테스트"""
    print("\n🔍 PyQt5 OCX 접근 테스트 중...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        
        # 키움 API OCX 컨트롤 생성
        ax_widget = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        if ax_widget.isValid():
            print("✅ PyQt5 OCX 접근 성공")
            return True
        else:
            print("❌ PyQt5 OCX 접근 실패 - 컨트롤이 유효하지 않음")
            return False
            
    except ImportError as e:
        print(f"❌ PyQt5 임포트 오류: {e}")
        print("💡 해결방법: pip install PyQt5")
        return False
    except Exception as e:
        print(f"❌ PyQt5 OCX 접근 오류: {e}")
        return False

def check_dependencies():
    """의존성 파일 확인"""
    print("\n🔍 의존성 파일 확인 중...")
    
    kiwoom_path = r"C:\Program Files (x86)\Kiwoom OpenAPI"
    required_files = [
        "KHOPENAPI.OCX",
        "KHOPENAPI.dll",
        "msvcp140.dll",
        "vcruntime140.dll"
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(kiwoom_path, file)
        if os.path.exists(file_path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (누락)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 누락된 파일: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ 모든 의존성 파일 존재")
        return True

def check_visual_cpp():
    """Visual C++ 재배포 패키지 확인"""
    print("\n🔍 Visual C++ 재배포 패키지 확인 중...")
    
    try:
        # Visual C++ 2015-2022 재배포 패키지 확인
        key_path = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            version, _ = winreg.QueryValueEx(key, "Version")
            print(f"✅ Visual C++ 2015-2022 설치됨 (버전: {version})")
            return True
    except FileNotFoundError:
        print("❌ Visual C++ 2015-2022 재배포 패키지 없음")
        print("💡 해결방법: Microsoft Visual C++ 재배포 패키지 설치")
        return False
    except Exception as e:
        print(f"❌ Visual C++ 확인 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 키움 OpenAPI OCX 등록 상태 테스트 시작")
    print("=" * 50)
    
    # 테스트 결과 저장
    results = {}
    
    # 1. OCX 파일 존재 확인
    results['ocx_file'] = check_ocx_file_exists()
    
    # 2. 의존성 파일 확인
    results['dependencies'] = check_dependencies()
    
    # 3. Visual C++ 재배포 패키지 확인
    results['visual_cpp'] = check_visual_cpp()
    
    # 4. 레지스트리 등록 상태 확인
    results['registry'] = check_registry_registration()
    
    # 5. regsvr32 테스트
    results['regsvr32'] = test_regsvr32()
    
    # 6. PyQt5 접근 테스트
    results['pyqt5'] = test_pyqt5_import()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name:15}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n총 {total_count}개 테스트 중 {success_count}개 성공")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트가 성공했습니다! 키움 API를 사용할 수 있습니다.")
    else:
        print(f"\n⚠️ {total_count - success_count}개 테스트가 실패했습니다.")
        print("💡 위의 실패 항목을 확인하고 해결해주세요.")
        
        # 실패한 항목에 대한 해결책 제시
        if not results['ocx_file']:
            print("\n🔧 OCX 파일 없음 해결책:")
            print("1. 키움 OpenAPI 재설치")
            print("2. 관리자 권한으로 설치")
            
        if not results['visual_cpp']:
            print("\n🔧 Visual C++ 재배포 패키지 해결책:")
            print("1. Microsoft Visual C++ 재배포 패키지 설치")
            print("2. https://aka.ms/vs/17/release/vc_redist.x86.exe")
            
        if not results['registry'] or not results['regsvr32']:
            print("\n🔧 OCX 등록 해결책:")
            print("1. 관리자 권한으로 명령 프롬프트 실행")
            print("2. regsvr32 \"C:\\Program Files (x86)\\Kiwoom OpenAPI\\KHOPENAPI.OCX\"")
            
        if not results['pyqt5']:
            print("\n🔧 PyQt5 해결책:")
            print("1. pip install PyQt5")
            print("2. Python 환경 재시작")

if __name__ == "__main__":
    main() 