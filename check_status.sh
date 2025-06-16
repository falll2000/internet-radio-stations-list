#!/bin/bash
echo "🔍 台灣電台App狀態檢查"
echo "======================"

# 檢查程序
if pgrep -f "start_radio_app.py" > /dev/null; then
    echo "✅ 服務正在運行"
    PID=$(pgrep -f "start_radio_app.py")
    echo "📍 進程ID: $PID"
else
    echo "❌ 服務未運行"
fi

# 檢查端口
if command -v lsof &> /dev/null; then
    if lsof -i :5000 &> /dev/null; then
        echo "✅ 端口 5000 已開啟"
    else
        echo "❌ 端口 5000 未開啟"
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tuln | grep ":5000" > /dev/null; then
        echo "✅ 端口 5000 已開啟"
    else
        echo "❌ 端口 5000 未開啟"
    fi
fi

# 測試API
if command -v curl &> /dev/null; then
    if curl -s http://localhost:5000/api/health > /dev/null; then
        echo "✅ API 正常回應"
        
        # 顯示電台統計
        echo "📊 電台統計:"
        curl -s http://localhost:5000/api/stats | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        stats = data['statistics']
        print(f'  總電台數量: {stats[\"total_stations\"]}')
        print(f'  資料來源: {stats[\"by_source\"]}')
        print(f'  最後更新: {stats[\"last_update\"]}')
    else:
        print('  無法獲取統計資料')
except:
    print('  API回應格式錯誤')
"
    else
        echo "❌ API 無回應"
    fi
fi

# 檢查資料庫
if [[ -f "expanded_radio_stations.db" ]]; then
    if command -v sqlite3 &> /dev/null; then
        STATION_COUNT=$(sqlite3 expanded_radio_stations.db "SELECT COUNT(*) FROM radio_stations;" 2>/dev/null || echo "0")
        echo "📻 資料庫電台數量: $STATION_COUNT"
    fi
else
    echo "❌ 資料庫檔案不存在"
fi
