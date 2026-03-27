#!/usr/bin/env python3
"""
極簡測試 - 只測試 yfinance 基礎功能
"""

import sys
import yfinance as yf
import pandas as pd
import json

print("測試 yfinance 庫...")
print("=" * 50)

# 測試 1: 檢查 yfinance 版本
print(f"yfinance 版本: {yf.__version__}")

# 測試 2: 嘗試獲取單個股票數據
try:
    print("\n嘗試獲取 AAPL 數據...")
    ticker = yf.Ticker("AAPL")
    
    # 獲取基本信息
    print("獲取 info...")
    info = ticker.info
    print(f"✅ info 獲取成功，包含 {len(info)} 個鍵")
    
    # 顯示關鍵信息
    important_keys = ['currentPrice', 'previousClose', 'marketCap', 'trailingPE', 'forwardPE', 
                     'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'currency', 'shortName']
    
    print("\n關鍵數據:")
    for key in important_keys:
        value = info.get(key, 'N/A')
        print(f"  {key}: {value}")
    
    # 獲取歷史數據
    print("\n獲取歷史數據...")
    history = ticker.history(period="2d")
    if not history.empty:
        print(f"✅ 歷史數據獲取成功，{len(history)} 行")
        print(f"  最新數據 (索引 {history.index[-1]}):")
        print(f"  收盤價: {history.iloc[-1]['Close']}")
        if len(history) >= 2:
            print(f"  前日收盤價: {history.iloc[-2]['Close']}")
    else:
        print("❌ 歷史數據為空")
        
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("測試完成")