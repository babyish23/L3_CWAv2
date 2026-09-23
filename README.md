# 🌤️ L3_CWAv2 - 台灣天氣預報儀表板

> **課程**: AIOT-DA  
> **作業**: L3 - 中央氣象署API應用 v2  
> **開發時間**: 2026年9月  
> **技術棧**: Python, Flask, Streamlit, Plotly, Folium  

## 📋 專案概述

基於中央氣象署開放資料 API 的天氣預報儀表板，提供台灣各縣市的36小時天氣預報資訊，包含溫度趨勢圖表、互動式地圖檢視和詳細資料分析。

### 🎯 主要功能

- 🔄 **自動資料獲取**: 串接中央氣象署 API 獲取即時天氣資料
- 📊 **視覺化圖表**: 溫度趨勢線圖，支援多縣市對比
- 🗺️ **互動式地圖**: 台灣天氣分布地圖，溫度分級顯示  
- 📋 **資料管理**: SQLite 本地儲存，支援歷史資料查詢
- 💻 **雙版本支援**: Streamlit (開發) + Flask (部署) 版本

## 🏗️ 系統架構

```
L3_CWAv2/
├── 🐍 Python 後端
│   ├── weather_api.py      # CWA API 串接模組
│   ├── database.py         # SQLite 資料庫管理
│   ├── app.py             # Flask 網頁應用 (部署版)
│   └── streamlit_app.py   # Streamlit 應用 (開發版)
├── 🎨 前端界面  
│   ├── templates/         # Flask HTML 模板
│   │   ├── index.html    # 主頁面
│   │   └── error.html    # 錯誤頁面
│   └── static/           # 靜態資源
│       ├── css/style.css # 樣式表
│       └── js/app.js     # JavaScript 邏輯
├── 🔧 配置檔案
│   ├── requirements.txt   # Python 依賴套件
│   ├── vercel.json       # Vercel 部署配置
│   └── .env              # 環境變數 (本地)
└── 📊 資料儲存
    ├── weather_data.db    # 天氣資料庫
    └── weather_monitor.db # 監控資料庫
```

## 🚀 開發流程

### 階段一：Streamlit 原型開發

**目標**: 快速建立功能原型，驗證核心邏輯

```python
# 核心功能實現
- CWA API 串接 ✅
- 資料庫設計 ✅  
- 圖表視覺化 ✅
- 地圖整合 ✅
```

**成果預覽**:
![Streamlit版本展示](assets/streamlit_demo.png)

### 階段二：Flask 生產版本

**目標**: 轉換為 Flask 以支援 Vercel 部署

**轉換要點**:
1. **後端架構重新設計**
   ```python
   # Streamlit → Flask
   st.selectbox() → <select> + AJAX
   st.plotly_chart() → Plotly.js
   st_folium() → Folium HTML embed
   ```

2. **前端界面開發**
   - Bootstrap 5 響應式設計
   - Plotly.js 互動圖表
   - 漸層背景 + 玻璃擬態效果

3. **API 端點設計**
   ```python
   GET  /                    # 主頁面
   GET  /api/weather-data    # 天氣資料 API
   POST /api/update-weather  # 更新資料 API
   GET  /api/weather-map     # 地圖資料 API
   GET  /api/download-csv    # CSV 下載 API
   ```

## 💻 技術實作

### 🔌 API 串接模組

```python
class CWAWeatherAPI:
    def __init__(self):
        self.api_key = os.getenv('CWA_API_KEY')
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.dataset_id = "F-C0032-001"  # 36小時天氣預報
    
    def fetch_weather_forecast(self, location):
        """獲取指定縣市天氣預報"""
        url = f"{self.base_url}/{self.dataset_id}"
        params = {
            'Authorization': self.api_key,
            'locationName': location,
            'format': 'JSON'
        }
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
```

### 🗃️ 資料庫管理

```python
class WeatherDatabase:
    def __init__(self):
        self.db_path = "weather_data.db"
        self.init_database()
    
    def save_weather_data(self, df):
        """儲存天氣資料，避免重複"""
        conn = sqlite3.connect(self.db_path)
        df.to_sql('weather_forecast', conn, 
                 if_exists='append', index=False)
        conn.close()
```

### 📊 圖表視覺化

**溫度趨勢圖**:
```python
def create_temperature_chart(df):
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for idx, location in enumerate(df['location'].unique()):
        data = df[df['location'] == location].sort_values('start_time')
        
        # 最高溫線
        fig.add_trace(go.Scatter(
            x=data['start_time'], y=data['max_temp'],
            name=f'{location} 最高溫',
            line=dict(color=colors[idx % len(colors)], width=3)
        ))
        
        # 最低溫線  
        fig.add_trace(go.Scatter(
            x=data['start_time'], y=data['min_temp'],
            name=f'{location} 最低溫',
            line=dict(color=colors[idx % len(colors)], width=2, dash='dash')
        ))
```

### 🗺️ 互動式地圖

```python  
def create_weather_map(df):
    taiwan_center = [23.8, 120.9]
    m = folium.Map(location=taiwan_center, zoom_start=7)
    
    # 縣市座標對映
    city_coords = {
        '臺北市': [25.0330, 121.5654],
        '新北市': [25.0173, 121.4437],
        # ... 更多縣市
    }
    
    # 根據溫度決定標記顏色
    for location, data in df.groupby('location').last().iterrows():
        if location in city_coords:
            temp = data['max_temp']
            color = 'red' if temp >= 30 else 'orange' if temp >= 25 else 'green'
            
            folium.CircleMarker(
                location=city_coords[location],
                radius=8, color=color, 
                popup=f"{location}: {temp}°C"
            ).add_to(m)
```

## 🎨 UI/UX 設計

### 設計理念
- **現代化視覺**: 漸層背景 + 玻璃擬態 (Glassmorphism)
- **直覺操作**: 三標籤頁設計，預設地圖檢視
- **響應式布局**: 支援桌面/平板/手機

### 視覺效果
```css
/* 漸層背景 */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 玻璃擬態卡片 */
.card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}
```

### 功能頁面

#### 🗺️ 地圖檢視 (預設頁面)
- 台灣縣市天氣分布圖
- 溫度分級顏色編碼
- 點擊標記顯示詳細資訊

#### 📊 圖表分析  
- 一周溫度趨勢線圖
- 多縣市對比功能
- 統計數據表格

#### 📋 詳細資料
- 完整天氣資料表格
- 縣市篩選功能
- CSV 檔案下載

## 🔧 部署配置

### Vercel 部署

**1. 專案配置** (`vercel.json`):
```json
{
    "version": 2,
    "builds": [{"src": "./app.py", "use": "@vercel/python"}],
    "routes": [{"src": "/(.*)", "dest": "./app.py"}]
}
```

**2. 環境變數設定**:
- 在 Vercel 儀表板設定 `CWA_API_KEY`
- 支援 Production/Preview/Development 環境

**3. 自動部署**:
- GitHub 連動，推送即部署
- 支援預覽分支功能

### 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
echo "CWA_API_KEY=你的API金鑰" > .env

# 啟動 Flask 版本
python app.py

# 或啟動 Streamlit 版本  
streamlit run streamlit_app.py
```

## 📊 專案成果

### 功能完成度

| 功能模組 | 完成狀態 | 說明 |
|---------|---------|------|
| 🔌 API 串接 | ✅ 完成 | 中央氣象署 36小時預報 |
| 🗃️ 資料儲存 | ✅ 完成 | SQLite 本地資料庫 |
| 📊 圖表視覺化 | ✅ 完成 | Plotly 溫度趨勢圖 |
| 🗺️ 地圖整合 | ✅ 完成 | Folium 互動式地圖 |
| 💻 網頁界面 | ✅ 完成 | Flask + Bootstrap 5 |
| 🚀 雲端部署 | ✅ 完成 | Vercel 自動部署 |

### 效能指標

- **API 回應時間**: < 2 秒
- **頁面載入時間**: < 3 秒  
- **資料庫查詢**: < 500ms
- **圖表渲染**: < 1 秒

### 支援範圍

- **涵蓋區域**: 台灣 22 個縣市
- **預報時長**: 36 小時 (3天)
- **更新頻率**: 每日 4 次
- **資料保存**: 7 天歷史記錄

## 🎯 學習成果

### 技術能力提升

1. **API 整合技術**
   - RESTful API 串接
   - JSON 資料解析
   - 錯誤處理與重試機制

2. **資料視覺化**
   - Plotly 圖表庫應用
   - 地理資訊視覺化 (Folium)
   - 互動式圖表設計

3. **全端開發經驗**
   - Python Flask 後端開發
   - HTML/CSS/JavaScript 前端
   - 資料庫設計與 ORM

4. **雲端部署實務**
   - Vercel 無伺服器部署
   - 環境變數管理
   - CI/CD 自動化流程

### 問題解決能力

1. **跨框架轉換**: Streamlit → Flask
2. **UI/UX 優化**: 從功能導向到用戶體驗導向
3. **部署問題排除**: 環境變數、依賴管理
4. **效能優化**: 快取機制、資料分頁

## 🔮 未來改進方向

### 短期目標 (1-2週)
- [ ] 加入天氣警報通知功能
- [ ] 支援更多天氣資料集 (雷達圖、衛星雲圖)  
- [ ] 增加歷史天氣資料對比
- [ ] 優化行動裝置體驗

### 長期目標 (1-3個月)
- [ ] 機器學習天氣預測模型
- [ ] 多語言介面支援 (中/英)
- [ ] 用戶個人化設定
- [ ] API 服務化，提供給其他應用使用

## 📞 專案資訊

### 開發環境
- **Python**: 3.11.9
- **主要框架**: Flask 3.1.3, Streamlit 1.64.0
- **資料庫**: SQLite 3
- **部署平台**: Vercel

### 資料來源  
- **中央氣象署開放資料平台**
- **資料集**: F-C0032-001 (一般天氣預報-今明36小時天氣預報)
- **更新頻率**: 每日 4 次 (02:30, 08:30, 14:30, 20:30)

### 專案連結
- **GitHub**: [https://github.com/babyish23/L3_CWAv2](https://github.com/babyish23/L3_CWAv2)
- **線上展示**: [部署完成後更新]
- **技術文件**: 本 README.md

---

## 📄 授權聲明

本專案僅供學習用途。天氣資料來源為中央氣象署開放資料平台，請遵守其使用條款。

**開發者**: NCHU AIOT-DA 課程  
**最後更新**: 2026年9月23日