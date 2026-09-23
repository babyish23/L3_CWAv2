from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import folium
import time
from datetime import datetime
import io

from weather_api import CWAWeatherAPI
from database import WeatherDatabase

# Vercel 只會用 CDN 提供 public/ 底下的靜態檔，本機則由 Flask 自己提供同一個資料夾
app = Flask(__name__, static_folder='public/static', static_url_path='/static')

WEEKLY_CACHE_SECONDS = 30 * 60
_weekly_cache = {'timestamp': 0, 'data': None}


def load_weather_data(location=None):
    """載入天氣資料"""
    db = WeatherDatabase()
    return db.get_weather_data(location=location)


def fetch_all_weather_data():
    """一次抓取全台 22 縣市的 36 小時預報並存入資料庫"""
    try:
        api = CWAWeatherAPI()
        raw_data = api.fetch_weather_forecast(None)
        if raw_data:
            df = api.parse_weather_data(raw_data)
            if not df.empty:
                WeatherDatabase().save_weather_data(df)
                return df
    except Exception as e:
        print(f"獲取天氣資料時發生錯誤: {e}")
    return pd.DataFrame()


def load_or_fetch_weather_data():
    """資料庫沒資料時（例如 Vercel 冷啟動），先向 API 抓一次"""
    all_data = load_weather_data()
    if all_data.empty:
        fetch_all_weather_data()
        all_data = load_weather_data()
    return all_data


def get_weekly_temperature():
    """取得一週逐日最高／最低溫，快取 30 分鐘"""
    now = time.time()
    if _weekly_cache['data'] is not None and now - _weekly_cache['timestamp'] < WEEKLY_CACHE_SECONDS:
        return _weekly_cache['data']

    df = CWAWeatherAPI().fetch_weekly_temperature()
    if not df.empty:
        _weekly_cache['data'] = df
        _weekly_cache['timestamp'] = now
    return df


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
        all_data = load_or_fetch_weather_data()
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
        all_data = load_or_fetch_weather_data()
        
        if all_data.empty:
            return jsonify({'success': False, 'message': '目前無法取得氣象署資料，請確認 CWA_API_KEY 設定'})
        
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
        
        # jsonify 會把無時區的時間標成 GMT，瀏覽器再加 8 小時；改傳台灣當地時間字串
        records = all_data.copy()
        for col in ['start_time', 'end_time', 'created_at']:
            if col in records.columns:
                records[col] = records[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

        return jsonify({
            'success': True,
            'data': records.to_dict('records'),
            'stats': {
                'temp': temp_stats,
                'pop': pop_stats,
                'total_records': len(all_data)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/weekly-temperature')
def weekly_temperature():
    """API: 各縣市一週逐日最高溫／最低溫"""
    try:
        df = get_weekly_temperature()
        if df.empty:
            return jsonify({'success': False, 'message': '無法取得一週預報資料'})

        series = {}
        for location, group in df.groupby('location'):
            group = group.sort_values('date')
            series[location] = {
                'dates': group['date'].tolist(),
                'max_temp': group['max_temp'].tolist(),
                'min_temp': group['min_temp'].tolist()
            }

        return jsonify({'success': True, 'series': series})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/update-weather')
def update_weather():
    """API: 更新全台天氣資料"""
    try:
        df = fetch_all_weather_data()
        _weekly_cache['data'] = None

        if df.empty:
            return jsonify({'success': False, 'error': '更新失敗，無法取得氣象署資料'})

        return jsonify({'success': True, 'message': f"已更新 {df['location'].nunique()} 個縣市的資料"})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/weather-map')
def get_weather_map():
    """API: 獲取天氣地圖"""
    try:
        all_data = load_or_fetch_weather_data()
        
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
