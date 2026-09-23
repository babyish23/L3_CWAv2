#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """測試套件導入"""
    try:
        import requests
        print("OK: requests OK")
    except ImportError as e:
        print(f"FAIL: requests failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("OK: pandas OK")
    except ImportError as e:
        print(f"FAIL: pandas failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("OK: python-dotenv OK")
    except ImportError as e:
        print(f"FAIL: python-dotenv failed: {e}")
        return False
    
    return True

def test_env():
    """測試環境變數"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('CWA_API_KEY')
    if api_key:
        print(f"OK: API Key loaded: {api_key[:20]}...")
        return True
    else:
        print("FAIL: API Key not found")
        return False

def test_basic_api():
    """測試基本API請求"""
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('CWA_API_KEY')
    
    if not api_key:
        print("FAIL: No API key")
        return False
    
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        'Authorization': api_key,
        'format': 'JSON',
        'locationName': '桃園市'
    }
    
    try:
        print("Requesting CWA API...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == 'true':
                print("OK: API request successful")
                records = data.get('records', {})
                locations = records.get('location', [])
                print(f"OK: Got data for {len(locations)} location(s)")
                return True
            else:
                print(f"FAIL: API returned error: {data}")
                return False
        else:
            print(f"FAIL: HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAIL: Request failed: {e}")
        return False

if __name__ == "__main__":
    print("=== L3_CWAv2 系統測試 ===\n")
    
    print("1. 套件導入測試:")
    if not test_imports():
        print("套件導入失敗，請檢查安裝")
        sys.exit(1)
    
    print("\n2. 環境變數測試:")
    if not test_env():
        print("環境變數設定失敗，請檢查 .env 檔案")
        sys.exit(1)
    
    print("\n3. API 連線測試:")
    if not test_basic_api():
        print("API 測試失敗")
        sys.exit(1)
    
    print("\n=== 所有測試通過！ ===")
    print("可以執行: streamlit run streamlit_app.py")