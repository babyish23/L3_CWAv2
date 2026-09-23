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

app = Flask(__name__)

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
        title="天氣預報趨勢圖",
        height=600,
        showlegend=True,
        hovermode='x unified'
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
            
            popup_text = f"""
            <b>{location}</b><br>
            溫度: {data['min_temp']:.1f}°C - {max_temp:.1f}°C<br>
            降雨機率: {data['pop']:.0f}%<br>
            天氣: {data['weather_description']}<br>
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
        # 載入天氣資料
        all_data = load_weather_data()
        locations = list(all_data['location'].unique()) if not all_data.empty else []
        
        return render_template('index.html', locations=locations)
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
            return jsonify({'success': False, 'message': '無資料'})
        
        # 準備圖表資料
        fig = create_temperature_chart(all_data)
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) if fig else None
        
        # 準備統計資料
        temp_stats = None
        pop_stats = None
        
        if 'max_temp' in all_data.columns and 'min_temp' in all_data.columns:
            temp_stats = all_data[['location', 'max_temp', 'min_temp']].groupby('location').agg({
                'max_temp': ['mean', 'max', 'min'],
                'min_temp': ['mean', 'max', 'min']
            }).round(1).to_dict()
        
        if 'pop' in all_data.columns:
            pop_stats = all_data[['location', 'pop']].groupby('location').agg({
                'pop': ['mean', 'max', 'min']
            }).round(1).to_dict()
        
        return jsonify({
            'success': True,
            'chart': chart_json,
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

if __name__ == '__main__':
    app.run(debug=True)