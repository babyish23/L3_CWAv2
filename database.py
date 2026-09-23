import sqlite3
import pandas as pd
from datetime import datetime
import os

class WeatherDatabase:
    def __init__(self, db_path="weather_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化資料庫和表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 建立天氣資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                weather_description TEXT,
                pop REAL,
                min_temp REAL,
                max_temp REAL,
                comfort_index TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(location, start_time, end_time)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"OK: 資料庫初始化完成: {self.db_path}")
    
    def save_weather_data(self, df):
        """
        儲存天氣資料到資料庫
        
        Args:
            df (pd.DataFrame): 天氣資料
            
        Returns:
            int: 儲存的記錄數量
        """
        if df.empty:
            print("沒有資料可儲存")
            return 0
            
        # 添加建立時間
        df_to_save = df.copy()
        df_to_save['created_at'] = datetime.now().isoformat()
        
        # 轉換時間格式為字串
        if 'start_time' in df_to_save.columns:
            df_to_save['start_time'] = df_to_save['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'end_time' in df_to_save.columns:
            df_to_save['end_time'] = df_to_save['end_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # 使用 REPLACE 來處理重複資料
            saved_count = df_to_save.to_sql(
                'weather_forecast', 
                conn, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            conn.commit()
            print(f"OK: 成功儲存 {len(df_to_save)} 筆天氣資料")
            return len(df_to_save)
            
        except Exception as e:
            print(f"FAIL: 儲存資料時發生錯誤: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_weather_data(self, location=None, limit=None):
        """
        從資料庫獲取天氣資料
        
        Args:
            location (str, optional): 指定縣市
            limit (int, optional): 限制記錄數量
            
        Returns:
            pd.DataFrame: 天氣資料
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM weather_forecast"
        params = []
        
        if location:
            query += " WHERE location = ?"
            params.append(location)
        
        query += " ORDER BY location, start_time"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            
            # 轉換時間欄位
            if not df.empty:
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
                df['created_at'] = pd.to_datetime(df['created_at'])
            
            return df
            
        except Exception as e:
            print(f"FAIL: 獲取資料時發生錯誤: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_locations(self):
        """獲取資料庫中所有的縣市"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT location FROM weather_forecast ORDER BY location")
            locations = [row[0] for row in cursor.fetchall()]
            return locations
        except Exception as e:
            print(f"FAIL: 獲取縣市列表時發生錯誤: {e}")
            return []
        finally:
            conn.close()
    
    def get_latest_data_by_location(self):
        """獲取每個縣市的最新資料"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT location, 
                   COUNT(*) as record_count,
                   MIN(start_time) as earliest_time,
                   MAX(start_time) as latest_time,
                   MAX(created_at) as last_updated
            FROM weather_forecast 
            GROUP BY location 
            ORDER BY location
        '''
        
        try:
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                time_cols = ['earliest_time', 'latest_time', 'last_updated']
                for col in time_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
            return df
        except Exception as e:
            print(f"FAIL: 獲取統計資料時發生錯誤: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def clear_old_data(self, days_to_keep=7):
        """清除舊資料"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM weather_forecast 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"OK: 清除了 {deleted_count} 筆超過 {days_to_keep} 天的舊資料")
            else:
                print("沒有需要清除的舊資料")
                
            return deleted_count
            
        except Exception as e:
            print(f"FAIL: 清除舊資料時發生錯誤: {e}")
            return 0
        finally:
            conn.close()

def test_database():
    """測試資料庫功能"""
    print("測試資料庫功能...")
    
    # 建立測試資料
    test_data = pd.DataFrame({
        'location': ['臺北市', '臺北市', '桃園市'],
        'start_time': pd.to_datetime(['2024-01-01 06:00', '2024-01-01 18:00', '2024-01-01 06:00']),
        'end_time': pd.to_datetime(['2024-01-01 18:00', '2024-01-02 06:00', '2024-01-01 18:00']),
        'weather_description': ['晴天', '多雲', '陰天'],
        'pop': [10, 30, 60],
        'min_temp': [15, 18, 16],
        'max_temp': [25, 22, 20],
        'comfort_index': ['舒適', '舒適', '稍有寒意']
    })
    
    # 測試資料庫操作
    db = WeatherDatabase("test_weather.db")
    
    # 測試儲存
    saved_count = db.save_weather_data(test_data)
    print(f"儲存測試: {saved_count} 筆資料")
    
    # 測試讀取
    all_data = db.get_weather_data()
    print(f"讀取測試: {len(all_data)} 筆資料")
    
    # 測試依縣市篩選
    taipei_data = db.get_weather_data(location='臺北市')
    print(f"臺北市資料: {len(taipei_data)} 筆")
    
    # 測試統計
    stats = db.get_latest_data_by_location()
    print(f"統計資料: {len(stats)} 個縣市")
    
    # 清理測試檔案
    if os.path.exists("test_weather.db"):
        os.remove("test_weather.db")
        print("OK: 測試檔案已清理")

if __name__ == "__main__":
    test_database()