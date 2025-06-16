#!/bin/bash
echo "🛑 停止台灣電台App服務"
echo "==================="

pkill -f "start_radio_app.py" 2>/dev/null || true
sleep 2

if pgrep -f "start_radio_app.py" > /dev/null; then
    echo "⚠️ 程序仍在運行，強制終止..."
    pkill -9 -f "start_radio_app.py" 2>/dev/null || true
    sleep 1
    
    if pgrep -f "start_radio_app.py" > /dev/null; then
        echo "❌ 無法停止程序"
    else
        echo "✅ 程序已強制停止"
    fi
else
    echo "✅ 服務已停止"
fi
