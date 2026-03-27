#!/usr/bin/env python3
"""
簡單測試腳本 - 驗證 MarketDataFetcher 基礎功能
使用更保守的設置避免速率限制
"""

import sys
import os
import json
import time

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_data_fetcher import MarketDataFetcher

def test_single_ticker():
    """測試單個股票代碼"""
    print("🧪 測試單個股票代碼獲取")
    print("=" * 50)
    
    # 使用更長的延遲和更少的重試
    fetcher = MarketDataFetcher(
        cache_enabled=True,
        cache_ttl=600  # 10分鐘緩存
    )
    fetcher.request_delay = 5.0  # 5秒延遲
    fetcher.max_retries = 2      # 2次重試
    fetcher.retry_delay = 10     # 10秒重試延遲
    
    # 測試一個簡單的代碼
    tickers = ["AAPL"]  # 先用 AAPL 測試
    
    for ticker in tickers:
        print(f"獲取 {ticker} 數據...")
        result = fetcher.fetch_single(ticker)
        
        if result["status"] == "success":
            print(f"✅ {ticker} 數據獲取成功")
            data = result["data"]
            print(f"   當前價格: {data.get('current_price', 'N/A')} {data.get('currency', 'USD')}")
            print(f"   市值: {data.get('market_cap', 'N/A')}")
            print(f"   數據時間: {result['timestamp']}")
            
            # 輸出 JSON 格式
            print("\nJSON 格式:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ {ticker} 數據獲取失敗")
            print(f"   錯誤: {result.get('error', '未知錯誤')}")
            
            # 如果是速率限制，建議等待
            if "Rate limited" in result.get("error", "") or "Too Many Requests" in result.get("error", ""):
                print("\n⚠️  檢測到速率限制，建議:")
                print("   1. 等待幾分鐘後再試")
                print("   2. 使用緩存數據")
                print("   3. 減少請求頻率")
        
        print("-" * 50)
        time.sleep(3)  # 額外等待

def test_yfinance_direct():
    """直接測試 yfinance"""
    print("\n🔧 直接測試 yfinance 庫")
    print("=" * 50)
    
    try:
        import yfinance as yf
        
        # 測試最簡單的請求
        print("測試 yfinance.Ticker()...")
        ticker = yf.Ticker("AAPL")
        
        print("測試 info 屬性...")
        info = ticker.info
        print(f"✅ info 獲取成功，鍵數量: {len(info)}")
        
        print("\n可用鍵 (前10個):")
        for i, key in enumerate(list(info.keys())[:10]):
            print(f"  {i+1}. {key}: {info.get(key, 'N/A')}")
        
        # 測試歷史數據
        print("\n測試歷史數據...")
        history = ticker.history(period="1d")
        if not history.empty:
            print(f"✅ 歷史數據獲取成功，數據行數: {len(history)}")
            print(f"   最新收盤價: {history.iloc[-1]['Close']}")
        else:
            print("❌ 歷史數據為空")
            
    except Exception as e:
        print(f"❌ yfinance 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("📊 MarketDataFetcher 功能測試")
    print("=" * 50)
    
    # 先測試 yfinance 直接功能
    test_yfinance_direct()
    
    # 等待避免速率限制
    print("\n⏳ 等待 10 秒避免速率限制...")
    time.sleep(10)
    
    # 測試我們的 fetcher
    test_single_ticker()

if __name__ == "__main__":
    main()