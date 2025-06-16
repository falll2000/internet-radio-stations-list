#!/bin/bash

# 確保使用 Bash
if [ -z "$BASH_VERSION" ]; then
    echo "🔄 切換到 Bash 環境..."
    exec bash "$0" "$@"
fi

echo "🛑 停止所有服務並退出"
echo "===================="

# 停止電台服務
echo "🛑 停止電台服務..."
pkill -f "start_radio_app.py" 2>/dev/null || true
pkill -f "radio_api_server.py" 2>/dev/null || true
sleep 2

# 檢查是否還有程序在運行
if pgrep -f "start_radio_app.py" > /dev/null || pgrep -f "radio_api_server.py" > /dev/null; then
    echo "⚠️ 電台服務仍在運行，強制終止..."
    pkill -9 -f "start_radio_app.py" 2>/dev/null || true
    pkill -9 -f "radio_api_server.py" 2>/dev/null || true
    sleep 1
    
    if pgrep -f "start_radio_app.py" > /dev/null || pgrep -f "radio_api_server.py" > /dev/null; then
        echo "❌ 無法完全停止服務"
        echo "🔍 仍在運行的程序:"
        pgrep -f "start_radio_app.py" 2>/dev/null | while read pid; do
            ps -p $pid -o pid,cmd --no-headers 2>/dev/null || echo "PID $pid"
        done
        pgrep -f "radio_api_server.py" 2>/dev/null | while read pid; do
            ps -p $pid -o pid,cmd --no-headers 2>/dev/null || echo "PID $pid"
        done
        echo ""
        echo "💡 你可以手動執行: kill -9 <PID>"
    else
        echo "✅ 所有電台服務已強制停止"
    fi
else
    echo "✅ 電台服務已完全停止"
fi

echo ""
echo "📊 最終狀態:"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "   🐍 虛擬環境: 在環境中，即將退出"
else
    echo "   🐍 虛擬環境: 不在虛擬環境中"
fi

if pgrep -f "start_radio_app.py" > /dev/null || pgrep -f "radio_api_server.py" > /dev/null; then
    echo "   📻 電台服務: 仍在運行"
else
    echo "   📻 電台服務: 已停止"
fi

echo ""
echo "✅ 所有服務已停止"
echo "💡 提示:"
echo "   重新啟動服務: ./enter_venv.sh"
echo "   檢查狀態: ./check_status.sh"
echo ""

# 如果在虛擬環境中，退出shell（這會同時退出虛擬環境）
if [ -n "$VIRTUAL_ENV" ]; then
    echo "🚪 退出虛擬環境..."
    exit 0
else
    echo "🏁 操作完成"
fi
