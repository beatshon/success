#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

class LogCleanupManager:
    """로그 파일 정리 관리자"""
    
    def __init__(self, base_dir="logs", retention_days=30):
        self.base_dir = Path(base_dir)
        self.retention_days = retention_days
        self.cutoff_date = datetime.now() - timedelta(days=retention_days)
        
    def get_folder_size(self, folder_path):
        """폴더 크기 계산 (MB 단위)"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size / (1024 * 1024)  # MB로 변환
        except Exception as e:
            logging.error(f"폴더 크기 계산 오류 ({folder_path}): {e}")
            return 0
    
    def backup_important_logs(self, folder_path):
        """중요한 로그 파일 백업"""
        try:
            backup_dir = Path("logs_backup") / Path(folder_path).name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 중요한 로그 파일만 백업
            important_files = ["error_log.csv", "critical_errors.log"]
            
            for file_name in important_files:
                source_file = Path(folder_path) / file_name
                if source_file.exists():
                    dest_file = backup_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    logging.info(f"중요 로그 백업: {source_file} → {dest_file}")
                    
        except Exception as e:
            logging.error(f"백업 중 오류 ({folder_path}): {e}")
    
    def cleanup_logs(self, dry_run=False):
        """로그 파일 정리"""
        if not self.base_dir.exists():
            logging.warning(f"로그 디렉토리가 존재하지 않습니다: {self.base_dir}")
            return
        
        deleted_count = 0
        total_size_freed = 0
        
        logging.info(f"로그 정리 시작 (보관 기간: {self.retention_days}일)")
        logging.info(f"삭제 기준 날짜: {self.cutoff_date.strftime('%Y-%m-%d')}")
        
        try:
            for folder in self.base_dir.iterdir():
                if not folder.is_dir():
                    continue
                
                # 날짜 형식 확인 (YYYY-MM-DD)
                try:
                    folder_date = datetime.strptime(folder.name, "%Y-%m-%d")
                except ValueError:
                    logging.warning(f"날짜 형식이 아닌 폴더 건너뜀: {folder.name}")
                    continue
                
                # 삭제 대상 확인
                if folder_date < self.cutoff_date:
                    folder_size = self.get_folder_size(folder)
                    
                    if dry_run:
                        logging.info(f"[DRY RUN] 삭제 예정: {folder} (크기: {folder_size:.2f}MB)")
                    else:
                        # 중요 로그 백업
                        self.backup_important_logs(folder)
                        
                        # 폴더 삭제
                        shutil.rmtree(folder)
                        deleted_count += 1
                        total_size_freed += folder_size
                        
                        logging.info(f"삭제 완료: {folder} (크기: {folder_size:.2f}MB)")
                else:
                    folder_size = self.get_folder_size(folder)
                    logging.debug(f"보관 대상: {folder} (크기: {folder_size:.2f}MB)")
        
        except Exception as e:
            logging.error(f"로그 정리 중 오류 발생: {e}")
            return False
        
        # 결과 요약
        if dry_run:
            logging.info(f"[DRY RUN] 정리 완료 - 삭제 예정: {deleted_count}개 폴더")
        else:
            logging.info(f"정리 완료 - 삭제된 폴더: {deleted_count}개, 절약된 공간: {total_size_freed:.2f}MB")
        
        return True
    
    def get_log_statistics(self):
        """로그 통계 정보"""
        if not self.base_dir.exists():
            return None
        
        stats = {
            "total_folders": 0,
            "total_size_mb": 0,
            "oldest_log": None,
            "newest_log": None,
            "folders_to_delete": 0,
            "size_to_free_mb": 0
        }
        
        try:
            for folder in self.base_dir.iterdir():
                if not folder.is_dir():
                    continue
                
                try:
                    folder_date = datetime.strptime(folder.name, "%Y-%m-%d")
                except ValueError:
                    continue
                
                folder_size = self.get_folder_size(folder)
                
                stats["total_folders"] += 1
                stats["total_size_mb"] += folder_size
                
                # 최신/최고 로그 날짜 업데이트
                if stats["oldest_log"] is None or folder_date < stats["oldest_log"]:
                    stats["oldest_log"] = folder_date
                if stats["newest_log"] is None or folder_date > stats["newest_log"]:
                    stats["newest_log"] = folder_date
                
                # 삭제 대상 확인
                if folder_date < self.cutoff_date:
                    stats["folders_to_delete"] += 1
                    stats["size_to_free_mb"] += folder_size
                    
        except Exception as e:
            logging.error(f"통계 수집 중 오류: {e}")
            return None
        
        return stats
    
    def print_statistics(self):
        """로그 통계 출력"""
        stats = self.get_log_statistics()
        if not stats:
            return
        
        print("\n" + "=" * 60)
        print("📊 로그 파일 통계")
        print("=" * 60)
        print(f"총 로그 폴더: {stats['total_folders']}개")
        print(f"총 크기: {stats['total_size_mb']:.2f}MB")
        print(f"최고 로그: {stats['oldest_log'].strftime('%Y-%m-%d') if stats['oldest_log'] else 'N/A'}")
        print(f"최신 로그: {stats['newest_log'].strftime('%Y-%m-%d') if stats['newest_log'] else 'N/A'}")
        print(f"삭제 대상: {stats['folders_to_delete']}개 폴더")
        print(f"절약 가능: {stats['size_to_free_mb']:.2f}MB")
        print("=" * 60)


def main():
    """메인 함수"""
    print("🧹 로그 파일 자동 정리 시스템")
    print("=" * 60)
    
    # 설정
    retention_days = 30
    dry_run = False
    
    # 명령행 인수 처리
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            dry_run = True
            print("🔍 DRY RUN 모드 (실제 삭제하지 않음)")
        elif sys.argv[1].isdigit():
            retention_days = int(sys.argv[1])
            print(f"📅 보관 기간: {retention_days}일")
        else:
            print("사용법: python log_cleanup.py [보관일수] [--dry-run]")
            print("예시: python log_cleanup.py 30 --dry-run")
            return
    
    if len(sys.argv) > 2 and sys.argv[2] == "--dry-run":
        dry_run = True
        print("🔍 DRY RUN 모드 (실제 삭제하지 않음)")
    
    # 로그 정리 매니저 초기화
    cleanup_manager = LogCleanupManager(retention_days=retention_days)
    
    # 통계 출력
    cleanup_manager.print_statistics()
    
    # 사용자 확인
    if not dry_run:
        response = input(f"\n{retention_days}일 이상 된 로그 파일을 삭제하시겠습니까? (y/N): ").strip().lower()
        if response != 'y':
            print("정리를 취소합니다.")
            return
    
    # 로그 정리 실행
    print(f"\n{'🔍 검사 중...' if dry_run else '🧹 정리 중...'}")
    success = cleanup_manager.cleanup_logs(dry_run=dry_run)
    
    if success:
        if dry_run:
            print("\n✅ DRY RUN 완료 - 실제 삭제할 항목을 확인했습니다.")
        else:
            print("\n✅ 로그 정리 완료!")
    else:
        print("\n❌ 로그 정리 중 오류가 발생했습니다.")
    
    # 정리 후 통계
    if not dry_run:
        print("\n📊 정리 후 통계:")
        cleanup_manager.print_statistics()


if __name__ == "__main__":
    main() 