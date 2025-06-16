🎵 台灣電台App - 使用說明
========================================

🎉 恭喜！台灣電台App已成功安裝！
本系統整合了多個電台來源，提供超過2000個電台的豐富內容。

📍 專案位置
========================================
專案目錄: ~/taiwan-radio-app/
配置文件: expanded_radio_stations.db
日誌文件: radio_app.log

🌐 API服務資訊
========================================
內網存取: http://192.168.0.84:5000
本機存取: http://localhost:5000

主要API端點:
- 健康檢查: /api/health
- 電台列表: /api/stations
- 搜尋電台: /api/stations/search?q=關鍵字
- 精選電台: /api/stations/featured
- 統計資訊: /api/stats
- 手動更新: /api/update (POST)

🧪 測試API指令
========================================
# 健康檢查
curl http://localhost:5000/api/health

# 獲取電台列表 (前10個)
curl "http://localhost:5000/api/stations?limit=10"

# 搜尋台灣電台
curl "http://localhost:5000/api/stations/search?q=台灣"

# 獲取精選電台
curl http://localhost:5000/api/stations/featured

# 查看統計資訊
curl http://localhost:5000/api/stats

🛠️ 管理指令
========================================
所有管理指令都在專案目錄中執行：
cd ~/taiwan-radio-app

基本管理:
./check_status.sh     # 檢查服務狀態
./restart_service.sh  # 重啟服務
./update_stations.sh  # 手動更新電台列表
./view_logs.sh        # 查看系統日誌
./stop_service.sh     # 停止服務

虛擬環境管理:
./enter_venv.sh       # 進入虛擬環境
./stop_venv.sh        # 停止服務並退出虛擬環境

手動操作:
source venv/bin/activate        # 手動進入虛擬環境
python3 start_radio_app.py      # 手動啟動服務
deactivate                      # 退出虛擬環境 (在虛擬環境shell中)
exit                            # 退出虛擬環境shell

⏰ 自動更新
========================================
系統會每天早上8點自動更新電台列表。
如需立即更新，請執行：
./update_stations.sh

📊 電台統計資訊
========================================
總電台數量: 2221個
資料來源分佈:
- 手動精選電台: 7個 (高品質台灣電台)
- Radio Browser API: 2214個 (國際電台)

電台涵蓋範圍:
- 台灣本地電台 (中文、英文)
- 國際中文電台
- 各種音樂類型 (流行、古典、爵士等)
- 新聞、談話、教育節目

🔧 故障排除
========================================

1. 服務無法啟動:
   - 檢查端口5000是否被占用: lsof -i :5000
   - 查看錯誤日誌: ./view_logs.sh
   - 重新安裝虛擬環境: rm -rf venv && python3 -m venv venv

2. API無回應:
   - 檢查服務狀態: ./check_status.sh
   - 重啟服務: ./restart_service.sh
   - 檢查防火牆設定

3. 電台更新失敗:
   - 檢查網路連線
   - 手動更新: ./update_stations.sh
   - 查看詳細日誌: ./view_logs.sh

4. 虛擬環境問題:
   - 確保在專案目錄: cd ~/taiwan-radio-app
   - 重新進入虛擬環境: ./enter_venv.sh
   - 檢查Python版本: python3 --version

📱 App整合說明
========================================
在你的App中設定以下配置:

API Base URL: http://192.168.0.84:5000
(如果是本機測試: http://localhost:5000)

建議的API使用流程:
1. 先呼叫健康檢查確認服務可用
2. 使用電台列表API獲取電台資料
3. 實作搜尋功能使用搜尋API
4. 優先顯示精選電台提升用戶體驗

🚀 開發建議
========================================
1. 實作電台收藏功能
2. 加入播放歷史記錄
3. 支援離線下載 (如果電台支援)
4. 實作電台分類瀏覽
5. 加入電台評分機制

📞 技術支援
========================================
如遇到技術問題：
1. 先查看本說明文件的故障排除章節
2. 執行 ./check_status.sh 檢查系統狀態
3. 查看日誌 ./view_logs.sh 了解詳細錯誤
4. 記錄錯誤訊息以便協助除錯

🎵 享受你的電台App！
========================================
系統已經準備就緒，包含2221個電台等你探索！
每天都會自動更新，確保內容保持最新。

最後更新: 2025-06-13
版本: v1.0 簡化部署版
