#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源電台收集器 - 簡化版
整合多個公開API來源，大幅增加電台數量
"""
import requests
import json
import sqlite3
import time
import logging
from datetime import datetime
from typing import List, Dict
import hashlib

# 導入各個收集器
from tunein_collector import TuneInCollector
from radio_browser_collector import RadioBrowserCollector


class MultiSourceRadioCollector:
    def __init__(self, db_path: str = "expanded_radio_stations.db"):
        self.db_path = db_path
        
        # 設定日誌
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化資料庫
        self.init_database()

    def init_database(self):
        """初始化資料庫結構"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS radio_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                homepage TEXT,
                favicon TEXT,
                tags TEXT,
                country TEXT,
                language TEXT,
                codec TEXT,
                bitrate INTEGER,
                source_api TEXT,
                source_type TEXT,
                collection_date TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                UNIQUE(name, url, source_api)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_manual_premium_stations(self) -> List[Dict]:
        """加入手動收集的高品質台灣電台"""
        self.logger.info("👑 加入手動收集的高品質電台...")
        
        premium_stations = [
            {
                'uuid': 'manual_icrt_fm100',
                'name': 'ICRT FM100.7',
                'url': 'https://live.leanstream.co/ICRTFM-MP3',
                'homepage': 'https://www.icrt.com.tw',
                'favicon': 'https://www.icrt.com.tw/favicon.ico',
                'tags': 'english,taiwan,news,music,premium',
                'country': 'Taiwan',
                'language': 'english',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_premium',
                'metadata': json.dumps({'verified': True, 'quality': 'high'})
            },
            {
                'uuid': 'manual_good_radio_989',
                'name': '好事989 Good Radio',
                'url': 'https://stream.rcs.revma.com/3yyys8mpkr3uv',
                'homepage': 'https://www.goodradio.com.tw',
                'favicon': 'https://www.goodradio.com.tw/favicon.ico',
                'tags': 'taiwan,good_music,premium,easy_listening,chinese',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_premium',
                'metadata': json.dumps({'verified': True, 'quality': 'high'})
            },
            {
                'uuid': 'manual_hit_fm',
                'name': 'Hit FM 聯播網 FM107.7',
                'url': 'https://live.leanstream.co/HITFM-MP3',
                'homepage': 'https://www.hitoradio.com',
                'favicon': 'https://www.hitoradio.com/favicon.ico',
                'tags': 'taiwan,pop,chinese,music,premium',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_premium',
                'metadata': json.dumps({'verified': True, 'popular': True})
            },
            {
                'uuid': 'manual_bcc_music',
                'name': '中廣音樂網 FM96.3',
                'url': 'https://stream.rcs.revma.com/ue4wkzdt08uv',
                'homepage': 'https://www.bcc.com.tw',
                'favicon': 'https://www.bcc.com.tw/favicon.ico',
                'tags': 'taiwan,music,classical,chinese,premium',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_premium',
                'metadata': json.dumps({'verified': True, 'genre': 'music'})
            },
            {
                'uuid': 'manual_kiss_radio',
                'name': 'KISS Radio 大眾廣播 FM99.9',
                'url': 'https://stream.rcs.revma.com/d8n8j3ca3k8uv',
                'homepage': 'https://www.kiss.com.tw',
                'favicon': 'https://www.kiss.com.tw/favicon.ico',
                'tags': 'taiwan,pop,music,chinese,premium',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_premium',
                'metadata': json.dumps({'verified': True, 'popular': True})
            },
            {
                'uuid': 'manual_police_radio',
                'name': '警察廣播電台',
                'url': 'https://cast.npa.gov.tw/live/pbs_128.m3u8',
                'homepage': 'https://www.pbs.gov.tw',
                'favicon': 'https://www.pbs.gov.tw/favicon.ico',
                'tags': 'taiwan,government,public,chinese',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_government',
                'metadata': json.dumps({'verified': True, 'official': True})
            },
            {
                'uuid': 'manual_ner_news',
                'name': '國立教育廣播電台',
                'url': 'https://live-ner.cdn.hinet.net/live/ner1/playlist.m3u8',
                'homepage': 'https://www.ner.gov.tw',
                'favicon': 'https://www.ner.gov.tw/favicon.ico',
                'tags': 'taiwan,education,government,chinese',
                'country': 'Taiwan',
                'language': 'chinese',
                'codec': 'mp3',
                'bitrate': 128,
                'source_api': 'manual',
                'source_type': 'manual_government',
                'metadata': json.dumps({'verified': True, 'education': True})
            }
        ]
        
        self.logger.info(f"✅ 手動電台: 加入 {len(premium_stations)} 個高品質電台")
        return premium_stations

    def should_run_tunein_today(self) -> bool:
        """檢查今天是否應該執行 TuneIn 收集"""
        from datetime import datetime
        
        now = datetime.now()
        today = now.day
        weekday = now.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 6=Sunday
        is_sunday = weekday == 6
        
        # 計算是第幾周
        first_day_of_month = datetime(now.year, now.month, 1)
        first_weekday = first_day_of_month.weekday()
        week_of_month = ((today - 1 + first_weekday) // 7) + 1
        
        weekday_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        
        # 週一：公共API + TuneIn特定類別 + 手動電台
        if weekday == 0:  # Monday
            self.logger.info(f"📅 今天是{weekday_names[weekday]}，執行: 公共API(每日) + TuneIn特定類別 + 手動電台")
            return True
        
        # 週二到週四：TuneIn 執行日 (執行特定類別)
        elif weekday in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
            self.logger.info(f"📅 今天是{weekday_names[weekday]}，TuneIn 特定類別執行日")
            return True
        
        # 週日檢查：第1-3周執行超大分類
        elif is_sunday:
            if week_of_month in [1, 2, 3]:  # 第1-3周週日執行超大分類
                self.logger.info(f"📅 今天是第{week_of_month}周{weekday_names[weekday]}，TuneIn 超大分類執行日")
                return True
            else:
                self.logger.info(f"📅 今天是第{week_of_month}周{weekday_names[weekday]}，TuneIn 休息日")
                return False
        
        # 週五、週六：休息日
        else:  # Friday, Saturday
            self.logger.info(f"📅 今天是{weekday_names[weekday]}，TuneIn 休息日")
            return False

    def get_tunein_collection_mode(self) -> str:
        """獲取 TuneIn 收集模式"""
        from datetime import datetime
        
        now = datetime.now()
        weekday = now.weekday()
        
        # 計算是第幾周
        first_day_of_month = datetime(now.year, now.month, 1)
        first_weekday = first_day_of_month.weekday()
        week_of_month = ((now.day - 1 + first_weekday) // 7) + 1
        
        # 週一：特定類別模式 (配合公共API)
        if weekday == 0:  # Monday
            return "specific_categories"
        
        # 週二到週四：特定類別模式
        elif weekday in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
            return "specific_categories"
        
        # 週日第1-3周：超大分類模式
        elif weekday == 6 and week_of_month in [1, 2, 3]:  # Sunday, weeks 1-3
            return "mega_categories"
        
        # 其他情況（不應該執行）
        else:
            return "none"

    def collect_all_stations(self) -> Dict:
        """收集所有來源的電台"""
        self.logger.info("🚀 開始多源電台收集...")
        
        all_stations = []
        collection_stats = {}
        
        # 獲取今天的收集模式
        tunein_mode = self.get_tunein_collection_mode()
        
        # 1. 手動高品質電台 - 每天都收集
        try:
            self.logger.info("👑 收集手動高品質電台...")
            start_time = time.time()
            manual_stations = self.add_manual_premium_stations()
            all_stations.extend(manual_stations)
            
            collection_stats['manual'] = {
                'stations_found': len(manual_stations),
                'time_seconds': time.time() - start_time,
                'success': True
            }
            
        except Exception as e:
            collection_stats['manual'] = {
                'stations_found': 0,
                'time_seconds': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
            self.logger.error(f"❌ 手動電台收集失敗: {e}")
        
        # 2. Radio Browser 收集器 - 每天執行（電台數不多）
        try:
            self.logger.info("🌐 執行 Radio Browser 收集器...")
            start_time = time.time()
            
            radio_browser_collector = RadioBrowserCollector()
            radio_browser_stations = radio_browser_collector.collect_from_radio_browser()
            all_stations.extend(radio_browser_stations)
            
            collection_stats['radio_browser'] = {
                'stations_found': len(radio_browser_stations),
                'time_seconds': time.time() - start_time,
                'success': True
            }
            
        except Exception as e:
            collection_stats['radio_browser'] = {
                'stations_found': 0,
                'time_seconds': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
            self.logger.error(f"❌ Radio Browser 收集失敗: {e}")
        
        # 3. TuneIn 收集器 - 根據排程執行
        if self.should_run_tunein_today():
            try:
                mode_description = {
                    'specific_categories': '特定類別',
                    'mega_categories': '超大分類',
                    'none': '無'
                }
                
                self.logger.info(f"📻 使用 TuneIn 收集器 ({mode_description.get(tunein_mode, tunein_mode)})...")
                start_time = time.time()
                
                tunein_collector = TuneInCollector()
                # 傳遞收集模式給 TuneIn 收集器
                tunein_stations = tunein_collector.collect_from_tunein(mode=tunein_mode)
                all_stations.extend(tunein_stations)
                
                collection_stats['tunein'] = {
                    'stations_found': len(tunein_stations),
                    'time_seconds': time.time() - start_time,
                    'success': True,
                    'mode': tunein_mode
                }
                
            except Exception as e:
                collection_stats['tunein'] = {
                    'stations_found': 0,
                    'time_seconds': 0,
                    'success': False,
                    'error': str(e),
                    'mode': tunein_mode
                }
                self.logger.error(f"❌ TuneIn 收集失敗: {e}")
        else:
            self.logger.info("⏸️ TuneIn 今日不執行，跳過收集")
            collection_stats['tunein'] = {
                'stations_found': 0,
                'time_seconds': 0,
                'success': True,
                'skipped': True,
                'reason': 'not_scheduled_today'
            }
        
        # 按優先級去重處理
        self.logger.info("🔄 開始按優先級去重處理...")
        self.logger.info("📋 去重優先級: 手動高品質電台 >> TuneIn >> Radio Browser API")
        unique_stations = self.deduplicate_stations(all_stations)
        
        self.logger.info(f"🎯 收集完成: 原始 {len(all_stations)} 個，去重後 {len(unique_stations)} 個電台")
        
        return {
            'stations': unique_stations,
            'stats': collection_stats,
            'total_found': len(all_stations),
            'total_unique': len(unique_stations),
            'collection_time': datetime.now().isoformat()
        }

    def deduplicate_stations(self, stations: List[Dict]) -> List[Dict]:
        """電台去重處理 - 按優先級保留：高品質電台 >> TuneIn >> 公共API"""
        # 定義優先級
        priority_map = {
            'manual': 1,          # 手動高品質電台 - 最高優先級
            'tunein': 2,          # TuneIn 收集器 - 中等優先級  
            'radio_browser': 3,   # Radio Browser API - 較低優先級
        }
        
        # 按優先級排序 - 優先級數字越小越優先
        stations_sorted = sorted(stations, key=lambda x: priority_map.get(x.get('source_api', ''), 999))
        
        seen = set()
        unique_stations = []
        duplicate_count = 0
        
        for station in stations_sorted:
            if not station.get('url'):
                continue
                
            # 使用名稱和URL的組合作為唯一標識
            name = station.get('name', '').lower().strip()
            url = station.get('url', '').strip()
            key = (name, url)
            
            # 如果是重複的電台
            if key in seen:
                duplicate_count += 1
                source = station.get('source_api', 'unknown')
                existing_station = next((s for s in unique_stations if (s.get('name', '').lower().strip(), s.get('url', '').strip()) == key), None)
                existing_source = existing_station.get('source_api', 'unknown') if existing_station else 'unknown'
                
                self.logger.debug(f"🔄 重複電台已跳過: {name} ({source} -> 保留 {existing_source})")
                continue
            
            seen.add(key)
            unique_stations.append(station)
        
        self.logger.info(f"🎯 去重完成: 跳過 {duplicate_count} 個重複電台，保留 {len(unique_stations)} 個唯一電台")
        
        # 按來源統計去重後的結果
        source_count = {}
        for station in unique_stations:
            source = station.get('source_api', 'unknown')
            source_count[source] = source_count.get(source, 0) + 1
        
        self.logger.info(f"📊 去重後按來源分佈: {source_count}")
        
        return unique_stations

    def get_sync_key(self, station: Dict) -> str:
        """根據電台資訊生成同步分組 key，用於精確的同步範圍控制"""
        source_api = station.get('source_api', '')
        
        if source_api == 'tunein':
            # TuneIn 根據 metadata 中的類別資訊生成同步 key
            try:
                metadata = json.loads(station.get('metadata', '{}'))
                category = metadata.get('category', 'unknown')
                subcategory = metadata.get('subcategory', 'unknown')
                return f"tunein_{category}_{subcategory}"
            except (json.JSONDecodeError, TypeError):
                return f"tunein_unknown"
        
        # 其他來源直接使用 source_api
        return source_api

    def sync_stations_to_db(self, stations_data: Dict):
        """智能同步電台到資料庫 - 基於類別階層進行精確同步"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stations = stations_data['stations']
        stats = stations_data['stats']
        
        # 統計變數
        added_count = 0
        updated_count = 0
        deleted_count = 0
        
        self.logger.info("🔄 開始智能同步資料庫...")
        
        # 1. 定義需要完整同步（包括刪除）的來源類型
        FULL_SYNC_SOURCE_PATTERNS = {
            'radio_browser',     # 公共 API - 全範圍同步
            'tunein_',          # TuneIn 類別 - 按子類別同步 (前綴匹配)
        }
        
        # 2. 按同步分組整理電台和統計
        executed_sync_groups = {}      # 所有執行的同步分組
        full_sync_groups = set()       # 需要完整同步的分組
        
        # 整理本次收集的電台按同步分組
        stations_by_sync_group = {}
        for station in stations:
            sync_key = self.get_sync_key(station)
            if sync_key not in stations_by_sync_group:
                stations_by_sync_group[sync_key] = []
            stations_by_sync_group[sync_key].append(station)
        
        # 分析執行狀態和同步策略
        for source_api, source_stats in stats.items():
            if source_stats.get('success', False) and not source_stats.get('skipped', False):
                # 根據 source_api 找到對應的同步分組
                source_sync_groups = []
                for sync_key in stations_by_sync_group.keys():
                    if (source_api == 'radio_browser' and sync_key == 'radio_browser') or \
                       (source_api == 'tunein' and sync_key.startswith('tunein_')) or \
                       (source_api == 'manual' and sync_key == 'manual'):
                        source_sync_groups.append(sync_key)
                
                for sync_key in source_sync_groups:
                    executed_sync_groups[sync_key] = source_stats
                    
                    # 判斷是否需要完整同步
                    needs_full_sync = False
                    for pattern in FULL_SYNC_SOURCE_PATTERNS:
                        if sync_key == pattern or sync_key.startswith(pattern):
                            needs_full_sync = True
                            break
                    
                    if needs_full_sync:
                        full_sync_groups.add(sync_key)
                        self.logger.info(f"✅ {sync_key} 本次執行，將進行完整同步（增刪改）")
                    else:
                        self.logger.info(f"✅ {sync_key} 本次執行，僅進行新增/更新同步")
            
            elif source_stats.get('skipped', False):
                self.logger.info(f"⏸️ {source_api} 本次跳過，保留資料庫中的資料")
            else:
                self.logger.warning(f"❌ {source_api} 執行失敗，保留資料庫中的資料")
        
        if not executed_sync_groups:
            self.logger.warning("⚠️ 沒有成功執行的收集器，跳過資料庫同步")
            return {'added': 0, 'updated': 0, 'deleted': 0, 'total_operations': 0}
        
        # 3. 獲取資料庫中需要完整同步分組的現有電台
        current_db_stations = {}
        for sync_key in full_sync_groups:
            if sync_key == 'radio_browser':
                # 公共 API - 直接查詢
                cursor.execute('''
                    SELECT uuid, name, url FROM radio_stations 
                    WHERE source_api = ?
                ''', ('radio_browser',))
            elif sync_key.startswith('tunein_'):
                # TuneIn 子類別 - 根據 metadata 查詢
                parts = sync_key.split('_')
                if len(parts) >= 3:
                    category = parts[1]
                    subcategory = parts[2]
                    cursor.execute('''
                        SELECT uuid, name, url FROM radio_stations 
                        WHERE source_api = 'tunein' 
                        AND metadata LIKE ? 
                        AND metadata LIKE ?
                    ''', (f'%"category": "{category}"%', f'%"subcategory": "{subcategory}"%'))
                else:
                    cursor.execute('''
                        SELECT uuid, name, url FROM radio_stations 
                        WHERE source_api = 'tunein'
                    ''')
            
            current_db_stations[sync_key] = {
                (row[1].lower().strip(), row[2].strip()): row[0]  # (name, url): uuid
                for row in cursor.fetchall()
            }
            self.logger.debug(f"📊 資料庫中 {sync_key} 現有電台: {len(current_db_stations[sync_key])} 個（將參與刪除比對）")
        
        # 4. 處理新收集的電台 - 新增或更新
        new_station_keys = {}  # 按同步分組記錄新電台
        for sync_key in executed_sync_groups.keys():
            new_station_keys[sync_key] = set()
        
        for station in stations:
            sync_key = self.get_sync_key(station)
            
            # 只處理本次執行的同步分組
            if sync_key not in executed_sync_groups:
                continue
                
            name = station.get('name', '').lower().strip()
            url = station.get('url', '').strip()
            station_key = (name, url)
            
            # 記錄新電台的key（用於後續刪除比對）
            if sync_key in full_sync_groups:
                new_station_keys[sync_key].add(station_key)
            
            try:
                # 檢查是否已存在（根據同步分組的查詢邏輯）
                source_api = station.get('source_api', '')
                if source_api == 'tunein':
                    # TuneIn 需要檢查 metadata 匹配
                    try:
                        metadata = json.loads(station.get('metadata', '{}'))
                        category = metadata.get('category', 'unknown')
                        subcategory = metadata.get('subcategory', 'unknown')
                        cursor.execute('''
                            SELECT id FROM radio_stations 
                            WHERE source_api = ? AND name = ? AND url = ?
                            AND metadata LIKE ? AND metadata LIKE ?
                        ''', (source_api, station.get('name', ''), url,
                              f'%"category": "{category}"%', f'%"subcategory": "{subcategory}"%'))
                    except (json.JSONDecodeError, TypeError):
                        cursor.execute('''
                            SELECT id FROM radio_stations 
                            WHERE source_api = ? AND name = ? AND url = ?
                        ''', (source_api, station.get('name', ''), url))
                else:
                    # 其他來源直接查詢
                    cursor.execute('''
                        SELECT id FROM radio_stations 
                        WHERE source_api = ? AND name = ? AND url = ?
                    ''', (source_api, station.get('name', ''), url))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新現有電台
                    cursor.execute('''
                        UPDATE radio_stations SET
                        homepage = ?, favicon = ?, tags = ?, country = ?, language = ?,
                        codec = ?, bitrate = ?, source_type = ?, metadata = ?,
                        collection_date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        station.get('homepage', ''),
                        station.get('favicon', ''),
                        station.get('tags', ''),
                        station.get('country', ''),
                        station.get('language', ''),
                        station.get('codec', ''),
                        station.get('bitrate', 0),
                        station.get('source_type', ''),
                        station.get('metadata', '{}'),
                        existing[0]
                    ))
                    updated_count += 1
                    self.logger.debug(f"🔄 更新電台: {station.get('name', '')} ({sync_key})")
                else:
                    # 新增電台
                    cursor.execute('''
                        INSERT INTO radio_stations 
                        (uuid, name, url, homepage, favicon, tags, country, language, 
                         codec, bitrate, source_api, source_type, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        station.get('uuid', ''),
                        station.get('name', ''),
                        station.get('url', ''),
                        station.get('homepage', ''),
                        station.get('favicon', ''),
                        station.get('tags', ''),
                        station.get('country', ''),
                        station.get('language', ''),
                        station.get('codec', ''),
                        station.get('bitrate', 0),
                        station.get('source_api', ''),
                        station.get('source_type', ''),
                        station.get('metadata', '{}')
                    ))
                    added_count += 1
                    self.logger.debug(f"➕ 新增電台: {station.get('name', '')} ({sync_key})")
                    
            except sqlite3.Error as e:
                self.logger.warning(f"⚠️ 處理電台失敗: {station.get('name', '')} - {e}")
        
        # 5. 刪除消失的電台（只針對需要完整同步的分組）
        for sync_key, db_stations in current_db_stations.items():
            for station_key, uuid in db_stations.items():
                # 如果資料庫中的電台在本次收集中沒有出現，就刪除
                if station_key not in new_station_keys.get(sync_key, set()):
                    try:
                        if sync_key == 'radio_browser':
                            cursor.execute('''
                                DELETE FROM radio_stations 
                                WHERE source_api = ? AND name = ? AND url = ?
                            ''', ('radio_browser', station_key[0], station_key[1]))
                        elif sync_key.startswith('tunein_'):
                            parts = sync_key.split('_')
                            if len(parts) >= 3:
                                category = parts[1]
                                subcategory = parts[2]
                                cursor.execute('''
                                    DELETE FROM radio_stations 
                                    WHERE source_api = 'tunein' AND name = ? AND url = ?
                                    AND metadata LIKE ? AND metadata LIKE ?
                                ''', (station_key[0], station_key[1],
                                      f'%"category": "{category}"%', f'%"subcategory": "{subcategory}"%'))
                            else:
                                cursor.execute('''
                                    DELETE FROM radio_stations 
                                    WHERE source_api = 'tunein' AND name = ? AND url = ?
                                ''', (station_key[0], station_key[1]))
                        
                        deleted_count += 1
                        self.logger.info(f"🗑️ 刪除消失的電台: {station_key[0]} ({sync_key})")
                    except sqlite3.Error as e:
                        self.logger.warning(f"⚠️ 刪除電台失敗: {station_key[0]} - {e}")
        
        conn.commit()
        conn.close()
        
        # 6. 記錄同步統計
        self.logger.info("📊 資料庫同步完成:")
        self.logger.info(f"   🎯 執行分組: {', '.join(executed_sync_groups.keys())}")
        self.logger.info(f"   🔄 完整同步分組: {', '.join(full_sync_groups)} (包含刪除)")
        self.logger.info(f"   📝 僅新增/更新分組: {', '.join(set(executed_sync_groups.keys()) - full_sync_groups)}")
        self.logger.info(f"   ➕ 新增: {added_count} 個電台")
        self.logger.info(f"   🔄 更新: {updated_count} 個電台")
        self.logger.info(f"   🗑️ 刪除: {deleted_count} 個電台")
        
        return {
            'added': added_count,
            'updated': updated_count,
            'deleted': deleted_count,
            'total_operations': added_count + updated_count + deleted_count,
            'executed_sync_groups': list(executed_sync_groups.keys()),
            'full_sync_groups': list(full_sync_groups),
            'update_only_groups': list(set(executed_sync_groups.keys()) - full_sync_groups)
        }

    def save_stations_to_db(self, stations_data: Dict):
        """保存電台到資料庫 - 保留舊方法以兼容性，但建議使用 sync_stations_to_db"""
        self.logger.info("⚠️ 使用舊版保存方法，建議使用 sync_stations_to_db 進行智能同步")
        return self.sync_stations_to_db(stations_data)

    def get_stations_summary(self) -> Dict:
        """獲取電台統計摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 總數統計
        cursor.execute('SELECT COUNT(*) FROM radio_stations')
        total_count = cursor.fetchone()[0]
        
        # 按來源統計
        cursor.execute('''
            SELECT source_api, COUNT(*) 
            FROM radio_stations 
            GROUP BY source_api 
            ORDER BY COUNT(*) DESC
        ''')
        by_source = cursor.fetchall()
        
        # 按國家統計
        cursor.execute('''
            SELECT country, COUNT(*) 
            FROM radio_stations 
            WHERE country != '' 
            GROUP BY country 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        by_country = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_stations': total_count,
            'by_source': dict(by_source),
            'by_country': dict(by_country),
            'summary_time': datetime.now().isoformat()
        }


def main():
    """主函數 - 簡化使用方式"""
    # 簡化的使用方式
    collector = MultiSourceRadioCollector()
    
    print("🎵 多源電台收集器 - 簡化版")
    print("=" * 50)
    
    # 一鍵收集所有電台
    result = collector.collect_all_stations()
    
    # 顯示本次收集統計
    print("\n📊 本次收集統計:")
    print(f"📻 本次收集總數: {result['total_found']}")
    print(f"🎯 去重後總數: {result['total_unique']}")
    
    # 按來源顯示本次收集數量
    print(f"📡 本次按來源分佈:")
    for source, stats in result['stats'].items():
        if stats.get('skipped'):
            print(f"   {source}: 0 個 (今日跳過 - {stats.get('reason', 'unknown')})")
        else:
            print(f"   {source}: {stats['stations_found']} 個")
    
    # 智能同步到資料庫
    if result['total_unique'] > 0 or any(not stats.get('skipped', False) for stats in result['stats'].values()):
        sync_result = collector.sync_stations_to_db(result)
        
        print(f"\n🔄 資料庫同步結果:")
        print(f"   🎯 執行分組: {', '.join(sync_result.get('executed_sync_groups', []))}")
        print(f"   🔄 完整同步分組: {', '.join(sync_result.get('full_sync_groups', []))} (包含刪除)")
        print(f"   📝 僅新增/更新分組: {', '.join(sync_result.get('update_only_groups', []))}")
        print(f"   ➕ 新增: {sync_result['added']} 個電台")
        print(f"   🔄 更新: {sync_result['updated']} 個電台") 
        print(f"   🗑️ 刪除: {sync_result['deleted']} 個電台")
        print(f"   📊 總操作: {sync_result['total_operations']} 次")
        
        # 顯示同步後的資料庫統計
        summary = collector.get_stations_summary()
        print(f"\n💾 同步後資料庫統計:")
        print(f"📻 資料庫總電台數量: {summary['total_stations']}")
        print(f"📡 資料庫按來源分佈: {summary['by_source']}")
        print(f"🌍 資料庫按國家分佈: {dict(list(summary['by_country'].items())[:5])}..." if len(summary['by_country']) > 5 else summary['by_country'])
    else:
        print(f"\n⏸️ 所有收集器都跳過，不進行資料庫同步")
    
    print(f"\n✅ 電台收集完成！資料庫: {collector.db_path}")

        # 新增：自動推送到 GitHub
    import subprocess
    try:
        print(f"\n 推送資料到 GitHub...") 
        result = subprocess.run(['./update_github.sh'], 
                              capture_output=True, text=True, check=True)
        print("✅ GitHub 推送成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ GitHub 推送失敗: {e}")
        print(f"錯誤輸出: {e.stderr}")


if __name__ == "__main__":
    main()