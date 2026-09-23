#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L3_CWAv2 - Taiwan Weather Forecast Tutorial
按照課程步驟 1-24 的完整學習流程
"""

import requests
import json
import pandas as pd
import sqlite3
from datetime import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class WeatherTutorial:
    def __init__(self):
        self.api_key = os.getenv('CWA_API_KEY')
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.db_path = "weather_forecast.db"
        
    def step1_introduction(self):
        """步驟1: 環境介紹 - AI + 資料 + 天氣 + 實作"""
        st.title("🌤️ 台灣天氣預報系統")
        st.subheader("步驟1: 環境介紹")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("### 🤖 AI")
            st.write("人工智慧")
            st.write("智能分析")
            
        with col2:
            st.markdown("### 📊 資料")
            st.write("氣象的重要性")
            st.write("資料分析顯示")
            
        with col3:
            st.markdown("### 🌦️ 天氣")
            st.write("天氣數據分析")
            st.write("智慧預報系統")
            
        with col4:
            st.markdown("### 💻 實作")
            st.write("動手做專案")
            st.write("整合多技能")
    
    def step2_weather_importance(self):
        """步驟2: 台灣的天氣與生活"""
        st.subheader("步驟2: 台灣的天氣與生活")
        st.write("氣象的重要性：")
        st.write("- 天氣影響生活")
        st.write("- 氣象預報服務")
        st.write("- 智慧城市應用")
        
    def step3_cwa_platform(self):
        """步驟3: 中央氣象署 CWA Open Data 平台"""
        st.subheader("步驟3: 中央氣象署 CWA")
        st.write("📡 Open Data 平台")
        st.write("- 註冊帳號")
        st.write("- 取得 API Key") 
        st.write("- 選擇資料集")
        
        if st.button("測試 API 連線"):
            if self.api_key:
                st.success(f"✅ API Key 已設定: {self.api_key[:20]}...")
            else:
                st.error("❌ 請先設定 API Key")
    
    def step4_api_requests(self):
        """步驟4: API 資料取得 - 使用 Requests 取得 JSON"""
        st.subheader("步驟4: API 資料取得")
        
        location = st.selectbox("選擇縣市", 
            ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"])
        
        if st.button("取得天氣資料"):
            with st.spinner("正在取得資料..."):
                try:
                    url = f"{self.base_url}/F-C0032-001"
                    params = {
                        'Authorization': self.api_key,
                        'format': 'JSON',
                        'locationName': location
                    }
                    
                    response = requests.get(url, params=params)
                    data = response.json()
                    
                    if data.get('success') == 'true':
                        st.success("✅ API 請求成功")
                        st.json(data)
                        return data
                    else:
                        st.error("❌ API 請求失敗")
                        
                except Exception as e:
                    st.error(f"錯誤: {e}")
                    
        return None
    
    def step5_json_parsing(self, raw_data):
        """步驟5: JSON 資料結構解析"""
        st.subheader("步驟5: JSON 資料結構解析")
        
        if raw_data:
            st.write("找到關鍵資料的位置：")
            st.code("""
# JSON 結構說明
{
  "records": {
    "location": [
      {
        "locationName": "縣市名稱",
        "weatherElement": [
          {
            "elementName": "Wx",     # 天氣現象
            "time": [...] 
          },
          {
            "elementName": "PoP",   # 降雨機率
            "time": [...]
          },
          {
            "elementName": "MinT",  # 最低溫度 
            "time": [...]
          },
          {
            "elementName": "MaxT",  # 最高溫度
            "time": [...]  
          }
        ]
      }
    ]
  }
}
            """)
    
    def step6_temperature_extraction(self, raw_data):
        """步驟6: 擷取最高最低氣溫"""
        st.subheader("步驟6: 擷取最高最低氣溫")
        
        if not raw_data:
            st.warning("請先取得 API 資料")
            return None
            
        try:
            locations = raw_data['records']['location']
            temperature_data = []
            
            for location in locations:
                location_name = location['locationName']
                
                for element in location['weatherElement']:
                    element_name = element['elementName']
                    
                    if element_name in ['MinT', 'MaxT']:
                        for time_period in element['time']:
                            temp_data = {
                                'location': location_name,
                                'element': element_name,
                                'start_time': time_period['startTime'],
                                'end_time': time_period['endTime'],
                                'temperature': int(time_period['parameter']['parameterName'])
                            }
                            temperature_data.append(temp_data)
            
            df = pd.DataFrame(temperature_data)
            st.success("✅ 溫度資料擷取成功")
            st.dataframe(df)
            
            return df
            
        except Exception as e:
            st.error(f"資料解析錯誤: {e}")
            return None
    
    def step7_pandas_processing(self, df):
        """步驟7: 資料整理與預覽 - 使用 Pandas 整理資料"""
        st.subheader("步驟7: 資料整理與預覽")
        
        if df is None or df.empty:
            st.warning("請先擷取溫度資料")
            return None
            
        # 數據透視表
        pivot_df = df.pivot_table(
            index=['location', 'start_time', 'end_time'],
            columns='element', 
            values='temperature',
            aggfunc='first'
        ).reset_index()
        
        pivot_df['start_time'] = pd.to_datetime(pivot_df['start_time'])
        pivot_df['end_time'] = pd.to_datetime(pivot_df['end_time'])
        
        st.success("✅ 資料整理完成")
        st.dataframe(pivot_df)
        
        return pivot_df
    
    def step8_sqlite_database(self, df):
        """步驟8: 建立 SQLite 資料庫"""
        st.subheader("步驟8: 建立 SQLite 資料庫")
        
        if df is None or df.empty:
            st.warning("請先整理資料")
            return False
            
        try:
            # 建立資料庫連線
            conn = sqlite3.connect(self.db_path)
            
            # 建立 TemperatureForecasts 表格
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TemperatureForecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    min_temp REAL,
                    max_temp REAL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # 儲存資料
            df['created_at'] = datetime.now().isoformat()
            df.to_sql('TemperatureForecasts', conn, if_exists='replace', index=False)
            
            conn.commit()
            conn.close()
            
            st.success("✅ 資料庫建立完成")
            st.info(f"資料庫位置: {self.db_path}")
            
            return True
            
        except Exception as e:
            st.error(f"資料庫錯誤: {e}")
            return False
    
    def step9_database_design(self):
        """步驟9: 資料庫設計 - TemperatureForecasts"""
        st.subheader("步驟9: 資料庫設計")
        
        st.code("""
CREATE TABLE TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    start_time TEXT NOT NULL, 
    end_time TEXT NOT NULL,
    min_temp REAL,
    max_temp REAL,
    created_at TEXT NOT NULL
);
        """)
        
        # 顯示目前資料庫內容
        if os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM TemperatureForecasts LIMIT 10", conn)
            conn.close()
            
            st.write("目前資料庫內容：")
            st.dataframe(df)
    
    def step10_sql_queries(self):
        """步驟10: 查詢資料語法 - 使用 SQL 查詢資料"""
        st.subheader("步驟10: SQL 查詢資料")
        
        if not os.path.exists(self.db_path):
            st.warning("請先建立資料庫")
            return
            
        # SQL 查詢範例
        sql_queries = {
            "查詢所有資料": "SELECT * FROM TemperatureForecasts",
            "查詢特定縣市": "SELECT * FROM TemperatureForecasts WHERE location = '臺北市'",
            "查詢最高溫": "SELECT location, MAX(max_temp) as highest_temp FROM TemperatureForecasts GROUP BY location",
            "查詢最低溫": "SELECT location, MIN(min_temp) as lowest_temp FROM TemperatureForecasts GROUP BY location"
        }
        
        selected_query = st.selectbox("選擇查詢", list(sql_queries.keys()))
        
        if st.button("執行查詢"):
            try:
                conn = sqlite3.connect(self.db_path)
                df = pd.read_sql_query(sql_queries[selected_query], conn)
                conn.close()
                
                st.success("✅ 查詢成功")
                st.dataframe(df)
                
            except Exception as e:
                st.error(f"查詢錯誤: {e}")

def main():
    """主程式 - 按步驟展示"""
    st.set_page_config(
        page_title="L3_CWAv2 - 台灣天氣預報教學",
        page_icon="🌤️",
        layout="wide"
    )
    
    tutorial = WeatherTutorial()
    
    # 側邊欄步驟選擇
    st.sidebar.title("📚 學習步驟")
    step = st.sidebar.selectbox("選擇步驟", [
        "步驟1: 環境介紹",
        "步驟2: 台灣天氣與生活", 
        "步驟3: CWA 平台",
        "步驟4: API 資料取得",
        "步驟5: JSON 解析",
        "步驟6: 溫度擷取",
        "步驟7: 資料整理",
        "步驟8: SQLite 資料庫",
        "步驟9: 資料庫設計",
        "步驟10: SQL 查詢"
    ])
    
    # 執行對應步驟
    if step == "步驟1: 環境介紹":
        tutorial.step1_introduction()
    elif step == "步驟2: 台灣天氣與生活":
        tutorial.step2_weather_importance()
    elif step == "步驟3: CWA 平台":
        tutorial.step3_cwa_platform()
    elif step == "步驟4: API 資料取得":
        raw_data = tutorial.step4_api_requests()
        if raw_data:
            st.session_state['raw_data'] = raw_data
    elif step == "步驟5: JSON 解析":
        raw_data = st.session_state.get('raw_data')
        tutorial.step5_json_parsing(raw_data)
    elif step == "步驟6: 溫度擷取":
        raw_data = st.session_state.get('raw_data')
        df = tutorial.step6_temperature_extraction(raw_data)
        if df is not None:
            st.session_state['temp_df'] = df
    elif step == "步驟7: 資料整理":
        df = st.session_state.get('temp_df')
        processed_df = tutorial.step7_pandas_processing(df)
        if processed_df is not None:
            st.session_state['processed_df'] = processed_df
    elif step == "步驟8: SQLite 資料庫":
        processed_df = st.session_state.get('processed_df')
        tutorial.step8_sqlite_database(processed_df)
    elif step == "步驟9: 資料庫設計":
        tutorial.step9_database_design()
    elif step == "步驟10: SQL 查詢":
        tutorial.step10_sql_queries()
        
    # 進度顯示
    progress = (int(step.split("步驟")[1].split(":")[0]) / 24) * 100
    st.sidebar.progress(progress / 100)
    st.sidebar.write(f"完成進度: {progress:.1f}%")

if __name__ == "__main__":
    main()