#!/bin/bash
echo "🔄 重啟台灣電台App服務"
echo "===================="

# 停止現有程序
pkill -f "start_radio_app.py" 2>/dev/null || true
sleep 2

# 啟動新程序
echo "🚀 啟動新服務..."
source venv/bin/activate
nohup python3 start_radio_app.py > radio_app.log 2>&1 &
echo "✅ 服務已在背景啟動"

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 5

# 檢查狀態
./check_status.sh
