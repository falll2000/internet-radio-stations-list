#!/bin/bash

# 設定變數
DB_PATH="expanded_radio_stations.db"
JSON_PATH="radio_stations.json"

# 檢查資料庫是否存在
if [ ! -f "$DB_PATH" ]; then
    echo "❌ 找不到資料庫檔案: $DB_PATH"
    exit 1
fi

# 1. 從 SQLite 匯出 JSON
echo "📤 匯出電台資料為 JSON..."
sqlite3 "$DB_PATH" <<SQL
.mode json
.output $JSON_PATH
SELECT 
    uuid,
    name,
    url,
    homepage,
    favicon,
    tags,
    country,
    language,
    codec,
    bitrate,
    source_api,
    source_type,
    collection_date,
    metadata
FROM radio_stations 
ORDER BY source_api, name;
SQL

# 檢查 JSON 檔案是否產生成功
if [ ! -f "$JSON_PATH" ]; then
    echo "❌ JSON 檔案產生失敗"
    exit 1
fi

# 顯示統計資訊
STATION_COUNT=$(jq length "$JSON_PATH" 2>/dev/null || echo "unknown")
echo "📊 匯出 $STATION_COUNT 個電台資料"

# 2. 推送到 GitHub
echo "📤 推送到 GitHub..."
git add "$JSON_PATH"

# 檢查是否有變更
if git diff --staged --quiet; then
    echo "ℹ️ 沒有資料變更，跳過推送"
    exit 0
fi

git commit -m "🔄 Update radio stations data - $(date '+%Y-%m-%d %H:%M:%S') - $STATION_COUNT stations"
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ GitHub 推送成功"
else
    echo "❌ GitHub 推送失敗"
    exit 1
fi
EOF