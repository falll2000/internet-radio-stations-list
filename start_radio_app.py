#!/usr/bin/env python3
"""
台灣電台App主啟動腳本
"""

import sys
import os
import time
import signal
from datetime import datetime

def signal_handler(signum, frame):
    print("\n🛑 收到停止信號，正在關閉服務...")
    sys.exit(0)

def main():
    print("🎵 台灣電台App啟動中...")
    print("=" * 40)
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 首次收集電台資料
        print("📻 初始化電台資料...")
        from multi_source_radio_collector import MultiSourceRadioCollector
        
        collector = MultiSourceRadioCollector()
        result = collector.collect_all_stations()
        collector.sync_stations_to_db(result)
        
        print(f"✅ 成功收集 {result['total_unique']} 個電台")
        
        # 顯示統計
        summary = collector.get_stations_summary()
        print(f"📊 電台統計: {summary['by_source']}")
        
        # 啟動API服務器
        print("🚀 啟動API服務器...")
        from radio_api_server import RadioAPI
        
        api = RadioAPI()
        
        print("✅ 台灣電台App已成功啟動！")
        print("📡 API端點: http://localhost:5000")
        print("🔍 健康檢查: http://localhost:5000/api/health")
        print("📱 電台列表: http://localhost:5000/api/stations")
        print("⏰ 每日早上8點自動更新電台")
        print("")
        print("按 Ctrl+C 停止服務")
        
        # 啟動服務
        api.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 用戶停止服務")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
