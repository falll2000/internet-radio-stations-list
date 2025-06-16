"""
TuneIn 電台收集器
智能週期調度系統，按日期執行不同分類的電台收集
"""

import xml.etree.ElementTree as ET
import hashlib
import random
import json
import time
import requests
from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Set

# 導入日誌管理器
from tunein_logger import TuneInLogger


class TuneInCollector:
    """TuneIn 電台收集器 - 智能週期調度系統"""
    
    def __init__(self):
        # 初始化日誌管理器
        self.tunein_logger = TuneInLogger()
        
        # 請求統計
        self.request_count = 0
        self.failed_requests = 0
        
        # 初始化 HTTP 會話
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_from_tunein(self) -> List[Dict]:
        """從 TuneIn 收集電台 - 智能週期調度系統"""
        # 啟動時清理舊日誌
        self.tunein_logger.cleanup_old_logs()
        self.tunein_logger.print_log_statistics()
        
        print("📻 從 TuneIn 收集電台...")
        
        # 獲取當前日期信息
        now = datetime.now()
        today = now.day
        weekday = now.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 6=Sunday
        is_sunday = weekday == 6
        
        # 計算是第幾周
        first_day_of_month = datetime(now.year, now.month, 1)
        first_weekday = first_day_of_month.weekday()
        week_of_month = ((today - 1 + first_weekday) // 7) + 1
        
        all_stations = []
        
        try:
            # 超大分類（每月特定週日執行）
            mega_categories_by_week = {
                1: {'music': 'http://opml.radiotime.com/Browse.ashx?c=music'},        # 第一周週日
                2: {'location': 'http://opml.radiotime.com/Browse.ashx?id=r0'},       # 第二周週日  
                3: {'language': 'http://opml.radiotime.com/Browse.ashx?c=lang'},      # 第三周週日
            }
            
            # 工作日固定組合
            weekday_categories = {
                0: {  # 週一: Talk + Taiwan
                    'talk': 'http://opml.radiotime.com/Browse.ashx?c=talk',
                    'taiwan': 'http://opml.radiotime.com/Browse.ashx?id=r101302',
                },
                1: {  # 週二: Sports + Hong Kong
                    'sports': 'http://opml.radiotime.com/Browse.ashx?c=sports',
                    'hongkong': 'http://opml.radiotime.com/Browse.ashx?id=r101296',
                },
                2: {  # 週三: Podcast + Singapore
                    'podcast': 'http://opml.radiotime.com/Browse.ashx?c=podcast',
                    'singapore': 'http://opml.radiotime.com/Browse.ashx?id=r101297',
                },
                3: {  # 週四: Local
                    'local': 'http://opml.radiotime.com/Browse.ashx?c=local',
                },
            }
            
            # 決定執行策略
            if is_sunday:
                if week_of_month in mega_categories_by_week:
                    categories = mega_categories_by_week[week_of_month]
                    category_type = f"超大分類 (第{week_of_month}周週日)"
                    execution_mode = "mega"
                    print(f"📅 今天是第{week_of_month}周週日，執行{category_type}: {list(categories.keys())}")
                else:
                    # 第4周或第5周週日不執行任何分類
                    print(f"📅 今天是第{week_of_month}周週日，休息日 - 不執行任何分類收集")
                    return []
            elif weekday in weekday_categories:
                categories = weekday_categories[weekday]
                weekday_names = ['週一', '週二', '週三', '週四']
                category_type = f"{weekday_names[weekday]}固定組合"
                execution_mode = "mixed"  # 混合模式（大分類+小分類）
                print(f"📅 今天是{weekday_names[weekday]}，執行{category_type}: {list(categories.keys())}")
            else:
                # 週五、週六不執行
                weekday_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
                print(f"📅 今天是{weekday_names[weekday]}，休息日 - 不執行任何分類收集")
                return []
            
            # 根據執行模式設置參數
            execution_params = self._get_execution_params(execution_mode)
            
            # 處理每個分類
            for category_name, url in categories.items():
                # 開始該分類的日誌記錄
                start_time = datetime.now()
                logger = self.tunein_logger.start_category_logging(category_name, execution_mode)
                
                # 重置統計
                self.request_count = 0
                self.failed_requests = 0
                
                try:
                    # 檢查失敗率
                    if self.failed_requests > execution_params['max_failures']:
                        logger.warning(f"⚠️ 失敗請求過多 ({self.failed_requests})，停止收集")
                        break
                    
                    # 根據分類類型調整延遲（混合模式需要區分大小分類）
                    if execution_mode == "mixed":
                        if category_name in ['talk', 'sports', 'podcast']:
                            # 大分類
                            delay = random.uniform(3.0, 6.0)
                            subcategory_factor = 1.0
                        else:
                            # 小分類
                            delay = random.uniform(1.0, 3.0)
                            subcategory_factor = 1.2
                    else:
                        # 超大分類
                        delay = random.uniform(execution_params['delay_range'][0], execution_params['delay_range'][1])
                        subcategory_factor = execution_params['subcategory_factor']
                    
                    time.sleep(delay)
                    
                    logger.info(f"🔍 收集{category_type}: {category_name} (已發送 {self.request_count} 個請求)")
                    logger.info(f"🌐 URL: {url}")
                    
                    # 重置 visited_urls
                    visited_urls = set()
                    
                    # 執行收集
                    category_stations = self._parse_tunein_opml_recursive_with_schedule(
                        url, category_name, url, 0, visited_urls, execution_mode, subcategory_factor, logger
                    )
                    all_stations.extend(category_stations)
                    
                    logger.info(f"📍 TuneIn {category_type} {category_name}: 收集到 {len(category_stations)} 個電台")
                    
                    # 超大分類需要額外的休息時間
                    if execution_mode == "mega":
                        extra_rest = random.uniform(30.0, 60.0)
                        logger.info(f"😴 超大分類處理完畢，額外休息 {extra_rest:.1f} 秒...")
                        time.sleep(extra_rest)
                    elif execution_mode == "mixed" and category_name in ['talk', 'sports', 'podcast']:
                        # 混合模式中的大分類也需要休息
                        extra_rest = random.uniform(10.0, 20.0)
                        logger.info(f"😴 大分類處理完畢，休息 {extra_rest:.1f} 秒...")
                        time.sleep(extra_rest)
                    
                    # 完成該分類的日誌記錄（添加統計信息）
                    self.tunein_logger.finish_category_logging(
                        category_stations, 
                        self.request_count, 
                        self.failed_requests, 
                        start_time, 
                        execution_mode
                    )
                    
                except Exception as e:
                    self.failed_requests += 1
                    logger.error(f"❌ 分類 {category_name} 收集失敗: {e}")
                    self._handle_request_error(e, category_name, category_type, execution_params, logger)
                    
                    # 即使出錯也要記錄統計
                    self.tunein_logger.finish_category_logging(
                        [], self.request_count, self.failed_requests, start_time, execution_mode
                    )
            
            # 記錄總體統計和下次執行計劃
            print(f"✅ TuneIn {category_type}: 總共收集到 {len(all_stations)} 個電台")
            self._log_next_execution_plan_weekly(now)
            
        except Exception as e:
            print(f"❌ TuneIn 收集失敗: {e}")
        
        return all_stations
    
    def _get_execution_params(self, execution_mode: str) -> dict:
        """根據執行模式獲取參數"""
        params = {
            "mega": {
                "delay_range": (10.0, 20.0),
                "max_failures": 50,
                "subcategory_factor": 2.0,
                "timeout": 45,
                "wait_403": (60.0, 120.0),
                "wait_429": (90.0, 180.0),
            },
            "mixed": {  # 週一到週四的混合模式
                "delay_range": (2.0, 5.0),
                "max_failures": 30,
                "subcategory_factor": 1.2,
                "timeout": 30,
                "wait_403": (20.0, 40.0),
                "wait_429": (30.0, 60.0),
            }
        }
        return params[execution_mode]
    
    def _handle_request_error(self, error, category_name: str, category_type: str, params: dict, logger):
        """統一的錯誤處理"""
        if "403" in str(error) or "Forbidden" in str(error):
            logger.error(f"❌ TuneIn {category_type} {category_name} 被禁止訪問 (403)")
            wait_time = random.uniform(params['wait_403'][0], params['wait_403'][1])
            logger.info(f"😴 遇到訪問限制，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
        elif "429" in str(error) or "Too Many Requests" in str(error):
            logger.error(f"❌ TuneIn {category_type} {category_name} 請求過於頻繁 (429)")
            wait_time = random.uniform(params['wait_429'][0], params['wait_429'][1])
            logger.info(f"😴 請求過於頻繁，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
        else:
            logger.warning(f"⚠️ TuneIn {category_type} {category_name} 收集失敗: {error}")
    
    def _log_next_execution_plan_weekly(self, current_date):
        """記錄每週執行計劃"""
        from datetime import timedelta
        
        # 計算明天的執行計劃
        tomorrow = current_date + timedelta(days=1)
        tomorrow_weekday = tomorrow.weekday()
        
        weekday_plans = {
            0: "週一: Talk + Taiwan",
            1: "週二: Sports + Hong Kong", 
            2: "週三: Podcast + Singapore",
            3: "週四: Local",
            4: "週五: 休息日",
            5: "週六: 休息日",
            6: "週日: 待定 (依第幾周決定)"
        }
        
        if tomorrow_weekday == 6:  # 週日
            # 計算明天是第幾周
            first_day = datetime(tomorrow.year, tomorrow.month, 1)
            first_weekday = first_day.weekday()
            tomorrow_week = ((tomorrow.day - 1 + first_weekday) // 7) + 1
            
            if tomorrow_week == 1:
                next_plan = "週日: 超大分類 Music"
            elif tomorrow_week == 2:
                next_plan = "週日: 超大分類 Location"
            elif tomorrow_week == 3:
                next_plan = "週日: 超大分類 Language"
            else:
                next_plan = "週日: 休息日"
        else:
            next_plan = weekday_plans[tomorrow_weekday]
        
        print(f"💡 明天 ({tomorrow.strftime('%Y-%m-%d')}) 計劃: {next_plan}")
    
    def _parse_tunein_opml_recursive_with_schedule(self, current_url: str, category: str, 
                                                 original_url: str, depth: int = 0, 
                                                 visited_urls: Set[str] = None, 
                                                 execution_mode: str = "mixed", 
                                                 subcategory_factor: float = 1.0,
                                                 logger = None) -> List[Dict]:
        """按調度模式的遞歸解析"""
        stations = []
        params = self._get_execution_params(execution_mode)
        
        # 檢查失敗率
        if self.failed_requests > params['max_failures']:
            if logger:
                logger.debug(f"⚠️ 失敗請求過多，停止深入 (深度 {depth})")
            return stations
        
        if visited_urls is None:
            visited_urls = set()
        
        if current_url in visited_urls:
            if logger:
                logger.debug(f"⚠️ 跳過已訪問的 URL (深度 {depth}): {current_url}")
            return stations
        
        visited_urls.add(current_url)
        
        try:
            # 根據執行模式和深度調整延遲
            if depth > 0:
                if execution_mode == "mega":
                    base_delay = random.uniform(5.0, 12.0)
                    depth_penalty = depth * 0.8
                else:  # mixed
                    # 根據分類類型調整
                    if category and any(big in category.lower() for big in ['talk', 'sports', 'podcast']):
                        base_delay = random.uniform(1.5, 4.0)
                        depth_penalty = depth * 0.3
                    else:
                        base_delay = random.uniform(0.5, 2.0)
                        depth_penalty = depth * 0.2
                
                delay = base_delay + depth_penalty
                time.sleep(delay)
            
            # 記錄請求
            self.request_count += 1
            
            if logger:
                logger.debug(f"📡 {execution_mode.upper()} 請求 #{self.request_count} (深度 {depth}): {current_url}")
            
            # 發送請求
            response = self.session.get(current_url, timeout=params['timeout'])
            response.raise_for_status()
            
            # 解析 OPML
            stations = self._parse_tunein_opml_recursive_with_factor(
                response.text, category, current_url, depth, visited_urls, 
                subcategory_factor, execution_mode, logger
            )
            
        except Exception as e:
            self.failed_requests += 1
            
            if "403" in str(e) or "Forbidden" in str(e):
                if logger:
                    logger.warning(f"⚠️ 請求被禁止 (深度 {depth}): {current_url}")
                return []
            elif "429" in str(e) or "Too Many Requests" in str(e):
                if logger:
                    logger.warning(f"⚠️ 請求過於頻繁 (深度 {depth}): {current_url}")
                wait_time = random.uniform(params['wait_429'][0] * 0.3, params['wait_429'][1] * 0.3)
                time.sleep(wait_time)
                return []
            else:
                if logger:
                    logger.warning(f"⚠️ 請求失敗 (深度 {depth}): {e}")
        
        return stations
    
    def _parse_tunein_opml_recursive_with_factor(self, opml_content: str, category: str, 
                                               current_url: str, depth: int = 0, 
                                               visited_urls: Set[str] = None, 
                                               subcategory_factor: float = 1.0, 
                                               execution_mode: str = "mixed",
                                               logger = None) -> List[Dict]:
        """帶子分類因子的遞歸解析"""
        stations = []
        
        if visited_urls is None:
            visited_urls = set()
        
        if current_url in visited_urls:
            return stations
        
        visited_urls.add(current_url)
        
        try:
            # 清理並解析 XML
            opml_content = opml_content.strip()
            if opml_content.startswith('\ufeff'):
                opml_content = opml_content[1:]
            
            root = ET.fromstring(opml_content)
            
            # 調整調試信息顯示
            show_debug = (depth <= 3) if execution_mode == "mega" else (depth <= 2)
            
            if show_debug and logger:
                logger.info(f"🔍 {execution_mode.upper()} - 分析分類 {category} (深度 {depth})")
            
            # 1. 查找電台
            audio_outlines = root.findall('.//outline[@type="audio"]')
            if audio_outlines:
                for outline in audio_outlines:
                    station = self._create_station_from_outline(outline, category)
                    if station:
                        stations.append(station)
            
            # 2. 處理子分類
            link_outlines = root.findall('.//outline[@type="link"]')
            if link_outlines:
                max_subcategories = self._get_max_subcategories_by_schedule(
                    category, depth, execution_mode, subcategory_factor
                )
                
                for i, link_outline in enumerate(link_outlines[:max_subcategories]):
                    link_url = link_outline.get('URL', '')
                    link_text = link_outline.get('text', '')
                    
                    if not link_url or 'opml.radiotime.com' not in link_url:
                        continue
                    
                    if link_url in visited_urls:
                        continue
                    
                    try:
                        new_visited_urls = visited_urls.copy()
                        sub_stations = self._parse_tunein_opml_recursive_with_schedule(
                            link_url,
                            f"{category}_{link_text.replace(' ', '_').replace('/', '_').replace('&', '_')}",
                            link_url,
                            depth + 1,
                            new_visited_urls,
                            execution_mode,
                            subcategory_factor,
                            logger
                        )
                        stations.extend(sub_stations)
                        
                        if len(sub_stations) > 0 and logger:
                            logger.info(f"✅ 子分類 {link_text} [深度 {depth+1}]: 收集到 {len(sub_stations)} 個電台")
                            
                    except Exception as e:
                        if show_debug and logger:
                            logger.warning(f"⚠️ 子分類失敗 {link_text}: {e}")
            
        except Exception as e:
            if logger:
                logger.error(f"❌ 解析錯誤 (分類: {category}, 深度: {depth}): {e}")
        
        return stations
    
    def _get_max_subcategories_by_schedule(self, category: str, depth: int, 
                                         execution_mode: str, factor: float = 1.0) -> int:
        """根據週期調度模式調整子分類處理數量"""
        
        # 基礎配額
        base_quotas = {
            "mega": {
                'music': [50, 40, 30, 25, 20, 15],
                'location': [45, 35, 28, 22, 18, 12],
                'language': [60, 50, 40, 30, 25, 20],
            },
            "mixed": {
                # 大分類
                'talk': [25, 20, 15, 12, 10, 8],
                'sports': [20, 15, 12, 10, 8, 6],
                'podcast': [20, 15, 12, 10, 8, 6],
                # 小分類
                'local': [15, 12, 10, 8, 6, 5],
                'taiwan': [25, 20, 15, 12, 10, 8],
                'hongkong': [25, 20, 15, 12, 10, 8],
                'singapore': [25, 20, 15, 12, 10, 8],
            }
        }
        
        # 獲取配額
        mode_quotas = base_quotas.get(execution_mode, {})
        quotas = mode_quotas.get(category, [10, 8, 6, 5, 4, 3])
        
        depth_index = min(depth, len(quotas) - 1)
        base_amount = quotas[depth_index]
        
        # 應用因子
        final_amount = int(base_amount * factor)
        
        return max(final_amount, 1)
    
    def _create_station_from_outline(self, outline, category: str, force_create: bool = False) -> dict:
        """從 outline 元素創建電台數據"""
        attrs = outline.attrib
        name = attrs.get('text', '')
        url = attrs.get('URL', '')
        
        # 驗證必要字段
        if not name or not url:
            return None
        
        # 只處理有效的電台 URL（除非強制創建）
        if not force_create and not any(keyword in url.lower() for keyword in ['tune.ashx', 'stream', 'radio']):
            return None
        
        # 生成唯一 ID
        station_id = attrs.get('guide_id', '') or f"tunein_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        # 構建電台數據
        station_data = {
            'uuid': station_id,
            'name': name,
            'url': url,
            'homepage': '',
            'favicon': attrs.get('image', ''),
            'tags': f"tunein,{category}",
            'country': self._extract_country_from_text(name, attrs.get('subtext', '')),
            'language': self._extract_language_from_tunein_text(name, attrs.get('subtext', '')),
            'codec': attrs.get('formats', 'mp3').split(',')[0],
            'bitrate': int(attrs.get('bitrate', 128)),
            'source_api': 'tunein',
            'source_type': 'opml_api',
            'subtext': attrs.get('subtext', ''),
            'genre_id': attrs.get('genre_id', ''),
            'reliability': attrs.get('reliability', ''),
            'guide_id': attrs.get('guide_id', ''),
            'metadata': json.dumps(attrs)
        }
        
        return station_data
    
    def _extract_language_from_tunein_text(self, name: str, subtext: str) -> str:
        """從 TuneIn 電台名稱和描述中提取語言信息"""
        text = f"{name} {subtext}".lower()
        
        if any(keyword in text for keyword in ['chinese', '中文', '台語', '國語', '粵語']):
            return 'chinese'
        elif 'english' in text or any(keyword in name for keyword in ['BBC', 'CNN', 'NPR']):
            return 'english'
        elif any(keyword in text for keyword in ['japanese', '日本', 'japan']):
            return 'japanese'
        elif any(keyword in text for keyword in ['korean', '韓國', 'korea']):
            return 'korean'
        elif 'french' in text or 'france' in text:
            return 'french'
        elif any('\u4e00' <= char <= '\u9fff' for char in name):
            return 'chinese'
        else:
            return 'unknown'
    
    def _extract_country_from_text(self, name: str, subtext: str) -> str:
        """從電台名稱和描述中提取國家信息"""
        text = f"{name} {subtext}".lower()
        
        if any(keyword in text for keyword in ['taiwan', '台灣', '台北', '高雄']):
            return 'Taiwan'
        elif any(keyword in text for keyword in ['hong kong', '香港', 'hk']):
            return 'Hong Kong'
        elif any(keyword in text for keyword in ['singapore', '新加坡', 'sg']):
            return 'Singapore'
        elif any(keyword in text for keyword in ['china', '中國', 'beijing', '北京']):
            return 'China'
        elif any(keyword in text for keyword in ['usa', 'america', 'united states']):
            return 'USA'
        elif any(keyword in text for keyword in ['uk', 'britain', 'england']):
            return 'UK'
        else:
            return 'Unknown'


# 主程序入口
if __name__ == "__main__":
    try:
        # 創建收集器實例
        collector = TuneInCollector()
        
        # 執行收集
        print("🚀 開始 TuneIn 電台收集...")
        stations = collector.collect_from_tunein()
        
        print(f"\n🎉 收集完成！")
        print(f"📻 總共收集到 {len(stations)} 個電台")
        
        if stations:
            print(f"🎵 電台樣本:")
            for i, station in enumerate(stations[:3], 1):
                print(f"   {i}. {station['name']} [{station['language']}, {station['country']}]")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷收集")
    except Exception as e:
        print(f"\n❌ 收集過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 TuneIn 收集器結束")