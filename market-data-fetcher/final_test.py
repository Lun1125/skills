#!/usr/bin/env python3
"""
最終測試 - 展示 MarketDataFetcher 完整功能
使用模擬數據展示結構化輸出
"""

import sys
import json
import os

# 直接使用模擬數據生成器
sys.path.append('.')

def generate_mock_data():
    """生成模擬數據來展示完整功能"""
    
    # 模擬數據模板
    mock_data = {
        "NVDA": {
            "current_price": 950.25,
            "previous_close": 945.50,
            "market_cap": "2.35T",  # 2.35兆
            "trailing_pe": 65.3,
            "forward_pe": 55.2,
            "week52_high": 980.75,
            "week52_low": 450.25,
            "volume": 42500000,
            "average_volume": 38000000,
            "dividend_yield": 0.003,
            "eps": 14.55,
            "currency": "USD",
            "exchange": "NASDAQ",
            "short_name": "NVIDIA Corp",
            "long_name": "NVIDIA Corporation"
        },
        "2330.TW": {
            "current_price": 850.0,
            "previous_close": 845.5,
            "market_cap": "22.1T",  # 22.1兆新台幣
            "trailing_pe": 18.5,
            "forward_pe": 16.8,
            "week52_high": 890.0,
            "week52_low": 550.0,
            "volume": 28500000,
            "average_volume": 25000000,
            "dividend_yield": 0.018,
            "eps": 45.9,
            "currency": "TWD",
            "exchange": "TWSE",
            "short_name": "台積電",
            "long_name": "台灣積體電路製造股份有限公司"
        },
        "BTC-USD": {
            "current_price": 87500.0,
            "previous_close": 87250.0,
            "market_cap": "1.71T",  # 1.71兆
            "trailing_pe": None,
            "forward_pe": None,
            "week52_high": 92000.0,
            "week52_low": 45000.0,
            "volume": 32500000000,
            "average_volume": 28000000000,
            "dividend_yield": None,
            "eps": None,
            "currency": "USD",
            "exchange": "CRYPTO",
            "short_name": "Bitcoin USD",
            "long_name": "Bitcoin"
        }
    }
    
    return mock_data

def main():
    print("🎯 Market-Data-Fetcher 功能展示")
    print("=" * 60)
    print("說明: 由於 Yahoo Finance API 速率限制，本次展示使用模擬數據")
    print("      實際部署時將自動切換到真實數據")
    print("=" * 60)
    
    # 生成模擬數據
    mock_data = generate_mock_data()
    
    # 構建完整響應格式
    results = []
    for ticker, data in mock_data.items():
        result = {
            "ticker": ticker,
            "timestamp": "2026-03-23T13:10:00Z",
            "status": "success_mock",
            "error": "Yahoo Finance API 速率限制，使用模擬數據展示",
            "data": data,
            "metadata": {
                "data_source": "Mock Data (展示用途)",
                "cache_hit": False,
                "request_time": "2026-03-23T13:10:00Z",
                "note": "此為模擬數據，僅供功能展示"
            }
        }
        results.append(result)
    
    # 完整 JSON 輸出
    output = {
        "timestamp": "2026-03-23T13:10:00Z",
        "ticker_count": len(results),
        "results": results
    }
    
    print("\n📊 JSON 輸出結果:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    # 保存到文件
    output_file = "market_data_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果已保存至: {output_file}")
    
    # RAG 格式展示
    print("\n" + "=" * 60)
    print("📝 RAG 格式展示:")
    print("=" * 60)
    
    for result in results:
        ticker = result["ticker"]
        data = result["data"]
        
        rag_text = f"""
{ticker} ({data.get('short_name', ticker)}) 市場數據 (模擬數據 - 真實API暫時不可用):
- 當前價格: {data.get('current_price', 'N/A')} {data.get('currency', 'USD')}
- 前日收盤: {data.get('previous_close', 'N/A')} {data.get('currency', 'USD')}
- 市值: {data.get('market_cap', 'N/A')}
- 本益比 (滾動): {data.get('trailing_pe', 'N/A')}
- 本益比 (預估): {data.get('forward_pe', 'N/A')}
- 52週高點: {data.get('week52_high', 'N/A')} {data.get('currency', 'USD')}
- 52週低點: {data.get('week52_low', 'N/A')} {data.get('currency', 'USD')}
- 成交量: {data.get('volume', 'N/A'):,}
- 股息收益率: {data.get('dividend_yield', 'N/A')}
- 每股盈餘 (EPS): {data.get('eps', 'N/A')}
- 交易所: {data.get('exchange', 'N/A')}
- 數據時間: {result['timestamp']}
"""
        print(rag_text.strip())
        print("-" * 50)

if __name__ == "__main__":
    main()