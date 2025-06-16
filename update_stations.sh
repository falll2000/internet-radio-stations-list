#!/bin/bash
echo "📻 手動更新電台列表"
echo "=================="

source venv/bin/activate

echo "🔄 正在更新電台資料..."
python3 -c "
from multi_source_radio_collector import MultiSourceRadioCollector
print('開始收集電台資料...')
collector = MultiSourceRadioCollector()
result = collector.collect_all_stations()
collector.sync_stations_to_db(result)
print(f'✅ 更新完成，共收集 {result[\"total_unique\"]} 個電台')

# 顯示統計
summary = collector.get_stations_summary()
print(f'📊 按來源統計: {summary[\"by_source\"]}')
"

echo "✅ 電台更新完成！"
