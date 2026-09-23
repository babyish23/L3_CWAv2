# L3_CWAv2 - 台灣天氣預報系統

基於中央氣象署開放資料 API 的天氣預報儀表板，使用 Python + Streamlit 建構。

## 🎯 專案目標

- 串接中央氣象署 API 獲取 36 小時天氣預報
- 使用 SQLite 儲存與管理天氣資料  
- 建立互動式 Streamlit 儀表板
- 提供圖表分析、地圖視覺化和資料查詢功能

## 🏗️ 系統架構

```
L3_CWAv2/
├── weather_api.py      # CWA API 串接模組
├── database.py         # SQLite 資料庫管理
├── streamlit_app.py    # Streamlit 網頁應用
├── requirements.txt    # Python 套件依賴
├── .env               # API 金鑰 (不提交至Git)
├── .gitignore         # Git 忽略清單
└── README.md          # 專案說明
```

## 🚀 快速開始

### 1. 環境設定

```bash
# 建立虛擬環境 (建議)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴套件
pip install -r requirements.txt
```

### 2. API 金鑰設定

1. 前往 [中央氣象署開放資料平台](https://opendata.cwa.gov.tw/)
2. 註冊並登入會員
3. 到 [授權金鑰頁面](https://opendata.cwa.gov.tw/user/authkey) 取得 API Key
4. 建立 `.env` 檔案：

```env
CWA_API_KEY=你的API金鑰
```

### 3. 測試 API 連線

```bash
python weather_api.py
```

### 4. 測試資料庫功能

```bash
python database.py
```

### 5. 啟動 Streamlit 應用

```bash
streamlit run streamlit_app.py
```

應用將在 `http://localhost:8501` 開啟。

## 📊 功能特色

### 🔍 資料獲取
- **API 串接**: 自動從中央氣象署獲取最新 36 小時天氣預報
- **多縣市支援**: 支援全台 22 個縣市的天氣資料
- **資料解析**: 提取溫度、降雨機率、天氣現象、舒適度等資訊

### 💾 資料管理
- **SQLite 儲存**: 本地化資料庫，支援歷史資料查詢
- **自動去重**: 避免重複儲存相同時段的預報資料
- **資料清理**: 自動清除過期的舊資料

### 🎛️ 互動儀表板
- **縣市選擇**: 多選下拉選單，自由選擇關注的縣市
- **即時更新**: 一鍵更新最新天氣資料
- **多標籤檢視**:
  - 📊 **圖表分析**: 溫度趨勢線圖 + 降雨機率長條圖
  - 🗺️ **地圖檢視**: 互動式台灣地圖，顯示各縣市天氣狀況
  - 📋 **詳細資料**: 完整的表格檢視與 CSV 下載

### 📈 視覺化功能
- **溫度趨勢圖**: Plotly 互動式圖表，顯示最高/最低溫變化
- **降雨機率圖**: 長條圖顯示各時段降雨機率
- **天氣地圖**: Folium 地圖標示各縣市天氣概況，顏色編碼溫度等級
- **統計摘要**: 自動計算平均溫度、降雨機率等統計指標

## 🛠️ 技術規格

### 核心套件
- **requests**: HTTP API 請求
- **pandas**: 資料處理與分析  
- **sqlite3**: 本地資料庫
- **streamlit**: 網頁應用框架
- **plotly**: 互動式圖表
- **folium**: 地圖視覺化
- **python-dotenv**: 環境變數管理

### API 規格
- **資料來源**: 中央氣象署開放資料平台
- **資料集**: F-C0032-001 (一般天氣預報-今明36小時天氣預報)
- **更新頻率**: 每日 4 次 (02:30, 08:30, 14:30, 20:30)
- **資料格式**: JSON

## 📁 檔案說明

### `weather_api.py`
- `CWAWeatherAPI`: 主要 API 類別
  - `fetch_weather_forecast()`: 獲取天氣預報資料
  - `parse_weather_data()`: 解析 API 回應為 DataFrame
  - `get_available_locations()`: 取得支援的縣市列表

### `database.py`
- `WeatherDatabase`: 資料庫管理類別
  - `save_weather_data()`: 儲存天氣資料
  - `get_weather_data()`: 查詢天氣資料
  - `get_locations()`: 取得已儲存的縣市
  - `clear_old_data()`: 清理過期資料

### `streamlit_app.py`
- 主要網頁應用程式
- 包含三個主要檢視標籤
- 快取機制優化載入效能
- 自動化資料更新流程

## 🎨 介面預覽

### 主控台
- 縣市選擇多選框
- 一鍵資料更新按鈕  
- 即時統計指標卡片

### 圖表分析
- 溫度趨勢雙軸圖表
- 降雨機率長條圖
- 分縣市統計表格

### 地圖檢視
- 台灣縣市天氣地圖
- 顏色編碼溫度等級
- 點擊標記顯示詳細資訊

## 🔧 進階設定

### 快取設定
- API 資料快取: 1 小時
- 資料庫查詢快取: 10 分鐘

### 資料保留政策
- 預設保留最近 7 天的資料
- 可透過 `clear_old_data()` 調整保留天數

## 🚀 部署選項

### 本地執行
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud 部署
1. 推送程式碼至 GitHub
2. 連結 Streamlit Cloud 帳號
3. 在 Streamlit Cloud 設定環境變數 `CWA_API_KEY`
4. 自動部署並獲得公開網址

## 📝 開發紀錄

### 已實現功能
- ✅ CWA API 串接
- ✅ SQLite 資料庫設計
- ✅ Streamlit 多頁面應用
- ✅ 互動式圖表 (Plotly)
- ✅ 台灣地圖視覺化 (Folium)
- ✅ CSV 資料匯出
- ✅ 響應式介面設計

### 未來改進方向
- 🔄 加入更多天氣資料集 (雷達圖、衛星雲圖)
- 🔄 預報準確度分析
- 🔄 警報通知功能
- 🔄 歷史資料趨勢分析
- 🔄 多語言介面支援

## 📞 聯絡資訊

- **課程**: AIOT-DA  
- **作業**: L3 - 中央氣象署API應用 v2
- **開發時間**: 2026年9月

## 📄 授權聲明

本專案僅供學習用途。天氣資料來源為中央氣象署開放資料平台，請遵守其使用條款。