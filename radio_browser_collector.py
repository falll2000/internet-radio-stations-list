#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radio Browser API 電台收集器
從 Radio Browser 公開 API 收集電台數據
"""
import requests
import json
import time
import logging
from datetime import datetime
from typing import List, Dict


class RadioBrowserCollector:
    """Radio Browser API 電台收集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Taiwan Radio App/1.0 (Personal Use)'
        })
        
        # 設定日誌
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # API 設定
        self.base_url = 'https://all.api.radio-browser.info'
        self.rate_limit = 1.0
    
    def collect_from_radio_browser(self) -> List[Dict]:
        """從 Radio Browser API 收集電台"""
        self.logger.info("🌐 從 Radio Browser API 收集電台...")
        stations = []
        
        try:
            # 收集台灣、中文、熱門電台
            endpoints = [
                ('taiwan', '/json/stations/bycountry/taiwan'),
                ('chinese', '/json/stations/bylanguage/chinese'),
                ('classical', '/json/stations/bytag/classical'),
                ('pop', '/json/stations/bytag/pop'),
                ('news', '/json/stations/bytag/news'),
                ('jazz', '/json/stations/bytag/jazz'),
                ('rock', '/json/stations/bytag/rock')
            ]
            
            for category, endpoint in endpoints:
                time.sleep(self.rate_limit)
                url = f"{self.base_url}{endpoint}"
                
                try:
                    self.logger.info(f"🔍 收集 Radio Browser 分類: {category}")
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # 限制數量避免過多
                    if category in ['classical', 'pop', 'jazz', 'rock']:
                        data = data[:50]
                    elif category == 'news':
                        data = data[:30]
                    
                    category_count = 0
                    for station in data:
                        station_data = self._create_station_from_radio_browser(station, category)
                        if station_data:
                            stations.append(station_data)
                            category_count += 1
                    
                    self.logger.info(f"📻 Radio Browser {category}: 收集到 {category_count} 個電台")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Radio Browser {category} 收集失敗: {e}")
            
            self.logger.info(f"✅ Radio Browser: 總共收集到 {len(stations)} 個電台")
            
        except Exception as e:
            self.logger.error(f"❌ Radio Browser 收集失敗: {e}")
        
        return stations
    
    def _create_station_from_radio_browser(self, station_data: dict, category: str) -> dict:
        """從 Radio Browser 數據創建電台記錄"""
        # 基本驗證
        if not station_data.get('name') or not station_data.get('url'):
            return None
        
        # 過濾無效的 URL
        url = station_data.get('url', '').strip()
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        # 構建電台數據
        return {
            'uuid': station_data.get('stationuuid', ''),
            'name': station_data.get('name', '').strip(),
            'url': url,
            'homepage': station_data.get('homepage', ''),
            'favicon': station_data.get('favicon', ''),
            'tags': f"radio_browser,{category},{station_data.get('tags', '')}",
            'country': station_data.get('country', ''),
            'language': self._normalize_language(station_data.get('language', '')),
            'codec': station_data.get('codec', 'mp3'),
            'bitrate': self._safe_int(station_data.get('bitrate', 0)),
            'source_api': 'radio_browser',
            'source_type': 'public_api',
            'metadata': json.dumps({
                'votes': station_data.get('votes', 0),
                'clickcount': station_data.get('clickcount', 0),
                'countrycode': station_data.get('countrycode', ''),
                'state': station_data.get('state', ''),
                'changeuuid': station_data.get('changeuuid', ''),
                'lastcheckok': station_data.get('lastcheckok', 0),
                'lastchecktime': station_data.get('lastchecktime', ''),
                'category': category
            })
        }
    
    def _normalize_language(self, language: str) -> str:
        """標準化語言代碼"""
        if not language:
            return 'unknown'
        
        language = language.lower().strip()
        
        # 語言映射
        language_mapping = {
            'chinese': 'chinese',
            'mandarin': 'chinese',
            'cantonese': 'chinese',
            'zh': 'chinese',
            'zh-cn': 'chinese',
            'zh-tw': 'chinese',
            'english': 'english',
            'en': 'english',
            'japanese': 'japanese',
            'ja': 'japanese',
            'korean': 'korean',
            'ko': 'korean',
            'french': 'french',
            'fr': 'french',
            'german': 'german',
            'de': 'german',
            'spanish': 'spanish',
            'es': 'spanish'
        }
        
        return language_mapping.get(language, language)
    
    def _safe_int(self, value) -> int:
        """安全的整數轉換"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def get_available_countries(self) -> List[Dict]:
        """獲取可用的國家列表"""
        try:
            url = f"{self.base_url}/json/countries"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"❌ 獲取國家列表失敗: {e}")
            return []
    
    def get_available_languages(self) -> List[Dict]:
        """獲取可用的語言列表"""
        try:
            url = f"{self.base_url}/json/languages"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"❌ 獲取語言列表失敗: {e}")
            return []
    
    def get_available_tags(self) -> List[Dict]:
        """獲取可用的標籤列表"""
        try:
            url = f"{self.base_url}/json/tags"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"❌ 獲取標籤列表失敗: {e}")
            return []
    
    def search_stations_by_name(self, name: str, limit: int = 50) -> List[Dict]:
        """按名稱搜索電台"""
        try:
            url = f"{self.base_url}/json/stations/byname/{name}"
            params = {'limit': limit}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            stations = []
            for station in response.json():
                station_data = self._create_station_from_radio_browser(station, 'search')
                if station_data:
                    stations.append(station_data)
            
            return stations
        except Exception as e:
            self.logger.error(f"❌ 按名稱搜索失敗: {e}")
            return []
    
    def get_top_stations_by_votes(self, limit: int = 100) -> List[Dict]:
        """獲取按投票數排序的熱門電台"""
        try:
            url = f"{self.base_url}/json/stations/topvote"
            params = {'limit': limit}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            stations = []
            for station in response.json():
                station_data = self._create_station_from_radio_browser(station, 'top_voted')
                if station_data:
                    stations.append(station_data)
            
            return stations
        except Exception as e:
            self.logger.error(f"❌ 獲取熱門電台失敗: {e}")
            return []
    
    def get_top_stations_by_clicks(self, limit: int = 100) -> List[Dict]:
        """獲取按點擊數排序的熱門電台"""
        try:
            url = f"{self.base_url}/json/stations/topclick"
            params = {'limit': limit}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            stations = []
            for station in response.json():
                station_data = self._create_station_from_radio_browser(station, 'top_clicked')
                if station_data:
                    stations.append(station_data)
            
            return stations
        except Exception as e:
            self.logger.error(f"❌ 獲取熱門電台失敗: {e}")
            return []


# 使用示例和測試
if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🌐 Radio Browser 收集器測試")
    print("=" * 50)
    
    # 創建收集器實例
    collector = RadioBrowserCollector()
    
    # 測試收集功能
    stations = collector.collect_from_radio_browser()
    
    print(f"\n📊 收集結果:")
    print(f"📻 總電台數: {len(stations)}")
    
    if stations:
        print(f"\n🎵 電台樣本 (前5個):")
        for i, station in enumerate(stations[:5], 1):
            print(f"   {i}. {station['name']} [{station['language']}, {station['country']}]")
            print(f"      URL: {station['url']}")
    
    # 測試其他功能
    print(f"\n🔍 測試其他功能:")
    
    # 獲取熱門電台
    top_voted = collector.get_top_stations_by_votes(10)
    print(f"📈 熱門電台 (按投票): {len(top_voted)} 個")
    
    # 搜索功能
    search_results = collector.search_stations_by_name("BBC", 5)
    print(f"🔎 搜索 'BBC': {len(search_results)} 個結果")
    
    print(f"\n✅ Radio Browser 收集器測試完成！")