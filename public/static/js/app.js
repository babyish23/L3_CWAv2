// 全域變數
let currentData = [];
let weeklySeries = {};
let loadingModal;
const DEFAULT_WEEKLY_LOCATION = '臺中市';

// 初始化應用
document.addEventListener('DOMContentLoaded', function() {
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    initializeEventListeners();
    updateLastUpdateTime();
    
    // 網址帶 #chart 或 #data 時直接開啟對應分頁
    const tabFromHash = document.getElementById(`${location.hash.slice(1)}-tab`);
    if (tabFromHash) bootstrap.Tab.getOrCreateInstance(tabFromHash).show();
    
    loadAllWeatherDataSilently();
    loadWeatherMap();
    loadWeeklyTemperature();
});

// 初始化事件監聽器
function initializeEventListeners() {
    // 更新資料按鈕
    document.getElementById('updateDataBtn').addEventListener('click', updateAllWeatherData);
    
    // 重新載入頁面按鈕
    document.getElementById('refreshPageBtn').addEventListener('click', function() {
        window.location.reload();
    });
    
    // 下載按鈕
    document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
    
    // 篩選和排序
    document.getElementById('locationFilter').addEventListener('change', filterAndDisplayTable);
    document.getElementById('sortColumn').addEventListener('change', filterAndDisplayTable);
    
    // 一週溫度圖的縣市切換
    document.getElementById('weeklyLocation').addEventListener('change', displayWeeklyChart);
    
    // 圖表在隱藏分頁中繪製時寬度為 0，切換到分頁後要重新計算尺寸
    document.getElementById('chart-tab').addEventListener('shown.bs.tab', function() {
        const chartDiv = document.getElementById('temperatureChart');
        if (chartDiv.data) Plotly.Plots.resize(chartDiv);
    });
}

// 顯示警告訊息
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alertId = 'alert-' + Date.now();
    
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // 自動關閉警告
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) bsAlert.close();
        }
    }, 5000);
}

// 顯示載入中
function showLoading() {
    loadingModal.show();
}

// 隱藏載入中
function hideLoading() {
    loadingModal.hide();
}

// 載入所有天氣資料
async function loadAllWeatherData() {
    showLoading();
    
    try {
        const response = await fetch('/api/weather-data');
        const result = await response.json();
        
        if (result.success) {
            currentData = result.data;
            
            // 更新統計（移除圖表功能）
            updateStatistics(result.stats);
            
            // 更新篩選選項
            updateLocationFilter(result.data);
            
            // 更新表格
            filterAndDisplayTable();
            
            if (result.data.length > 0) {
                showAlert(`成功載入 ${result.data.length} 筆資料`, 'success');
            }
        } else {
            showAlert(result.message || result.error, 'danger');
        }
    } catch (error) {
        showAlert('載入資料時發生錯誤：' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 靜默載入所有天氣資料（不顯示loading和alert）
async function loadAllWeatherDataSilently() {
    try {
        const response = await fetch('/api/weather-data');
        const result = await response.json();
        
        if (result.success) {
            currentData = result.data;
            
            // 更新統計（移除圖表功能）
            updateStatistics(result.stats);
            
            // 更新篩選選項
            updateLocationFilter(result.data);
            
            // 更新表格
            filterAndDisplayTable();
        }
    } catch (error) {
        console.error('背景載入資料錯誤：', error);
    }
}

// 更新所有天氣資料
async function updateAllWeatherData() {
    showLoading();
    
    try {
        const response = await fetch('/api/update-weather');
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            loadAllWeatherData();
            loadWeatherMap();
            loadWeeklyTemperature();
        } else {
            showAlert(result.error, 'danger');
        }
    } catch (error) {
        showAlert('更新資料時發生錯誤：' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 載入一週溫度預報
async function loadWeeklyTemperature() {
    const chartDiv = document.getElementById('temperatureChart');
    
    try {
        const response = await fetch('/api/weekly-temperature');
        const result = await response.json();
        
        if (!result.success) {
            chartDiv.innerHTML = `<p class="text-center text-muted pt-5">${result.message || result.error}</p>`;
            return;
        }
        
        weeklySeries = result.series;
        
        const select = document.getElementById('weeklyLocation');
        const previous = select.value;
        const locations = Object.keys(weeklySeries);
        select.innerHTML = locations.map(loc => `<option value="${loc}">${loc}</option>`).join('');
        select.value = locations.includes(previous) ? previous
            : (locations.includes(DEFAULT_WEEKLY_LOCATION) ? DEFAULT_WEEKLY_LOCATION : locations[0]);
        
        displayWeeklyChart();
    } catch (error) {
        chartDiv.innerHTML = '<p class="text-center text-muted pt-5">一週預報載入失敗：' + error.message + '</p>';
    }
}

// 繪製選定縣市的一週最高／最低溫折線圖
function displayWeeklyChart() {
    const chartDiv = document.getElementById('temperatureChart');
    const location = document.getElementById('weeklyLocation').value;
    const series = weeklySeries[location];
    if (!series) return;
    
    const traces = [
        {
            x: series.dates,
            y: series.max_temp,
            name: '最高溫',
            type: 'scatter',
            mode: 'lines+markers+text',
            text: series.max_temp.map(v => `${v}°`),
            textposition: 'top center',
            line: { color: '#e74c3c', width: 3 },
            marker: { size: 8 }
        },
        {
            x: series.dates,
            y: series.min_temp,
            name: '最低溫',
            type: 'scatter',
            mode: 'lines+markers+text',
            text: series.min_temp.map(v => `${v}°`),
            textposition: 'bottom center',
            line: { color: '#3498db', width: 3 },
            marker: { size: 8 }
        }
    ];
    
    const allTemps = series.max_temp.concat(series.min_temp);
    const layout = {
        title: { text: `${location} 一週溫度預報` },
        xaxis: { title: { text: '日期' }, type: 'category' },
        yaxis: { title: { text: '溫度 (°C)' }, range: [Math.min(...allTemps) - 3, Math.max(...allTemps) + 3] },
        legend: { orientation: 'h', x: 1, xanchor: 'right', y: 1.12 },
        hovermode: 'x unified',
        margin: { t: 60, r: 20, b: 60, l: 60 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    chartDiv.innerHTML = '';
    Plotly.newPlot(chartDiv, traces, layout, { responsive: true, displaylogo: false });
}

// 更新統計資訊
function updateStatistics(stats) {
    // 更新總記錄數
    document.getElementById('totalRecords').textContent = stats.total_records || 0;
    updateLastUpdateTime();
    
    // 更新溫度統計
    const tempStatsDiv = document.getElementById('tempStats');
    if (stats.temp) {
        tempStatsDiv.innerHTML = createStatsTable(stats.temp, 'temp');
    } else {
        tempStatsDiv.innerHTML = '<p class="text-muted">無溫度統計資料</p>';
    }
    
    // 更新降雨統計
    const popStatsDiv = document.getElementById('popStats');
    if (stats.pop) {
        popStatsDiv.innerHTML = createStatsTable(stats.pop, 'pop');
    } else {
        popStatsDiv.innerHTML = '<p class="text-muted">無降雨統計資料</p>';
    }
}

// 創建統計表格
function createStatsTable(data, type) {
    let headers, keys;
    
    if (type === 'temp') {
        headers = ['縣市', '平均最高溫', '最高溫度', '最低最高溫', '平均最低溫', '最高最低溫', '最低最低溫'];
        keys = ['max_temp_mean', 'max_temp_max', 'max_temp_min', 'min_temp_mean', 'min_temp_max', 'min_temp_min'];
    } else {
        headers = ['縣市', '平均降雨機率', '最高降雨機率', '最低降雨機率'];
        keys = ['mean', 'max', 'min'];
    }
    
    let html = '<table class="table table-sm stats-table"><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // 獲取所有位置
    const locations = Object.keys(data);
    
    locations.forEach(location => {
        html += `<tr><td><strong>${location}</strong></td>`;
        keys.forEach(key => {
            const value = data[location][key];
            const unit = type === 'temp' ? '°C' : '%';
            html += `<td>${value?.toFixed(1) || '-'}${unit}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}

// 更新最後更新時間
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-TW');
    document.getElementById('lastUpdate').textContent = timeString;
}

// 載入天氣地圖
async function loadWeatherMap() {
    const mapDiv = document.getElementById('weatherMap');
    
    try {
        mapDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>載入地圖中...</p></div>';
        
        const response = await fetch('/api/weather-map');
        const mapHtml = await response.text();
        
        mapDiv.innerHTML = mapHtml;
    } catch (error) {
        mapDiv.innerHTML = '<div class="alert alert-danger">地圖載入失敗：' + error.message + '</div>';
    }
}

// 更新位置篩選選項
function updateLocationFilter(data) {
    const select = document.getElementById('locationFilter');
    const currentValue = select.value;
    
    // 清空現有選項（保留"全部"）
    select.innerHTML = '<option value="全部">全部</option>';
    
    // 添加新的位置選項
    const locations = [...new Set(data.map(item => item.location))];
    locations.forEach(location => {
        const option = document.createElement('option');
        option.value = location;
        option.textContent = location;
        select.appendChild(option);
    });
    
    // 恢復之前的選擇
    select.value = currentValue;
}

// 篩選並顯示表格
function filterAndDisplayTable() {
    const locationFilter = document.getElementById('locationFilter').value;
    const sortColumn = document.getElementById('sortColumn').value;
    const tbody = document.getElementById('weatherTableBody');
    
    if (currentData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">無資料</td></tr>';
        return;
    }
    
    // 篩選資料
    let filteredData = currentData.slice();
    if (locationFilter !== '全部') {
        filteredData = filteredData.filter(item => item.location === locationFilter);
    }
    
    // 排序資料
    filteredData.sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        if (typeof aVal === 'string') {
            return aVal.localeCompare(bVal);
        } else {
            return aVal - bVal;
        }
    });
    
    // 生成表格HTML
    tbody.innerHTML = '';
    filteredData.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.location || '-'}</td>
            <td>${formatDateTime(item.start_time)}</td>
            <td>${formatDateTime(item.end_time)}</td>
            <td>${item.weather_description || '-'}</td>
            <td>${item.max_temp?.toFixed(1) || '-'}</td>
            <td>${item.min_temp?.toFixed(1) || '-'}</td>
            <td>${item.pop?.toFixed(0) || '-'}</td>
            <td>${item.comfort_index || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

// 格式化日期時間
function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

// 下載CSV檔案
async function downloadCSV() {
    const locationFilter = document.getElementById('locationFilter').value;
    const sortColumn = document.getElementById('sortColumn').value;
    
    try {
        const params = new URLSearchParams({
            location: locationFilter,
            sort: sortColumn
        });
        
        const response = await fetch(`/api/download-csv?${params}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `weather_data_${new Date().toISOString().slice(0, 16).replace(/[-:]/g, '')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('CSV檔案下載成功', 'success');
        } else {
            throw new Error('下載失敗');
        }
    } catch (error) {
        showAlert('下載CSV檔案時發生錯誤：' + error.message, 'danger');
    }
}