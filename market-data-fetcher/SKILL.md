---
name: Market-Data-Fetcher
description: 即時市場數據檢索技能，使用 yfinance 套件抓取股票、ETF、加密貨幣的即時財務數據，作為 RAG（檢索增強生成）的資料源，消除 AI 幻覺。支援多種資產類別與全球市場代碼。
---

# Market-Data-Fetcher (即時市場數據檢索)

## 概述

Market-Data-Fetcher 是一個專門用於獲取即時市場數據的技能，透過 Yahoo Finance API (yfinance 套件) 抓取股票、ETF、加密貨幣等各類資產的財務數據。本技能旨在為 AI 分析提供準確、即時的數據源，減少 AI 幻覺並提高分析準確性。

## 核心功能

### 1. 多資產數據獲取
- **股票**: NYSE、NASDAQ、NYSE American 等交易所股票
- **國際股票**: 台灣 (2330.TW)、香港 (0700.HK)、日本 (7203.T) 等
- **ETF**: SPY、QQQ、ARKK 等交易所交易基金
- **加密貨幣**: BTC-USD、ETH-USD 等加密貨幣對
- **指數**: ^GSPC (S&P 500)、^DJI (道瓊)、^IXIC (納斯達克)

### 2. 關鍵指標提取
針對每個資產代碼，提取以下即時數據：
- **當前價格 (Current Price)**: 最新成交價
- **前日收盤價 (Previous Close)**: 前一個交易日的收盤價
- **市值 (Market Cap)**: 市場總市值
- **本益比 (P/E Ratio)**: 滾動本益比或預估本益比
- **52週高低點 (52 Week High/Low)**: 過去52週的最高價和最低價
- **成交量 (Volume)**: 當日成交量
- **每股盈餘 (EPS)**: 每股收益
- **股息收益率 (Dividend Yield)**: 股息收益率

### 3. 數據格式化
- **結構化 JSON**: 將數據整理為標準化的 JSON 格式
- **時間戳記**: 包含數據獲取時間戳
- **錯誤處理**: 無效代碼或 API 錯誤時提供友好的錯誤訊息

## 快速開始

### 安裝依賴
```bash
pip install yfinance pandas
```

### 基礎使用
```python
from market_data_fetcher import MarketDataFetcher

# 初始化獲取器
fetcher = MarketDataFetcher()

# 獲取單個股票數據
data = fetcher.fetch_single("NVDA")
print(data)

# 獲取多個股票數據
data_list = fetcher.fetch_multiple(["NVDA", "2330.TW", "BTC-USD"])
print(data_list)

# 批量獲取 (支援最多 10 個代碼)
batch_data = fetcher.fetch_batch(["AAPL", "TSLA", "MSFT", "GOOGL"])
```

### 命令行使用
```bash
# 獲取單個股票
python scripts/market_data_fetcher.py NVDA

# 獲取多個股票
python scripts/market_data_fetcher.py NVDA 2330.TW BTC-USD

# 從文件讀取代碼列表
python scripts/market_data_fetcher.py --file tickers.txt
```

## 數據源與限制

### 支持的數據源
- **主要源**: Yahoo Finance (透過 yfinance 套件)
- **更新頻率**: 即時 (延遲約15-20分鐘)
- **歷史數據**: 支援日線、週線、月線數據
- **免費使用**: 無需 API 金鑰

### 限制與注意事項
1. **速率限制**: 避免過度頻繁請求，建議間隔至少1秒
2. **數據準確性**: Yahoo Finance 數據僅供參考，投資決策應使用官方數據
3. **市場時間**: 非交易時段數據可能不更新
4. **國際代碼**: 需使用正確的後綴 (.TW、.HK、.T 等)

## 進階功能

### 自定義指標
```python
# 獲取額外技術指標
extra_data = fetcher.fetch_with_custom_indicators(
    "NVDA",
    indicators=["RSI", "MACD", "BollingerBands"]
)

# 獲取財務報表數據
financials = fetcher.fetch_financials("AAPL")
```

### 緩存機制
```python
# 啟用緩存 (預設 5 分鐘)
fetcher = MarketDataFetcher(cache_enabled=True, cache_ttl=300)

# 手動清除緩存
fetcher.clear_cache()
```

### 錯誤處理與重試
```python
# 自定義錯誤處理
try:
    data = fetcher.fetch_single("INVALID_CODE")
except MarketDataError as e:
    print(f"數據獲取失敗: {e}")
    # 使用備用數據源或返回預設值
```

## 整合示例

### 與 RAG 系統整合
```python
from market_data_fetcher import MarketDataFetcher
from rag_system import RAGSystem

class MarketEnhancedRAG:
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.rag = RAGSystem()
    
    def analyze_stock(self, ticker, question):
        # 獲取即時數據
        market_data = self.fetcher.fetch_single(ticker)
        
        # 將數據轉換為文本上下文
        context = self._format_market_context(market_data)
        
        # 使用 RAG 進行分析
        answer = self.rag.query(question, context=context)
        
        return {
            "answer": answer,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat()
        }
```

### 與交易系統整合
```python
class TradingSystem:
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.positions = {}
    
    def monitor_positions(self):
        for ticker in self.positions.keys():
            data = self.fetcher.fetch_single(ticker)
            
            # 檢查停損停利
            current_price = data["current_price"]
            entry_price = self.positions[ticker]["entry_price"]
            
            if current_price <= entry_price * 0.95:  # 5% 停損
                self.sell(ticker, "stop_loss")
            elif current_price >= entry_price * 1.10:  # 10% 停利
                self.sell(ticker, "take_profit")
```

## 配置選項

### 配置文件 (config/fetcher_config.json)
```json
{
  "rate_limit": 1.0,
  "timeout": 10,
  "cache_enabled": true,
  "cache_ttl": 300,
  "default_indicators": [
    "current_price",
    "previous_close",
    "market_cap",
    "pe_ratio",
    "week52_high",
    "week52_low"
  ],
  "fallback_enabled": true,
  "logging_level": "INFO"
}
```

## 錯誤代碼與處理

| 錯誤代碼 | 描述 | 處理建議 |
|----------|------|----------|
| DATA_UNAVAILABLE | 數據暫時無法獲取 | 稍後重試，檢查代碼格式 |
| INVALID_TICKER | 無效的代碼格式 | 驗證代碼格式與交易所後綴 |
| API_TIMEOUT | API 請求超時 | 檢查網絡連接，增加 timeout |
| RATE_LIMITED | 請求過於頻繁 | 增加請求間隔時間 |

## 性能優化

### 批量處理建議
```python
# 不佳：逐一請求
for ticker in ticker_list:
    data = fetcher.fetch_single(ticker)  # 每個請求間隔短

# 推薦：批量請求
batch_data = fetcher.fetch_batch(ticker_list)  # 單次請求多個代碼
```

### 緩存策略
- **短期緩存**: 5分鐘 TTL 適合即時數據
- **長期緩存**: 1小時 TTL 適合日終數據
- **自定義緩存**: 根據需求調整 TTL

## 更新日誌

### v1.0.0 (2026-03-23)
- 初始版本發布
- 支援股票、ETF、加密貨幣數據獲取
- 基本錯誤處理與緩存機制
- 結構化 JSON 輸出格式

## 貢獻與支持

### 問題回報
如遇數據獲取問題，請提供：
1. 使用的代碼列表
2. 錯誤訊息截圖
3. 操作環境資訊

### 功能建議
歡迎提出新功能建議，特別是：
1. 新的數據指標
2. 額外的數據源
3. 性能優化方案

---

**重要聲明**: 本技能提供的市場數據僅供參考，不構成投資建議。投資有風險，入市需謹慎。