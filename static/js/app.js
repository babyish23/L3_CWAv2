// 全域變數
let currentData = [];
let loadingModal;

// 初始化應用
document.addEventListener('DOMContentLoaded', function() {
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    initializeEventListeners();
    updateLastUpdateTime();
});

// 初始化事件監聽器
function initializeEventListeners() {
    // 載入資料按鈕
    document.getElementById('loadDataBtn').addEventListener('click', loadWeatherData);
    
    // 更新資料按鈕
    document.getElementById('updateDataBtn').addEventListener('click', updateWeatherData);
    
    // 下載按鈕
    document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
    
    // 篩選和排序
    document.getElementById('locationFilter').addEventListener('change', filterAndDisplayTable);
    document.getElementById('sortColumn').addEventListener('change', filterAndDisplayTable);
    
    // 標籤頁切換事件
    document.getElementById('map-tab').addEventListener('shown.bs.tab', loadWeatherMap);
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

// 獲取選中的縣市
function getSelectedLocations() {
    const select = document.getElementById('locationSelect');
    const selected = [];
    
    for (let option of select.options) {
        if (option.selected) {
            selected.push(option.value);
        }
    }
    
    return selected;
}

// 載入天氣資料
async function loadWeatherData() {
    const selectedLocations = getSelectedLocations();
    
    if (selectedLocations.length === 0) {
        showAlert('請先選擇縣市', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const params = new URLSearchParams();
        selectedLocations.forEach(loc => params.append('locations', loc));
        
        const response = await fetch(`/api/weather-data?${params}`);
        const result = await response.json();
        
        if (result.success) {
            currentData = result.data;
            
            // 更新圖表
            if (result.chart) {
                displayChart(result.chart);
            }
            
            // 更新統計
            updateStatistics(result.stats);
            
            // 更新篩選選項
            updateLocationFilter(result.data);
            
            // 更新表格
            filterAndDisplayTable();
            
            showAlert(`成功載入 ${result.data.length} 筆資料`, 'success');
        } else {
            showAlert(result.message || result.error, 'danger');
        }
    } catch (error) {
        showAlert('載入資料時發生錯誤：' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 更新天氣資料
async function updateWeatherData() {
    const selectedLocations = getSelectedLocations();
    
    if (selectedLocations.length === 0) {
        showAlert('請先選擇縣市', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const params = new URLSearchParams();
        selectedLocations.forEach(loc => params.append('locations', loc));
        
        const response = await fetch(`/api/update-weather?${params}`);
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            // 更新完成後重新載入資料
            setTimeout(() => {
                loadWeatherData();
            }, 1000);
        } else {
            showAlert(result.error, 'danger');
        }
    } catch (error) {
        showAlert('更新資料時發生錯誤：' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 顯示圖表
function displayChart(chartData) {
    const chartDiv = document.getElementById('temperatureChart');
    
    try {
        Plotly.newPlot(chartDiv, chartData.data, chartData.layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        });
    } catch (error) {
        console.error('圖表顯示錯誤:', error);
        chartDiv.innerHTML = '<p class="text-center text-muted">圖表載入失敗</p>';
    }
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
        keys = [
            ['max_temp', 'mean'],
            ['max_temp', 'max'], 
            ['max_temp', 'min'],
            ['min_temp', 'mean'],
            ['min_temp', 'max'],
            ['min_temp', 'min']
        ];
    } else {
        headers = ['縣市', '平均降雨機率', '最高降雨機率', '最低降雨機率'];
        keys = [
            ['pop', 'mean'],
            ['pop', 'max'],
            ['pop', 'min']
        ];
    }
    
    let html = '<table class="table table-sm stats-table"><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // 獲取所有位置
    const locations = Object.keys(data[keys[0][0]]);
    
    locations.forEach(location => {
        html += `<tr><td><strong>${location}</strong></td>`;
        keys.forEach(key => {
            const value = data[key[0]][key[1]][location];
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
    const selectedLocations = getSelectedLocations();
    const mapDiv = document.getElementById('weatherMap');
    
    if (selectedLocations.length === 0) {
        mapDiv.innerHTML = '<div class="alert alert-warning">請先選擇縣市並載入資料</div>';
        return;
    }
    
    try {
        mapDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>載入地圖中...</p></div>';
        
        const params = new URLSearchParams();
        selectedLocations.forEach(loc => params.append('locations', loc));
        
        const response = await fetch(`/api/weather-map?${params}`);
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