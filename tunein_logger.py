"""
TuneIn 日誌管理系統
獨立模組，負責所有日誌記錄和管理功能
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import glob


class TuneInLogger:
    """TuneIn 收集結果日誌管理器 - 記錄所有 terminal 輸出"""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        self.tunein_log_dir = self.base_log_dir / "tunein"
        
        # 確保基礎目錄存在
        self.tunein_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 當前分類和日誌器
        self.current_category = None
        self.current_logger = None
        self.current_log_file = None
        
    def start_category_logging(self, category: str, execution_mode: str = "mixed") -> logging.Logger:
        """開始記錄某個分類的所有輸出"""
        # 創建分類資料夾
        category_dir = self.tunein_log_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # 生成日誌檔名
        now = datetime.now()
        log_filename = now.strftime("%Y_%m_%d_%H_%M_%S.log")
        log_file_path = category_dir / log_filename
        
        # 保存當前信息
        self.current_category = category
        self.current_log_file = log_file_path
        
        # 創建日誌器
        logger_name = f'tunein_{category}_{now.strftime("%H%M%S")}'
        category_logger = logging.getLogger(logger_name)
        category_logger.setLevel(logging.DEBUG)
        
        # 清除已存在的處理器
        if category_logger.handlers:
            category_logger.handlers.clear()
        
        # 創建文件處理器 - 記錄所有級別
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 創建控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 設置日誌格式 - 簡潔格式，模擬 terminal 輸出
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # 添加處理器
        category_logger.addHandler(file_handler)
        category_logger.addHandler(console_handler)
        
        self.current_logger = category_logger
        
        # 記錄開始信息
        category_logger.info("=" * 80)
        category_logger.info(f"🚀 TuneIn 分類收集開始")
        category_logger.info(f"📂 分類: {category}")
        category_logger.info(f"📊 執行模式: {execution_mode}")
        category_logger.info(f"📁 日誌文件: {log_file_path}")
        category_logger.info(f"⏰ 開始時間: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        category_logger.info("=" * 80)
        
        return category_logger
    
    def finish_category_logging(self, stations: List[Dict], request_count: int, 
                              failed_requests: int, start_time: datetime, 
                              execution_mode: str):
        """完成分類記錄並添加統計信息"""
        if not self.current_logger:
            return
            
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 記錄結束分隔線
        self.current_logger.info("=" * 80)
        self.current_logger.info("📋 收集完成 - 統計摘要")
        self.current_logger.info("=" * 80)
        
        # 基本統計
        self.current_logger.info(f"🎯 分類: {self.current_category}")
        self.current_logger.info(f"📊 執行模式: {execution_mode}")
        self.current_logger.info(f"⏰ 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.current_logger.info(f"🏁 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.current_logger.info(f"⏱️ 執行時長: {str(duration).split('.')[0]}")  # 去掉微秒
        self.current_logger.info(f"📻 收集電台數: {len(stations)} 個")
        self.current_logger.info(f"📡 總請求數: {request_count} 次")
        self.current_logger.info(f"❌ 失敗請求數: {failed_requests} 次")
        
        # 計算成功率
        success_rate = ((request_count - failed_requests) / max(request_count, 1) * 100) if request_count > 0 else 0
        self.current_logger.info(f"✅ 成功率: {success_rate:.1f}%")
        
        if stations:
            # 統計電台信息
            language_stats = {}
            country_stats = {}
            codec_stats = {}
            bitrate_stats = {}
            
            for station in stations:
                # 語言統計
                language = station.get('language', 'unknown')
                language_stats[language] = language_stats.get(language, 0) + 1
                
                # 國家統計
                country = station.get('country', 'unknown')
                country_stats[country] = country_stats.get(country, 0) + 1
                
                # 編碼統計
                codec = station.get('codec', 'unknown')
                codec_stats[codec] = codec_stats.get(codec, 0) + 1
                
                # 比特率統計
                bitrate = station.get('bitrate', 0)
                if bitrate > 0:
                    bitrate_range = f"{bitrate}kbps"
                    bitrate_stats[bitrate_range] = bitrate_stats.get(bitrate_range, 0) + 1
            
            # 輸出統計信息
            self.current_logger.info("-" * 40)
            self.current_logger.info("📊 電台詳細統計:")
            
            # 語言分布 (按數量排序)
            if language_stats:
                sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
                self.current_logger.info(f"🌐 語言分布:")
                for lang, count in sorted_languages:
                    percentage = (count / len(stations)) * 100
                    self.current_logger.info(f"   {lang}: {count} 個 ({percentage:.1f}%)")
            
            # 國家分布 (按數量排序)
            if country_stats:
                sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)
                self.current_logger.info(f"🏳️ 國家分布:")
                for country, count in sorted_countries[:10]:  # 只顯示前10個
                    percentage = (count / len(stations)) * 100
                    self.current_logger.info(f"   {country}: {count} 個 ({percentage:.1f}%)")
                if len(sorted_countries) > 10:
                    others = sum(count for _, count in sorted_countries[10:])
                    self.current_logger.info(f"   其他: {others} 個")
            
            # 編碼格式分布
            if codec_stats:
                sorted_codecs = sorted(codec_stats.items(), key=lambda x: x[1], reverse=True)
                self.current_logger.info(f"🎵 編碼格式:")
                for codec, count in sorted_codecs:
                    percentage = (count / len(stations)) * 100
                    self.current_logger.info(f"   {codec}: {count} 個 ({percentage:.1f}%)")
            
            # 比特率分布 (只顯示前5個)
            if bitrate_stats:
                sorted_bitrates = sorted(
                    bitrate_stats.items(), 
                    key=lambda x: int(x[0].replace('kbps', '')) if x[0] != 'unknown' else 0, 
                    reverse=True
                )
                self.current_logger.info(f"📡 比特率分布:")
                for bitrate, count in sorted_bitrates[:5]:
                    percentage = (count / len(stations)) * 100
                    self.current_logger.info(f"   {bitrate}: {count} 個 ({percentage:.1f}%)")
            
            # 電台樣本 (前5個)
            self.current_logger.info("-" * 40)
            self.current_logger.info("🎵 電台樣本 (前5個):")
            for i, station in enumerate(stations[:5], 1):
                name = station.get('name', 'Unknown')[:50]  # 限制名稱長度
                language = station.get('language', 'unknown')
                country = station.get('country', 'unknown')
                bitrate = station.get('bitrate', 0)
                self.current_logger.info(f"   {i}. {name}")
                self.current_logger.info(f"      語言: {language} | 國家: {country} | 比特率: {bitrate}kbps")
        
        self.current_logger.info("=" * 80)
        self.current_logger.info(f"✅ 分類 {self.current_category} 收集完成")
        self.current_logger.info("=" * 80)
        
        # 清理當前狀態
        self.current_category = None
        self.current_logger = None
        self.current_log_file = None
    
    def cleanup_old_logs(self):
        """清理上個月的日誌文件"""
        try:
            # 計算上個月的年月
            today = datetime.now()
            if today.month == 1:
                last_month_year = today.year - 1
                last_month_month = 12
            else:
                last_month_year = today.year
                last_month_month = today.month - 1
            
            last_month_prefix = f"{last_month_year:04d}_{last_month_month:02d}_"
            
            total_deleted = 0
            deleted_categories = []
            
            # 遍歷所有分類資料夾
            for category_dir in self.tunein_log_dir.iterdir():
                if category_dir.is_dir():
                    category_deleted = 0
                    
                    # 尋找上個月的日誌文件
                    log_pattern = category_dir / f"{last_month_prefix}*.log"
                    
                    # 刪除 log 文件
                    for log_file in glob.glob(str(log_pattern)):
                        try:
                            file_size = os.path.getsize(log_file) / (1024 * 1024)  # MB
                            os.remove(log_file)
                            category_deleted += 1
                            total_deleted += 1
                            print(f"🗑️ 刪除: {log_file} ({file_size:.2f} MB)")
                        except Exception as e:
                            print(f"⚠️ 無法刪除日誌文件 {log_file}: {e}")
                    
                    if category_deleted > 0:
                        deleted_categories.append(f"{category_dir.name}({category_deleted})")
            
            if total_deleted > 0:
                print(f"🧹 清理完成: 刪除了 {total_deleted} 個上月日誌文件")
                print(f"📂 涉及分類: {', '.join(deleted_categories)}")
                print(f"📅 清理目標: {last_month_year}年{last_month_month}月")
            else:
                print(f"🧹 清理完成: 沒有找到需要刪除的上月日誌文件 ({last_month_year}年{last_month_month}月)")
                
        except Exception as e:
            print(f"❌ 清理舊日誌失敗: {e}")
    
    def get_log_statistics(self) -> Dict:
        """獲取日誌統計信息"""
        stats = {
            'categories': {},
            'total_files': 0,
            'total_size_mb': 0,
            'date_range': {'earliest': None, 'latest': None}
        }
        
        try:
            all_dates = []
            
            for category_dir in self.tunein_log_dir.iterdir():
                if category_dir.is_dir():
                    category_name = category_dir.name
                    log_files = list(category_dir.glob("*.log"))
                    
                    category_stats = {
                        'log_files': len(log_files),
                        'total_files': len(log_files),
                        'size_mb': 0
                    }
                    
                    # 計算文件大小
                    for file_path in log_files:
                        try:
                            size = file_path.stat().st_size
                            category_stats['size_mb'] += size / (1024 * 1024)
                            
                            # 提取日期用於統計
                            filename = file_path.stem
                            if filename.count('_') >= 5:  # yyyy_mm_dd_HH_MM_SS format
                                date_part = '_'.join(filename.split('_')[:3])
                                try:
                                    file_date = datetime.strptime(date_part, '%Y_%m_%d')
                                    all_dates.append(file_date)
                                except ValueError:
                                    pass
                        except Exception:
                            pass
                    
                    stats['categories'][category_name] = category_stats
                    stats['total_files'] += category_stats['total_files']
                    stats['total_size_mb'] += category_stats['size_mb']
            
            # 計算日期範圍
            if all_dates:
                stats['date_range']['earliest'] = min(all_dates).strftime('%Y-%m-%d')
                stats['date_range']['latest'] = max(all_dates).strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"❌ 獲取日誌統計失敗: {e}")
        
        return stats
    
    def print_log_statistics(self):
        """打印日誌統計信息"""
        stats = self.get_log_statistics()
        
        print("📊 TuneIn 日誌統計")
        print("=" * 50)
        print(f"📁 總文件數: {stats['total_files']}")
        print(f"💽 總大小: {stats['total_size_mb']:.2f} MB")
        
        if stats['date_range']['earliest']:
            print(f"📅 日期範圍: {stats['date_range']['earliest']} ~ {stats['date_range']['latest']}")
        
        if stats['categories']:
            print("📂 分類統計:")
            for category, cat_stats in sorted(stats['categories'].items()):
                print(f"   {category}: {cat_stats['total_files']} 文件, {cat_stats['size_mb']:.2f} MB")
        
        print("=" * 50)


# 使用示例和測試
if __name__ == "__main__":
    # 創建日誌管理器
    logger_manager = TuneInLogger()
    
    # 清理舊日誌
    logger_manager.cleanup_old_logs()
    
    # 顯示統計
    logger_manager.print_log_statistics()
    
    # 測試日誌記錄
    print("\n🧪 測試日誌記錄功能...")
    
    # 模擬數據
    test_stations = [
        {'name': 'Test Radio 1', 'language': 'chinese', 'country': 'Taiwan', 'codec': 'mp3', 'bitrate': 128},
        {'name': 'Test Radio 2', 'language': 'english', 'country': 'USA', 'codec': 'aac', 'bitrate': 64},
        {'name': 'Test Radio 3', 'language': 'chinese', 'country': 'Hong Kong', 'codec': 'mp3', 'bitrate': 256},
    ]
    
    # 開始測試日誌
    start_time = datetime.now()
    test_logger = logger_manager.start_category_logging("test", "mixed")
    
    test_logger.info("🔍 這是一個測試日誌訊息")
    test_logger.warning("⚠️ 這是一個警告訊息")
    test_logger.debug("🐛 這是一個調試訊息")
    
    # 結束測試日誌
    logger_manager.finish_category_logging(test_stations, 5, 1, start_time, "mixed")
    
    print("✅ 測試完成！")