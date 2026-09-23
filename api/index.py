from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
import json
from datetime import datetime, timedelta
import io

from weather_api import CWAWeatherAPI
from database import WeatherDatabase
import numpy as np

app = Flask(__name__)

def generate_sample_data():
    """生成範例天氣資料"""
    import random
    from datetime import datetime, timedelta
    
    locations = ['臺北市', '新北市', '臺中市', '高雄市', '桃園市']
    sample_data = []
    
    base_time = datetime.now()
    
    for i in range(3):  # 3個時段
        for location in locations:
            start_time = base_time + timedelta(hours=i*8)
            end_time = start_time + timedelta(hours=8)
            
            sample_data.append({
                'location': location,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'max_temp': random.uniform(20, 35),
                'min_temp': random.uniform(15, 25),
                'pop': random.uniform(0, 80),
                'weather_description': random.choice(['晴天', '多雲', '陰天', '小雨']),
                'comfort_index': random.choice(['舒適', '稍熱', '悶熱'])
            })
    
    return pd.DataFrame(sample_data)

def load_weather_data(location=None):
    """載入天氣資料"""
    db = WeatherDatabase()
    return db.get_weather_data(location=location)

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
        print(f"獲取 {location} 天氣資料時發生錯誤: {e}")
    return pd.DataFrame()

def create_temperature_chart(df):
    """建立簡化的溫度趨勢圖"""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    # 為每個縣市添加最高溫和最低溫線條
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    color_idx = 0
    
    for location in df['location'].unique():
        location_data = df[df['location'] == location].sort_values('start_time')
        
        if len(location_data) > 0:
            # 最高溫線
            fig.add_trace(
                go.Scatter(
                    x=location_data['start_time'],
                    y=location_data['max_temp'],
                    mode='lines+markers',
                    name=f'{location} 最高溫',
                    line=dict(color=colors[color_idx % len(colors)], width=3),
                    marker=dict(size=8, symbol='circle')
                )
            )
            
            # 最低溫線
            fig.add_trace(
                go.Scatter(
                    x=location_data['start_time'],
                    y=location_data['min_temp'],
                    mode='lines+markers',
                    name=f'{location} 最低溫',
                    line=dict(color=colors[color_idx % len(colors)], width=2, dash='dash'),
                    marker=dict(size=6, symbol='diamond')
                )
            )
            
            color_idx += 1
    
    fig.update_layout(
        title={
            'text': "📈 一周溫度趨勢預報",
            'x': 0.5,
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="時間",
        yaxis_title="溫度 (°C)",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(t=80, b=60, l=60, r=60)
    )
    
    # 美化軸線
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128,128,128,0.2)',
        showline=True, 
        linewidth=1, 
        linecolor='rgba(128,128,128,0.3)'
    )
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128,128,128,0.2)',
        showline=True, 
        linewidth=1, 
        linecolor='rgba(128,128,128,0.3)'
    )
    
    return fig

def create_weather_map(df):
    """建立天氣地圖"""
    if df.empty:
        return None
    
    # 台灣中心座標
    taiwan_center = [23.8, 120.9]
    m = folium.Map(location=taiwan_center, zoom_start=7)
    
    # 縣市座標對映
    city_coords = {
        '臺北市': [25.0330, 121.5654], '新北市': [25.0173, 121.4437],
        '桃園市': [24.9937, 121.3009], '臺中市': [24.1477, 120.6736],
        '臺南市': [22.9999, 120.2269], '高雄市': [22.6273, 120.3014],
        '基隆市': [25.1276, 121.7392], '新竹市': [24.8067, 120.9683],
        '新竹縣': [24.7036, 121.0178], '苗栗縣': [24.4818, 120.8039],
        '彰化縣': [24.0518, 120.4818], '南投縣': [23.9609, 120.9718],
        '雲林縣': [23.7571, 120.3897], '嘉義縣': [23.4518, 120.2554],
        '嘉義市': [23.4801, 120.4491], '屏東縣': [22.5516, 120.5473],
        '宜蘭縣': [24.7021, 121.7378], '花蓮縣': [23.7569, 121.3542],
        '臺東縣': [22.7972, 121.1444], '澎湖縣': [23.5712, 119.5793],
        '金門縣': [24.3265, 118.3186], '連江縣': [26.1435, 119.9397]
    }
    
    # 獲取每個城市最新的溫度資料
    latest_data = df.sort_values('start_time').groupby('location').last()
    
    for location, data in latest_data.iterrows():
        if location in city_coords:
            coords = city_coords[location]
            max_temp = data['max_temp'] if 'max_temp' in data and pd.notna(data['max_temp']) else 0
            
            # 根據溫度決定顏色
            if max_temp >= 30:
                color = 'red'
                temp_level = '高溫'
            elif max_temp >= 25:
                color = 'orange'  
                temp_level = '溫暖'
            elif max_temp >= 20:
                color = 'green'
                temp_level = '舒適'
            else:
                color = 'blue'
                temp_level = '涼爽'
            
            min_temp = data['min_temp'] if 'min_temp' in data and pd.notna(data['min_temp']) else 0
            pop = data['pop'] if 'pop' in data and pd.notna(data['pop']) else 0
            weather_desc = data['weather_description'] if 'weather_description' in data else '晴天'
            
            popup_text = f"""
            <b>{location}</b><br>
            溫度: {min_temp:.1f}°C - {max_temp:.1f}°C<br>
            降雨機率: {pop:.0f}%<br>
            天氣: {weather_desc}<br>
            等級: {temp_level}
            """
            
            folium.CircleMarker(
                location=coords,
                radius=8,
                popup=folium.Popup(popup_text, max_width=200),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
    
    return m

@app.route('/')
def index():
    """主頁面"""
    try:
        # 自動載入所有天氣資料
        all_data = load_weather_data()
        
        # 如果沒有資料，嘗試獲取所有縣市的資料
        if all_data.empty:
            # 預設縣市列表
            default_locations = [
                '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市',
                '基隆市', '新竹市', '新竹縣', '苗栗縣', '彰化縣', '南投縣',
                '雲林縣', '嘉義縣', '嘉義市', '屏東縣', '宜蘭縣', '花蓮縣',
                '臺東縣', '澎湖縣', '金門縣', '連江縣'
            ]
            
            # 獲取所有縣市的資料
            for location in default_locations[:5]:  # 先獲取前5個避免API限制
                try:
                    fetch_new_weather_data(location)
                except:
                    continue
            
            all_data = load_weather_data()
        
        # 如果仍然沒有資料，使用範例資料
        if all_data.empty:
            all_data = generate_sample_data()
            print("主頁面使用範例資料")
        
        locations = list(all_data['location'].unique()) if not all_data.empty else []
        
        return render_template('index.html', 
                             locations=locations, 
                             initial_data=all_data.to_dict('records') if not all_data.empty else [])
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/weather-data')
def get_weather_data():
    """API: 獲取天氣資料"""
    try:
        selected_locations = request.args.getlist('locations')
        
        if selected_locations:
            all_data = pd.DataFrame()
            for location in selected_locations:
                data = load_weather_data(location)
                all_data = pd.concat([all_data, data], ignore_index=True)
        else:
            all_data = load_weather_data()
        
        if all_data.empty:
            # 使用範例資料
            all_data = generate_sample_data()
            print("使用範例資料生成圖表")
        
        # 移除圖表功能，只保留統計資料
        chart_json = None
        
        # 準備統計資料
        temp_stats = None
        pop_stats = None
        
        if 'max_temp' in all_data.columns and 'min_temp' in all_data.columns:
            temp_grouped = all_data[['location', 'max_temp', 'min_temp']].groupby('location').agg({
                'max_temp': ['mean', 'max', 'min'],
                'min_temp': ['mean', 'max', 'min']
            }).round(1)
            
            # 扁平化多層級索引
            temp_stats = {}
            for location in temp_grouped.index:
                temp_stats[location] = {
                    'max_temp_mean': temp_grouped.loc[location, ('max_temp', 'mean')],
                    'max_temp_max': temp_grouped.loc[location, ('max_temp', 'max')],
                    'max_temp_min': temp_grouped.loc[location, ('max_temp', 'min')],
                    'min_temp_mean': temp_grouped.loc[location, ('min_temp', 'mean')],
                    'min_temp_max': temp_grouped.loc[location, ('min_temp', 'max')],
                    'min_temp_min': temp_grouped.loc[location, ('min_temp', 'min')]
                }
        
        if 'pop' in all_data.columns:
            pop_grouped = all_data[['location', 'pop']].groupby('location').agg({
                'pop': ['mean', 'max', 'min']
            }).round(1)
            
            # 扁平化多層級索引
            pop_stats = {}
            for location in pop_grouped.index:
                pop_stats[location] = {
                    'mean': pop_grouped.loc[location, ('pop', 'mean')],
                    'max': pop_grouped.loc[location, ('pop', 'max')],
                    'min': pop_grouped.loc[location, ('pop', 'min')]
                }
        
        return jsonify({
            'success': True,
            'data': all_data.to_dict('records'),
            'stats': {
                'temp': temp_stats,
                'pop': pop_stats,
                'total_records': len(all_data)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-weather')
def update_weather():
    """API: 更新天氣資料"""
    try:
        locations = request.args.getlist('locations')
        
        if not locations:
            return jsonify({'success': False, 'message': '未選擇縣市'})
        
        for location in locations:
            fetch_new_weather_data(location)
        
        return jsonify({'success': True, 'message': f'已更新 {len(locations)} 個縣市的資料'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/weather-map')
def get_weather_map():
    """API: 獲取天氣地圖"""
    try:
        selected_locations = request.args.getlist('locations')
        
        if selected_locations:
            all_data = pd.DataFrame()
            for location in selected_locations:
                data = load_weather_data(location)
                all_data = pd.concat([all_data, data], ignore_index=True)
        else:
            all_data = load_weather_data()
        
        # 如果沒有資料，使用範例資料
        if all_data.empty:
            all_data = generate_sample_data()
        
        weather_map = create_weather_map(all_data)
        if weather_map:
            return weather_map._repr_html_()
        else:
            return '<p>無地圖資料</p>'
    
    except Exception as e:
        return f'<p>錯誤: {str(e)}</p>'

@app.route('/api/download-csv')
def download_csv():
    """API: 下載CSV檔案"""
    try:
        location_filter = request.args.get('location', '全部')
        sort_column = request.args.get('sort', 'start_time')
        
        all_data = load_weather_data()
        
        if location_filter != '全部':
            all_data = all_data[all_data['location'] == location_filter]
        
        all_data = all_data.sort_values(sort_column)
        
        # 建立CSV
        output = io.StringIO()
        all_data.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        # 建立檔案名稱
        filename = f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# For Vercel serverless function
def handler(request):
    return app(request.environ, lambda status, headers: None)

# Export for Vercel
application = app