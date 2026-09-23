import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import time

from weather_api import CWAWeatherAPI
from database import WeatherDatabase

# 頁面設定
st.set_page_config(
    page_title="台灣天氣預報儀表板",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)  # 快取10分鐘
def load_weather_data(location=None):
    """載入天氣資料"""
    db = WeatherDatabase()
    return db.get_weather_data(location=location)

@st.cache_data(ttl=3600)  # 快取1小時
def fetch_new_weather_data(location):
    """獲取新的天氣資料"""
    try:
        api = CWAWeatherAPI()
        raw_data = api.fetch_weather_forecast(location)
        if raw_data:
            df = api.parse_weather_data(raw_data)
            if not df.empty:
                db = WeatherDatabase()
                db.save_weather_data(df)
                return df
    except Exception as e:
        st.error(f"獲取 {location} 天氣資料時發生錯誤: {e}")
    return pd.DataFrame()

def create_temperature_chart(df):
    """建立溫度圖表"""
    if df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('溫度趨勢', '降雨機率'),
        vertical_spacing=0.1
    )
    
    # 溫度圖
    for location in df['location'].unique():
        location_data = df[df['location'] == location].sort_values('start_time')
        
        fig.add_trace(
            go.Scatter(
                x=location_data['start_time'],
                y=location_data['max_temp'],
                mode='lines+markers',
                name=f'{location} 最高溫',
                line=dict(color='red', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=location_data['start_time'],
                y=location_data['min_temp'],
                mode='lines+markers',
                name=f'{location} 最低溫',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        # 降雨機率
        fig.add_trace(
            go.Bar(
                x=location_data['start_time'],
                y=location_data['pop'],
                name=f'{location} 降雨機率',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="時間", row=2, col=1)
    fig.update_yaxes(title_text="溫度 (°C)", row=1, col=1)
    fig.update_yaxes(title_text="降雨機率 (%)", row=2, col=1)
    
    fig.update_layout(
        height=600,
        title_text="天氣預報趨勢圖",
        showlegend=True
    )
    
    return fig

def create_weather_map(df):
    """建立天氣地圖"""
    if df.empty:
        return None
    
    # 台灣縣市座標 (簡化版)
    city_coords = {
        '臺北市': [25.0330, 121.5654],
        '新北市': [25.0173, 121.4467],
        '桃園市': [24.9936, 121.3010],
        '臺中市': [24.1477, 120.6736],
        '臺南市': [22.9999, 120.2269],
        '高雄市': [22.6273, 120.3014],
        '基隆市': [25.1276, 121.7392],
        '新竹市': [24.8138, 120.9675],
        '嘉義市': [23.4801, 120.4491],
        '宜蘭縣': [24.7021, 121.7378],
        '新竹縣': [24.8387, 121.0177],
        '苗栗縣': [24.5602, 120.8214],
        '彰化縣': [24.0518, 120.5161],
        '南投縣': [23.9609, 120.9718],
        '雲林縣': [23.7093, 120.4314],
        '嘉義縣': [23.4518, 120.2554],
        '屏東縣': [22.5519, 120.5487],
        '花蓮縣': [23.9871, 121.6015],
        '臺東縣': [22.7972, 121.1713],
        '澎湖縣': [23.5711, 119.5793],
        '金門縣': [24.4490, 118.3570],
        '連江縣': [26.1967, 119.9325]
    }
    
    # 建立地圖
    m = folium.Map(
        location=[23.8, 121.0],  # 台灣中心
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # 取得每個縣市的最新資料
    latest_data = df.groupby('location').first().reset_index()
    
    for _, row in latest_data.iterrows():
        location = row['location']
        if location in city_coords:
            coords = city_coords[location]
            
            # 建立popup內容
            popup_text = f"""
            <b>{location}</b><br>
            天氣: {row.get('weather_description', 'N/A')}<br>
            最高溫: {row.get('max_temp', 'N/A')}°C<br>
            最低溫: {row.get('min_temp', 'N/A')}°C<br>
            降雨機率: {row.get('pop', 'N/A')}%<br>
            舒適度: {row.get('comfort_index', 'N/A')}
            """
            
            # 根據溫度決定標記顏色
            max_temp = row.get('max_temp', 20)
            if pd.isna(max_temp):
                color = 'gray'
            elif max_temp >= 30:
                color = 'red'
            elif max_temp >= 25:
                color = 'orange'
            elif max_temp >= 20:
                color = 'green'
            else:
                color = 'blue'
            
            folium.Marker(
                coords,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{location}: {max_temp}°C",
                icon=folium.Icon(color=color, icon='cloud')
            ).add_to(m)
    
    return m

def main():
    """主要應用程式"""
    
    # 標題
    st.markdown("<h1 class='main-header'>🌤️ 台灣天氣預報儀表板</h1>", unsafe_allow_html=True)
    
    # 側邊欄
    st.sidebar.header("🔧 控制面板")
    
    # 初始化API和資料庫
    api = CWAWeatherAPI()
    db = WeatherDatabase()
    
    # 獲取可用縣市
    available_locations = api.get_available_locations()
    
    # 縣市選擇
    selected_locations = st.sidebar.multiselect(
        "選擇縣市",
        available_locations,
        default=["臺北市", "桃園市", "臺中市"]
    )
    
    # 資料更新按鈕
    if st.sidebar.button("🔄 更新天氣資料", type="primary"):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        
        for i, location in enumerate(selected_locations):
            status_text.text(f"正在獲取 {location} 的資料...")
            progress_bar.progress((i + 1) / len(selected_locations))
            
            # 獲取並儲存資料
            fetch_new_weather_data(location)
            time.sleep(0.5)  # 避免API請求過於頻繁
        
        status_text.text("✅ 資料更新完成!")
        time.sleep(1)
        st.experimental_rerun()
    
    # 載入資料
    if selected_locations:
        all_data = pd.DataFrame()
        for location in selected_locations:
            location_data = load_weather_data(location)
            all_data = pd.concat([all_data, location_data], ignore_index=True)
    else:
        all_data = pd.DataFrame()
    
    if all_data.empty:
        st.warning("📭 目前沒有資料，請選擇縣市並點擊「更新天氣資料」按鈕")
        return
    
    # 主要內容區域
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📍 縣市數量",
            value=len(selected_locations)
        )
    
    with col2:
        avg_max_temp = all_data['max_temp'].mean()
        st.metric(
            label="🌡️ 平均最高溫",
            value=f"{avg_max_temp:.1f}°C" if not pd.isna(avg_max_temp) else "N/A"
        )
    
    with col3:
        avg_min_temp = all_data['min_temp'].mean()
        st.metric(
            label="❄️ 平均最低溫",
            value=f"{avg_min_temp:.1f}°C" if not pd.isna(avg_min_temp) else "N/A"
        )
    
    with col4:
        avg_pop = all_data['pop'].mean()
        st.metric(
            label="🌧️ 平均降雨機率",
            value=f"{avg_pop:.0f}%" if not pd.isna(avg_pop) else "N/A"
        )
    
    # 分頁顯示
    tab1, tab2, tab3 = st.tabs(["📊 圖表分析", "🗺️ 地圖檢視", "📋 詳細資料"])
    
    with tab1:
        st.subheader("📈 溫度與降雨趨勢")
        
        # 建立並顯示圖表
        fig = create_temperature_chart(all_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 統計摘要
        st.subheader("📊 統計摘要")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'max_temp' in all_data.columns and 'min_temp' in all_data.columns:
                temp_stats = all_data[['location', 'max_temp', 'min_temp']].groupby('location').agg({
                    'max_temp': ['mean', 'max', 'min'],
                    'min_temp': ['mean', 'max', 'min']
                }).round(1)
                
                temp_stats.columns = ['平均最高溫', '最高溫度', '最低最高溫', '平均最低溫', '最高最低溫', '最低最低溫']
                st.dataframe(temp_stats, use_container_width=True)
        
        with col2:
            if 'pop' in all_data.columns:
                pop_stats = all_data[['location', 'pop']].groupby('location').agg({
                    'pop': ['mean', 'max', 'min']
                }).round(1)
                
                pop_stats.columns = ['平均降雨機率', '最高降雨機率', '最低降雨機率']
                st.dataframe(pop_stats, use_container_width=True)
    
    with tab2:
        st.subheader("🗺️ 天氣分布地圖")
        
        weather_map = create_weather_map(all_data)
        if weather_map:
            st_folium(weather_map, width=700, height=500)
        
        st.info("💡 地圖說明：紅色=高溫(≥30°C), 橙色=溫暖(25-29°C), 綠色=舒適(20-24°C), 藍色=涼爽(<20°C)")
    
    with tab3:
        st.subheader("📋 完整天氣資料")
        
        # 資料篩選
        col1, col2 = st.columns(2)
        with col1:
            location_filter = st.selectbox(
                "篩選縣市",
                ["全部"] + list(all_data['location'].unique())
            )
        
        with col2:
            sort_column = st.selectbox(
                "排序依據",
                ["start_time", "location", "max_temp", "min_temp", "pop"]
            )
        
        # 篩選資料
        filtered_data = all_data.copy()
        if location_filter != "全部":
            filtered_data = filtered_data[filtered_data['location'] == location_filter]
        
        # 排序
        filtered_data = filtered_data.sort_values(sort_column)
        
        # 顯示資料
        st.dataframe(
            filtered_data[['location', 'start_time', 'end_time', 'weather_description', 
                          'max_temp', 'min_temp', 'pop', 'comfort_index']],
            use_container_width=True
        )
        
        # 下載按鈕
        csv = filtered_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下載CSV檔案",
            data=csv,
            file_name=f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # 頁尾資訊
    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    📊 **資料來源**: 中央氣象署開放資料平台  
    🔄 **最後更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    📈 **總記錄數**: {len(all_data)}
    """)

if __name__ == "__main__":
    main()