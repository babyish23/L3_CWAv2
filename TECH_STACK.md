# L3_CWAv2 技術架構與套件說明

## 📋 專案概述

**L3_CWAv2** 是一個基於中央氣象署開放資料的即時天氣監控儀表板，採用現代 Web 技術棧構建，提供專業級氣象資料視覺化與監控功能。

## 🏗️ 系統架構

### 整體架構 (MVC Pattern)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │    Business     │    │      Data       │
│     Layer       │    │     Logic       │    │     Layer       │
│                 │    │     Layer       │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Streamlit   │ │◄──►│ │WeatherMonitor│ │◄──►│ │   SQLite    │ │
│ │   Web UI    │ │    │ │    Class     │ │    │ │  Database   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Plotly      │ │    │ │   API       │ │    │ │    CWA      │ │
│ │ Charts      │ │    │ │ Integration │ │    │ │ Open Data   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │                 │    │                 │
│ │ Folium      │ │    │                 │    │                 │
│ │    Map      │ │    │                 │    │                 │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 資料流程圖
```
CWA API (O-A0003-001) 
        ↓
    HTTP Request
        ↓
   JSON Response
        ↓
   Data Parsing
        ↓
   SQLite Storage
        ↓
  Streamlit Frontend
        ↓
   Visual Dashboard
```

## 📦 核心套件清單

### 🌐 Web 框架
```python
streamlit==1.64.0              # 主要 Web 應用框架
streamlit-folium==0.27.4       # 地圖整合套件
```

**選擇原因:**
- **Streamlit**: 快速建構資料科學 Web 應用，無需前端開發經驗
- **Streamlit-folium**: 提供互動式地圖功能，適合地理資料視覺化

### 📊 資料處理與分析
```python
pandas>=2.0.0                  # 資料結構與分析
numpy>=2.4.6                   # 數值計算基礎
```

**選擇原因:**
- **Pandas**: 強大的資料清理、轉換、分析功能
- **NumPy**: 提供高效能數值運算支援

### 🌐 網路請求
```python
requests>=2.31.0               # HTTP 請求處理
```

**選擇原因:**
- 簡潔易用的 API 請求介面
- 良好的錯誤處理與重試機制
- 廣泛的社群支援

### 🗄️ 資料庫
```python
sqlite3                        # 內建輕量級資料庫
```

**選擇原因:**
- Python 內建，無需額外安裝
- 適合中小型資料量的本地儲存
- 支援標準 SQL 語法

### 📈 資料視覺化
```python
plotly>=5.15.0                 # 互動式圖表
folium>=0.14.0                 # 互動式地圖
```

**選擇原因:**
- **Plotly**: 豐富的圖表類型，支援互動功能
- **Folium**: 基於 Leaflet.js，提供專業級地圖視覺化

### ⚙️ 環境管理
```python
python-dotenv>=1.0.0           # 環境變數管理
```

**選擇原因:**
- 安全管理 API 金鑰
- 方便部署時的環境設定

## 🏛️ 系統架構設計

### 1. 資料層 (Data Layer)

#### SQLite 資料庫設計
```sql
CREATE TABLE weather_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT NOT NULL,           -- 測站名稱
    station_id TEXT NOT NULL,             -- 測站代碼  
    obs_time TEXT NOT NULL,               -- 觀測時間
    latitude REAL,                        -- 緯度
    longitude REAL,                       -- 經度
    county_name TEXT,                     -- 縣市名稱
    town_name TEXT,                       -- 鄉鎮名稱
    temperature REAL,                     -- 氣溫 (°C)
    humidity REAL,                        -- 濕度 (%)
    pressure REAL,                        -- 氣壓 (hPa)
    wind_speed REAL,                      -- 風速 (m/s)
    wind_direction REAL,                  -- 風向 (°)
    precipitation REAL,                   -- 降雨量 (mm)
    weather_desc TEXT,                    -- 天氣描述
    uv_index REAL,                        -- 紫外線指數
    created_at TEXT NOT NULL              -- 資料建立時間
);

CREATE UNIQUE INDEX idx_station_obs_time 
ON weather_observations(station_id, obs_time);
```

#### API 整合設計
```python
# CWA Open Data API 規格
Base URL: https://opendata.cwa.gov.tw/api/v1/rest/datastore
Dataset:  O-A0003-001 (即時觀測資料)
Format:   JSON
Update:   每 10 分鐘更新
Auth:     API Key (Authorization Header)
```

### 2. 業務邏輯層 (Business Logic Layer)

#### WeatherMonitor 類別架構
```python
class WeatherMonitor:
    def __init__(self):
        # 初始化設定
        
    def fetch_weather_data(self):
        # API 資料獲取
        
    def parse_weather_data(self):
        # JSON 資料解析
        
    def save_to_database(self):
        # 資料庫儲存
        
    def get_latest_data(self):
        # 資料查詢
```

### 3. 展示層 (Presentation Layer)

#### Streamlit 頁面架構
```
├── 主標題區域 (Header)
├── 控制面板 (Control Panel)
├── 統計摘要 (Metrics Summary)  
└── 分頁內容 (Tabbed Content)
    ├── 🗺️ 即時監控 (Real-time Monitor)
    │   ├── 互動式地圖 (Interactive Map)
    │   └── 測站卡片 (Station Cards)
    ├── 📊 數據分析 (Data Analysis)
    │   ├── 溫度分布圖 (Temperature Distribution)
    │   ├── 縣市排行榜 (County Ranking)
    │   └── 相關性分析 (Correlation Analysis)
    └── 📋 詳細資料 (Detailed Data)
        ├── 資料篩選 (Data Filtering)
        └── 資料匯出 (Data Export)
```

## 🎨 UI/UX 設計原則

### 設計靈感
參考 **AirBox 環境監測平台** 的專業監控介面設計：
- 清潔現代的卡片式佈局
- 直觀的色彩編碼系統
- 響應式網格排版
- 即時資料更新提示

### 色彩系統
```css
Primary Blue:    #2a5298 (主要品牌色)
Success Green:   #28a745 (正常狀態)
Warning Yellow:  #ffc107 (注意狀態)
Danger Red:      #dc3545 (警告狀態)
Light Gray:      #f8f9fa (背景色)
```

### 響應式設計
- **桌面版**: 多欄位網格佈局
- **平板版**: 自適應欄位寬度  
- **手機版**: 單欄堆疊佈局

## 🚀 效能優化策略

### 1. 資料快取機制
```python
@st.cache_data(ttl=600)  # 10分鐘快取
def load_weather_data():
    # 資料載入快取
```

### 2. API 請求優化
- **批量請求**: 一次獲取多個縣市資料
- **錯誤重試**: 自動重試失敗的請求
- **請求限制**: 避免過度頻繁的 API 呼叫

### 3. 資料庫優化
- **索引設計**: 針對查詢欄位建立索引
- **資料清理**: 定期清除過期資料
- **批量插入**: 減少資料庫 I/O 次數

## 🛡️ 安全性考量

### 1. API 金鑰保護
```python
# 使用 .env 檔案儲存敏感資訊
CWA_API_KEY=your_api_key_here

# .gitignore 防止金鑰洩露
.env
.env.local
```

### 2. 資料驗證
```python
def safe_float(value):
    """安全的數值轉換，防止異常值"""
    try:
        return float(value) if value not in [None, '', '-99', -99] else None
    except (ValueError, TypeError):
        return None
```

### 3. SQL 注入防護
```python
# 使用參數化查詢
cursor.execute("SELECT * FROM table WHERE id = ?", [user_input])
```

## 📊 監控與分析功能

### 1. 即時監控
- **全台測站地圖**: 視覺化所有氣象站位置與即時數據
- **溫度色彩編碼**: 直觀的溫度等級顯示
- **測站狀態卡片**: 重點測站詳細資訊展示

### 2. 數據分析
- **統計分布**: 溫度、濕度等參數的分布分析
- **地區比較**: 各縣市氣象數據比較
- **趨勢分析**: 歷史資料趨勢變化

### 3. 資料匯出
- **CSV 格式**: 支援資料表格匯出
- **篩選功能**: 依縣市、時間等條件篩選
- **即時下載**: 一鍵下載當前篩選資料

## 🔄 部署與維運

### 本地部署
```bash
# 環境設置
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
echo "CWA_API_KEY=your_key" > .env

# 啟動應用
streamlit run weather_monitor.py
```

### 雲端部署選項
1. **Streamlit Cloud**: 直接從 GitHub 部署
2. **Heroku**: 容器化部署
3. **AWS EC2**: 自主管理部署
4. **Docker**: 容器化跨平台部署

## 🔮 未來擴展計畫

### 短期目標 (1-2 個月)
- [ ] 增加更多氣象資料集 (雨量、風速等)
- [ ] 實作警報通知功能
- [ ] 加入歷史資料趨勢分析
- [ ] 優化手機版介面體驗

### 中期目標 (3-6 個月)  
- [ ] 機器學習預測模型整合
- [ ] 多語言介面支援 (英文)
- [ ] API 服務對外開放
- [ ] 進階圖表與儀表板客製化

### 長期目標 (6-12 個月)
- [ ] 微服務架構重構
- [ ] 即時 WebSocket 資料推送  
- [ ] 大數據分析平台整合
- [ ] 行動 App 開發

## 📝 開發團隊與貢獻

### 技術棧選擇理由
1. **Python 生態系**: 豐富的資料科學套件支援
2. **Streamlit 框架**: 快速原型開發，降低前端開發複雜度  
3. **SQLite 資料庫**: 輕量級部署，適合 MVP 產品
4. **開源套件**: 降低成本，社群支援完善

### 版本控制
- **Git**: 分散式版本控制
- **GitHub**: 程式碼託管與協作平台
- **語義化版本**: 遵循 SemVer 規範

---

*📅 最後更新: 2026-09-23*  
*🔗 專案連結: https://github.com/babyish23/L3_CWAv2*