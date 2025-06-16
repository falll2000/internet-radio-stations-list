#!/bin/bash

# 確保使用 Bash
if [ -z "$BASH_VERSION" ]; then
    echo "🔄 切換到 Bash 環境..."
    exec bash "$0" "$@"
fi

# 檢查是否在正確的目錄
if [ ! -d "venv" ]; then
    echo "❌ 找不到虛擬環境目錄，請確保在專案根目錄執行此腳本"
    echo "📍 當前目錄: $(pwd)"
    echo "💡 請先執行: cd ~/taiwan-radio-app"
    exit 1
fi

echo "🐍 啟動台灣電台App虛擬環境..."
echo "📍 專案目錄: $(pwd)"
echo ""

# 啟動虛擬環境
. venv/bin/activate

# 檢查虛擬環境是否啟動成功
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ 虛擬環境已啟用！"
    echo "🐍 虛擬環境路徑: $VIRTUAL_ENV"
else
    echo "❌ 虛擬環境啟動失敗"
    echo "🔍 請檢查虛擬環境是否正確安裝"
    exit 1
fi

echo ""
echo "💡 可用指令："
echo "   python3 start_radio_app.py  # 啟動電台服務"
echo "   ./check_status.sh          # 檢查服務狀態"
echo "   ./update_stations.sh       # 更新電台列表"
echo "   ./view_logs.sh             # 查看日誌"
echo "   deactivate                 # 退出虛擬環境"
echo "   exit                       # 退出 shell"
echo ""

# 顯示Python路徑確認
echo "🔍 當前 Python: $(which python3)"
echo "📦 當前 pip: $(which pip)"
echo ""

# 設定自定義提示符（支援不同 shell）
if [ -n "$BASH_VERSION" ]; then
    # Bash 彩色提示符
    export PS1="(taiwan-radio) \[\033[1;32m\]\u@\h\[\033[0m\]:\[\033[1;34m\]\w\[\033[0m\]\$ "
elif [ -n "$ZSH_VERSION" ]; then
    # Zsh 提示符
    export PS1="(taiwan-radio) %n@%m:%~ %# "
else
    # 通用提示符
    export PS1="(taiwan-radio) \u@\h:\w\$ "
fi

# 啟動新的交互式 shell
if [ -n "$BASH_VERSION" ]; then
    exec bash --norc -i
elif [ -n "$ZSH_VERSION" ]; then
    exec zsh -i
else
    exec bash --norc -i
fi
