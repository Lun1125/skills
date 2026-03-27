#!/usr/bin/env python3
"""
快速測試 - 直接測試 MarketDataFetcher 功能
使用極簡配置避免速率限制
"""

import sys
import json

# 添加當前目錄到路徑
sys.path.append('.')

from scripts.market_data_fetcher import MarketDataFetcher

def main():
    print("🚀 Market-Data-Fetcher 快速測試")
    print("=" * 60)
    
    # 使用極簡配置
    fetcher = MarketDataFetcher(
        cache_enabled=False,  # 禁用緩存
        cache_ttl=60
    )
    fetcher.request_delay = 0.1  # 很短延遲
    fetcher.max_retries = 1      # 只重試1次
    fetcher.retry_delay = 1      # 1秒重試
    
    # 測試股票代碼
    test_tickers = ["NVDA", "2330.TW", "BTC-USD"]
    
    print(f"測試股票代碼: {test_tickers}")
    print("\n開始獲取數據...")
    
    results = []
    for ticker in test_tickers:
        print(f"\n正在獲取 {ticker}...")
        try:
            result = fetcher.fetch_single(ticker)
            results.append(result)
            
            # 簡單狀態顯示
            status_emoji = "✅" if result["status"] in ["success", "success_mock"] else "❌"
            print(f"  {status_emoji} 狀態: {result['status']}")
            
            if result["data"]:
                data = result["data"]
                print(f"  價格: {data.get('current_price', 'N/A')} {data.get('currency', 'USD')}")
                print(f"  市值: {data.get('market_cap', 'N/A')}")
        
        except Exception as e:
            print(f"  ❌ 異常: {e}")
            results.append({
                "ticker": ticker,
                "status": "error",
                "error": str(e),
                "data": None
            })
    
    # 生成 JSON 輸出
    output = {
        "timestamp": "2026-03-23T13:05:00Z",
        "ticker_count": len(results),
        "results": results
    }
    
    print("\n" + "=" * 60)
    print("📊 JSON 輸出結果:")
    print("=" * 60)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    # 保存到文件
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果已保存至: test_results.json")
    
    # 簡單統計
    success_count = sum(1 for r in results if r["status"] in ["success", "success_mock"])
    print(f"\n📈 統計:")
    print(f"  總數: {len(results)}")
    print(f"  成功: {success_count}")
    print(f"  失敗: {len(results) - success_count}")

if __name__ == "__main__":
    main()