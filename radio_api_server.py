#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化電台API服務器
整合現有收集器模組
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time
import schedule

class RadioAPI:
    def __init__(self, db_path: str = "expanded_radio_stations.db"):
        self.db_path = db_path
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 設定日誌
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 註冊路由
        self.register_routes()
        
        # 設定定時任務
        self.setup_scheduler()

    def setup_scheduler(self):
        """設定定時任務 - 每日早上8點更新電台"""
        schedule.every().day.at("08:00").do(self.update_stations_background)
        
        # 在背景執行排程器
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("⏰ 定時任務已設定：每日早上8點自動更新電台")

    def register_routes(self):
        """註冊所有API路由"""
        
        @self.app.route('/api/stations', methods=['GET'])
        def get_stations():
            """獲取電台列表（支援篩選和分頁）"""
            try:
                # 獲取查詢參數
                country = request.args.get('country', '')
                language = request.args.get('language', '')
                search = request.args.get('search', '')
                page = int(request.args.get('page', 1))
                limit = min(int(request.args.get('limit', 50)), 200)
                
                stations = self.get_filtered_stations(
                    country=country,
                    language=language,
                    search=search,
                    page=page,
                    limit=limit
                )
                
                return jsonify({
                    'success': True,
                    'stations': stations['data'],
                    'pagination': stations['pagination'],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"獲取電台列表失敗: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/stations/search', methods=['GET'])
        def search_stations():
            """搜尋電台"""
            try:
                query = request.args.get('q', '').strip()
                if not query:
                    return jsonify({
                        'success': False,
                        'error': '搜尋關鍵字不能為空'
                    }), 400
                
                results = self.search_stations_by_query(query)
                
                return jsonify({
                    'success': True,
                    'query': query,
                    'results': results,
                    'total_found': len(results)
                })
                
            except Exception as e:
                self.logger.error(f"搜尋電台失敗: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/stations/featured', methods=['GET'])
        def get_featured_stations():
            """獲取精選電台"""
            try:
                featured = self.get_featured_stations()
                return jsonify({
                    'success': True,
                    'featured_stations': featured
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """獲取電台統計資訊"""
            try:
                stats = self.get_database_stats()
                return jsonify({
                    'success': True,
                    'statistics': stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/update', methods=['POST'])
        def trigger_update():
            """手動觸發電台更新"""
            try:
                threading.Thread(target=self.update_stations_background).start()
                return jsonify({
                    'success': True,
                    'message': '電台更新已開始執行'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康檢查"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM radio_stations')
                count = cursor.fetchone()[0]
                conn.close()
                
                return jsonify({
                    'success': True,
                    'status': 'healthy',
                    'total_stations': count
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'status': 'unhealthy',
                    'error': str(e)
                }), 500

    def get_filtered_stations(self, country='', language='', search='', page=1, limit=50):
        """獲取篩選後的電台列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if country:
            conditions.append('country LIKE ?')
            params.append(f'%{country}%')
        
        if language:
            conditions.append('language LIKE ?')
            params.append(f'%{language}%')
            
        if search:
            conditions.append('(name LIKE ? OR tags LIKE ?)')
            params.extend([f'%{search}%', f'%{search}%'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # 計算總數
        count_query = f'SELECT COUNT(*) FROM radio_stations WHERE {where_clause}'
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 獲取分頁資料
        offset = (page - 1) * limit
        data_query = f'''
            SELECT uuid, name, url, homepage, favicon, tags, country, language, 
                   codec, bitrate, source_api, source_type
            FROM radio_stations 
            WHERE {where_clause}
            ORDER BY 
                CASE source_api 
                    WHEN 'manual' THEN 1 
                    WHEN 'tunein' THEN 2
                    WHEN 'radio_browser' THEN 3
                    ELSE 4 
                END,
                name
            LIMIT ? OFFSET ?
        '''
        
        cursor.execute(data_query, params + [limit, offset])
        rows = cursor.fetchall()
        
        stations = []
        for row in rows:
            stations.append({
                'uuid': row[0],
                'name': row[1],
                'url': row[2],
                'homepage': row[3],
                'favicon': row[4],
                'tags': row[5].split(',') if row[5] else [],
                'country': row[6],
                'language': row[7],
                'codec': row[8],
                'bitrate': row[9],
                'source_api': row[10],
                'source_type': row[11]
            })
        
        conn.close()
        
        return {
            'data': stations,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }

    def search_stations_by_query(self, query: str) -> List[Dict]:
        """根據查詢字串搜尋電台"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_query = '''
            SELECT uuid, name, url, homepage, favicon, tags, country, language, 
                   codec, bitrate, source_api, source_type
            FROM radio_stations 
            WHERE name LIKE ? OR tags LIKE ? OR country LIKE ?
            ORDER BY 
                CASE 
                    WHEN name LIKE ? THEN 1
                    WHEN tags LIKE ? THEN 2
                    ELSE 3
                END, name
            LIMIT 100
        '''
        
        like_query = f'%{query}%'
        cursor.execute(search_query, [like_query, like_query, like_query, like_query, like_query])
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'uuid': row[0],
                'name': row[1],
                'url': row[2],
                'homepage': row[3],
                'favicon': row[4],
                'tags': row[5].split(',') if row[5] else [],
                'country': row[6],
                'language': row[7],
                'codec': row[8],
                'bitrate': row[9],
                'source_api': row[10],
                'source_type': row[11]
            })
        
        conn.close()
        return results

    def get_featured_stations(self) -> List[Dict]:
        """獲取精選電台"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT uuid, name, url, homepage, favicon, tags, country, language, 
                   codec, bitrate, source_api, source_type
            FROM radio_stations 
            WHERE source_api = 'manual'
            ORDER BY name
            LIMIT 20
        ''')
        
        featured = []
        for row in cursor.fetchall():
            featured.append({
                'uuid': row[0],
                'name': row[1],
                'url': row[2],
                'homepage': row[3],
                'favicon': row[4],
                'tags': row[5].split(',') if row[5] else [],
                'country': row[6],
                'language': row[7],
                'codec': row[8],
                'bitrate': row[9],
                'source_api': row[10],
                'source_type': row[11],
                'featured_reason': '⭐ 手動精選高品質電台'
            })
        
        conn.close()
        return featured

    def get_database_stats(self) -> Dict:
        """獲取資料庫統計資訊"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 總電台數
        cursor.execute('SELECT COUNT(*) FROM radio_stations')
        total = cursor.fetchone()[0]
        
        # 按來源統計
        cursor.execute('''
            SELECT source_api, COUNT(*) 
            FROM radio_stations 
            GROUP BY source_api 
            ORDER BY COUNT(*) DESC
        ''')
        by_source = dict(cursor.fetchall())
        
        # 按國家統計
        cursor.execute('''
            SELECT country, COUNT(*) 
            FROM radio_stations 
            WHERE country != '' 
            GROUP BY country 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        by_country = dict(cursor.fetchall())
        
        # 最近更新時間
        cursor.execute('SELECT MAX(collection_date) FROM radio_stations')
        last_update = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_stations': total,
            'by_source': by_source,
            'by_country': by_country,
            'last_update': last_update
        }

    def update_stations_background(self):
        """背景更新電台資料"""
        try:
            self.logger.info("🔄 開始背景更新電台資料...")
            from multi_source_radio_collector import MultiSourceRadioCollector
            
            collector = MultiSourceRadioCollector(self.db_path)
            result = collector.collect_all_stations()
            collector.sync_stations_to_db(result)
            
            self.logger.info(f"✅ 背景更新完成，共 {result['total_unique']} 個電台")
        except Exception as e:
            self.logger.error(f"❌ 背景更新失敗: {e}")

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """啟動API服務器"""
        self.logger.info(f"🚀 電台API服務器啟動於 http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函數"""
    api = RadioAPI()
    
    # 首次啟動時更新電台資料
    print("🔄 首次啟動，更新電台資料...")
    api.update_stations_background()
    
    # 啟動API服務器
    api.run(debug=False)

if __name__ == "__main__":
    main()
