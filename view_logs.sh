#!/bin/bash
echo "📋 查看台灣電台App日誌"
echo "===================="

if [[ -f "radio_app.log" ]]; then
    echo "--- 最近50行 ---"
    tail -n 50 radio_app.log
else
    echo "無日誌檔案"
fi

echo ""
echo "💡 提示: 使用 'tail -f radio_app.log' 即時查看日誌"
