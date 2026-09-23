import requests
import json
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CWAWeatherAPI:
    def __init__(self):
        self.api_key = os.getenv('CWA_API_KEY')
        if not self.api_key:
            raise ValueError("CWA_API_KEY not found in environment variables")
        
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        
    def fetch_weather_forecast(self, location_name="臺北市"):
        """
        獲取36小時天氣預報資料
        
        Args:
            location_name (str): 縣市名稱，如 "臺北市", "桃園市"
            
        Returns:
            dict: API回應的完整資料
        """
        
        # F-C0032-001: 一般天氣預報-今明36小時天氣預報
        dataset_id = "F-C0032-001"
        
        params = {
            'Authorization': self.api_key,
            'format': 'JSON',
            'locationName': location_name
        }
        
        url = f"{self.base_url}/{dataset_id}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') != 'true':
                raise Exception(f"API request failed: {data}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"網路請求錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"其他錯誤: {e}")
            return None

    def parse_weather_data(self, raw_data):
        """
        解析天氣資料，提取最高溫、最低溫等資訊
        
        Args:
            raw_data (dict): 從API獲取的原始資料
            
        Returns:
            pd.DataFrame: 整理後的天氣資料
        """
        
        if not raw_data or not raw_data.get('records'):
            return pd.DataFrame()
            
        records = raw_data['records']
        locations = records.get('location', [])
        
        weather_list = []
        
        for location in locations:
            location_name = location.get('locationName', '')
            weather_elements = location.get('weatherElement', [])
            
            # 建立時間索引對應的資料字典
            time_data = {}
            
            for element in weather_elements:
                element_name = element.get('elementName', '')
                time_periods = element.get('time', [])
                
                for time_period in time_periods:
                    start_time = time_period.get('startTime', '')
                    end_time = time_period.get('endTime', '')
                    
                    # 建立時間鍵
                    time_key = f"{start_time}_to_{end_time}"
                    
                    if time_key not in time_data:
                        time_data[time_key] = {
                            'location': location_name,
                            'start_time': start_time,
                            'end_time': end_time
                        }
                    
                    # 根據不同的天氣元素提取資料
                    parameter = time_period.get('parameter', {})
                    
                    if element_name == 'Wx':  # 天氣現象
                        time_data[time_key]['weather_description'] = parameter.get('parameterName', '')
                    elif element_name == 'PoP':  # 降雨機率
                        time_data[time_key]['pop'] = parameter.get('parameterName', '')
                    elif element_name == 'MinT':  # 最低溫度
                        time_data[time_key]['min_temp'] = parameter.get('parameterName', '')
                    elif element_name == 'MaxT':  # 最高溫度
                        time_data[time_key]['max_temp'] = parameter.get('parameterName', '')
                    elif element_name == 'CI':  # 舒適度
                        time_data[time_key]['comfort_index'] = parameter.get('parameterName', '')
            
            # 將字典轉換為列表
            for time_key, data in time_data.items():
                weather_list.append(data)
        
        # 建立DataFrame
        df = pd.DataFrame(weather_list)
        
        # 資料型態轉換
        if not df.empty:
            # 轉換時間欄位
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['end_time'] = pd.to_datetime(df['end_time'])
            
            # 轉換數值欄位
            numeric_cols = ['pop', 'min_temp', 'max_temp']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 排序
            df = df.sort_values(['location', 'start_time']).reset_index(drop=True)
        
        return df
    
    def get_available_locations(self):
        """
        獲取所有可用的縣市列表
        
        Returns:
            list: 縣市名稱列表
        """
        locations = [
            "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
            "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
            "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
            "南投縣", "雲林縣", "嘉義縣", "屏東縣"
        ]
        return locations

def test_api():
    """測試API功能"""
    print("測試中央氣象署API...")
    
    api = CWAWeatherAPI()
    
    # 測試桃園市天氣
    print("\n獲取桃園市36小時天氣預報...")
    raw_data = api.fetch_weather_forecast("桃園市")
    
    if raw_data:
        print("✓ API請求成功")
        
        # 解析資料
        df = api.parse_weather_data(raw_data)
        print(f"✓ 解析完成，共 {len(df)} 筆記錄")
        
        if not df.empty:
            print("\n前3筆資料預覽:")
            print(df.head(3).to_string())
            
            print(f"\n可用欄位: {list(df.columns)}")
        
    else:
        print("✗ API請求失敗")

if __name__ == "__main__":
    test_api()