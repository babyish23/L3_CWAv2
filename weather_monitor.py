#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L3_CWAv2 - Taiwan Weather Monitoring Dashboard
即時天氣監控儀表板 - 參考 AirBox 設計風格
使用 CWA O-A0003-001 即時觀測資料
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

class WeatherMonitor:
    def __init__(self):
        self.api_key = os.getenv('CWA_API_KEY')
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.dataset_id = "O-A0003-001"  # 即時觀測資料
        self.db_path = "weather_monitor.db"
        self.init_database()
    
    def init_database(self):
        """初始化資料庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                station_id TEXT NOT NULL,
                obs_time TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                county_name TEXT,
                town_name TEXT,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                wind_speed REAL,
                wind_direction REAL,
                precipitation REAL,
                weather_desc TEXT,
                uv_index REAL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 建立唯一索引來避免重複資料
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_station_obs_time 
            ON weather_observations(station_id, obs_time)
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_weather_data(self, station_name=None, county_name=None):
        """獲取即時天氣觀測資料"""
        url = f"{self.base_url}/{self.dataset_id}"
        params = {
            'Authorization': self.api_key,
            'format': 'JSON'
        }
        
        if station_name:
            params['StationName'] = station_name
        if county_name:
            params['CountyName'] = county_name
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') != 'true':
                return None
                
            return data
            
        except Exception as e:
            st.error(f"API 請求失敗: {e}")
            return None
    
    def parse_weather_data(self, raw_data):
        """解析天氣觀測資料"""
        if not raw_data or not raw_data.get('records'):
            return pd.DataFrame()
        
        stations = raw_data['records'].get('Station', [])
        weather_list = []
        
        for station in stations:
            try:
                # 基本資訊
                station_name = station.get('StationName', '')
                station_id = station.get('StationId', '')
                
                # 觀測時間
                obs_time = station.get('ObsTime', {}).get('DateTime', '')
                
                # 地理資訊
                geo_info = station.get('GeoInfo', {})
                coordinates = geo_info.get('Coordinates', [{}])
                wgs84_coord = next((c for c in coordinates if c.get('CoordinateName') == 'WGS84'), {})
                
                latitude = float(wgs84_coord.get('StationLatitude', 0)) if wgs84_coord.get('StationLatitude') else None
                longitude = float(wgs84_coord.get('StationLongitude', 0)) if wgs84_coord.get('StationLongitude') else None
                
                county_name = geo_info.get('CountyName', '')
                town_name = geo_info.get('TownName', '')
                
                # 氣象資料
                weather_element = station.get('WeatherElement', {})
                
                def safe_float(value):
                    try:
                        return float(value) if value not in [None, '', '-99', -99] else None
                    except (ValueError, TypeError):
                        return None
                
                temperature = safe_float(weather_element.get('AirTemperature'))
                humidity = safe_float(weather_element.get('RelativeHumidity'))
                pressure = safe_float(weather_element.get('AirPressure'))
                wind_speed = safe_float(weather_element.get('WindSpeed'))
                wind_direction = safe_float(weather_element.get('WindDirection'))
                precipitation = safe_float(weather_element.get('Now', {}).get('Precipitation') if isinstance(weather_element.get('Now'), dict) else None)
                weather_desc = weather_element.get('Weather', '')
                uv_index = safe_float(weather_element.get('UVIndex'))
                
                weather_record = {
                    'station_name': station_name,
                    'station_id': station_id,
                    'obs_time': obs_time,
                    'latitude': latitude,
                    'longitude': longitude,
                    'county_name': county_name,
                    'town_name': town_name,
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': pressure,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction,
                    'precipitation': precipitation,
                    'weather_desc': weather_desc,
                    'uv_index': uv_index,
                    'created_at': datetime.now().isoformat()
                }
                
                weather_list.append(weather_record)
                
            except Exception as e:
                continue  # 跳過有問題的資料
        
        return pd.DataFrame(weather_list)
    
    def save_to_database(self, df):
        """儲存資料到資料庫"""
        if df.empty:
            return 0
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            saved_count = 0
            
            for _, row in df.iterrows():
                # 使用 INSERT OR REPLACE 避免重複資料問題
                cursor.execute('''
                    INSERT OR REPLACE INTO weather_observations (
                        station_name, station_id, obs_time, latitude, longitude,
                        county_name, town_name, temperature, humidity, pressure,
                        wind_speed, wind_direction, precipitation, weather_desc,
                        uv_index, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['station_name'], row['station_id'], row['obs_time'],
                    row['latitude'], row['longitude'], row['county_name'],
                    row['town_name'], row['temperature'], row['humidity'],
                    row['pressure'], row['wind_speed'], row['wind_direction'],
                    row['precipitation'], row['weather_desc'], row['uv_index'],
                    row['created_at']
                ))
                saved_count += 1
            
            conn.commit()
            return saved_count
            
        except Exception as e:
            st.error(f"資料庫儲存失敗: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_latest_data(self, hours=24):
        """獲取最新資料"""
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
            
        conn = sqlite3.connect(self.db_path)
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            query = '''
                SELECT * FROM weather_observations 
                WHERE created_at > ? 
                ORDER BY obs_time DESC, created_at DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=[cutoff_time])
            
            if not df.empty:
                df['obs_time'] = pd.to_datetime(df['obs_time'])
                df['created_at'] = pd.to_datetime(df['created_at'])
            
            return df
            
        except Exception as e:
            st.error(f"資料讀取失敗: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

# 頁面設定 - 參考 AirBox 風格
st.set_page_config(
    page_title="Taiwan Weather Monitor",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS - 模仿監控平台風格
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    
    .status-good { border-left-color: #28a745 !important; }
    .status-moderate { border-left-color: #ffc107 !important; }
    .status-bad { border-left-color: #dc3545 !important; }
    
    .weather-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .station-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    .station-name {
        font-weight: bold;
        color: #2a5298;
        margin-bottom: 0.5rem;
    }
    
    .data-row {
        display: flex;
        justify-content: space-between;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    
    .update-time {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)  # 快取10分鐘
def load_weather_data():
    monitor = WeatherMonitor()
    return monitor.get_latest_data()

def update_weather_data():
    """更新天氣資料"""
    monitor = WeatherMonitor()
    
    # 獲取主要縣市資料
    major_cities = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市']
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_data = []
    
    for i, city in enumerate(major_cities):
        status_text.text(f"正在更新 {city} 資料...")
        progress_bar.progress((i + 1) / len(major_cities))
        
        raw_data = monitor.fetch_weather_data(county_name=city)
        if raw_data:
            df = monitor.parse_weather_data(raw_data)
            if not df.empty:
                monitor.save_to_database(df)
                all_data.append(df)
        
        time.sleep(0.5)  # 避免 API 請求過於頻繁
    
    status_text.text("資料更新完成！")
    progress_bar.progress(1.0)
    
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def create_weather_map(df):
    """建立天氣監控地圖"""
    if df.empty:
        return None
    
    # 取得最新資料
    latest_df = df.dropna(subset=['latitude', 'longitude']).drop_duplicates('station_id').copy()
    
    if latest_df.empty:
        return None
    
    # 建立地圖
    center_lat = latest_df['latitude'].mean()
    center_lon = latest_df['longitude'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # 添加測站標記
    for _, row in latest_df.iterrows():
        # 根據溫度決定顏色
        temp = row['temperature']
        if pd.isna(temp):
            color = 'gray'
        elif temp >= 30:
            color = 'red'
        elif temp >= 25:
            color = 'orange'
        elif temp >= 20:
            color = 'green'
        else:
            color = 'blue'
        
        popup_html = f"""
        <div style="width: 200px;">
            <h4>{row['station_name']}</h4>
            <p><strong>溫度:</strong> {temp:.1f}°C</p>
            <p><strong>濕度:</strong> {row['humidity']:.1f}%</p>
            <p><strong>風速:</strong> {row['wind_speed']:.1f} m/s</p>
            <p><strong>觀測時間:</strong> {row['obs_time'].strftime('%H:%M')}</p>
        </div>
        """
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['station_name']}: {temp}°C",
            color='white',
            weight=2,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    return m

def main():
    # 主標題
    st.markdown("""
    <div class="main-header">
        <h1>🌡️ Taiwan Weather Monitor</h1>
        <p>中央氣象署即時觀測資料監控平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 控制按鈕
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 更新資料", type="primary"):
            with st.spinner("正在更新資料..."):
                update_weather_data()
                st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("自動更新 (10分鐘)")
    
    # 載入資料
    df = load_weather_data()
    
    if df.empty:
        st.warning("📭 目前沒有資料，請點擊「更新資料」取得最新觀測資料")
        return
    
    # 顯示最後更新時間
    if not df.empty:
        last_update = df['created_at'].max()
        st.markdown(f"""
        <div class="update-time">
            📡 最後更新時間: {pd.to_datetime(last_update).strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
    
    # 統計摘要
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        active_stations = df['station_id'].nunique()
        st.metric("📍 監測站數", active_stations)
    
    with col2:
        avg_temp = df['temperature'].mean()
        st.metric("🌡️ 平均溫度", f"{avg_temp:.1f}°C" if not pd.isna(avg_temp) else "N/A")
    
    with col3:
        avg_humidity = df['humidity'].mean()
        st.metric("💧 平均濕度", f"{avg_humidity:.0f}%" if not pd.isna(avg_humidity) else "N/A")
    
    with col4:
        avg_wind = df['wind_speed'].mean()
        st.metric("💨 平均風速", f"{avg_wind:.1f} m/s" if not pd.isna(avg_wind) else "N/A")
    
    with col5:
        data_count = len(df)
        st.metric("📊 資料筆數", data_count)
    
    # 主要內容區域
    tab1, tab2, tab3 = st.tabs(["🗺️ 即時監控", "📊 數據分析", "📋 詳細資料"])
    
    with tab1:
        st.subheader("🗺️ 全台測站即時監控")
        
        # 建立並顯示地圖
        weather_map = create_weather_map(df)
        if weather_map:
            st_folium(weather_map, width=700, height=500)
        
        # 測站卡片展示
        st.subheader("📡 重點測站資訊")
        
        # 選取最新的主要測站資料
        latest_stations = df.drop_duplicates('station_id', keep='last').head(12)
        
        cols = st.columns(3)
        for idx, (_, station) in enumerate(latest_stations.iterrows()):
            with cols[idx % 3]:
                temp_status = "status-good" if station['temperature'] and 20 <= station['temperature'] <= 28 else "status-moderate"
                
                st.markdown(f"""
                <div class="metric-card {temp_status}">
                    <div class="station-name">{station['station_name']}</div>
                    <div class="data-row">
                        <span>🌡️ 溫度:</span>
                        <strong>{station['temperature']:.1f}°C</strong>
                    </div>
                    <div class="data-row">
                        <span>💧 濕度:</span>
                        <span>{station['humidity']:.0f}%</span>
                    </div>
                    <div class="data-row">
                        <span>💨 風速:</span>
                        <span>{station['wind_speed']:.1f} m/s</span>
                    </div>
                    <div class="data-row">
                        <span>📍 位置:</span>
                        <span>{station['county_name']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("📈 溫度分布分析")
        
        if not df.empty:
            # 溫度分布圖
            fig_temp = px.histogram(
                df, 
                x='temperature', 
                nbins=20,
                title="溫度分布直方圖",
                labels={'temperature': '溫度 (°C)', 'count': '測站數量'}
            )
            fig_temp.update_layout(showlegend=False)
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # 縣市平均溫度
            col1, col2 = st.columns(2)
            
            with col1:
                county_stats = df.groupby('county_name')['temperature'].agg(['mean', 'count']).reset_index()
                county_stats = county_stats[county_stats['count'] >= 1].sort_values('mean', ascending=False)
                
                fig_county = px.bar(
                    county_stats.head(10),
                    x='mean',
                    y='county_name',
                    orientation='h',
                    title="各縣市平均溫度",
                    labels={'mean': '平均溫度 (°C)', 'county_name': '縣市'}
                )
                st.plotly_chart(fig_county, use_container_width=True)
            
            with col2:
                # 溫濕度關係
                valid_data = df.dropna(subset=['temperature', 'humidity'])
                if not valid_data.empty:
                    fig_scatter = px.scatter(
                        valid_data,
                        x='temperature',
                        y='humidity',
                        color='county_name',
                        title="溫度與濕度關係",
                        labels={'temperature': '溫度 (°C)', 'humidity': '濕度 (%)'}
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
    
    with tab3:
        st.subheader("📋 完整觀測資料")
        
        # 資料篩選
        col1, col2, col3 = st.columns(3)
        
        with col1:
            counties = ['全部'] + sorted(df['county_name'].unique().tolist())
            selected_county = st.selectbox("縣市篩選", counties)
        
        with col2:
            sort_options = {
                '觀測時間': 'obs_time',
                '測站名稱': 'station_name',
                '溫度': 'temperature',
                '濕度': 'humidity'
            }
            sort_by = st.selectbox("排序依據", list(sort_options.keys()))
        
        with col3:
            ascending = st.selectbox("排序方式", ['降序', '升序']) == '升序'
        
        # 篩選和排序資料
        filtered_df = df.copy()
        if selected_county != '全部':
            filtered_df = filtered_df[filtered_df['county_name'] == selected_county]
        
        if not filtered_df.empty:
            filtered_df = filtered_df.sort_values(sort_options[sort_by], ascending=ascending)
            
            # 顯示資料表
            display_columns = [
                'station_name', 'county_name', 'obs_time', 
                'temperature', 'humidity', 'wind_speed', 'pressure'
            ]
            
            st.dataframe(
                filtered_df[display_columns],
                use_container_width=True,
                column_config={
                    'station_name': '測站名稱',
                    'county_name': '縣市',
                    'obs_time': '觀測時間',
                    'temperature': st.column_config.NumberColumn('溫度 (°C)', format="%.1f"),
                    'humidity': st.column_config.NumberColumn('濕度 (%)', format="%.0f"),
                    'wind_speed': st.column_config.NumberColumn('風速 (m/s)', format="%.1f"),
                    'pressure': st.column_config.NumberColumn('氣壓 (hPa)', format="%.1f")
                }
            )
            
            # 下載功能
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下載 CSV",
                data=csv,
                file_name=f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    # 自動更新
    if auto_refresh:
        time.sleep(600)  # 10分鐘
        st.rerun()

if __name__ == "__main__":
    main()