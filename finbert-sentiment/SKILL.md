---
name: finbert-sentiment
description: FinBERT 情緒量化技能，使用 Hugging Face 的 FinBERT 模型分析財經新聞、財報文字與市場資訊，輸出情緒分數與信心度，並與節能系統連動。當系統處理美股、加密貨幣、台股相關新聞時使用此技能。核心功能：1) FinBERT 情緒分析 2) 情緒分數量化 (-1 到 1) 3) 雜訊檢測與節能連動 4) 批量新聞處理。
---

# FinBERT 情緒量化技能

## Overview

FinBERT 情緒量化技能專為財經文本分析設計，使用預訓練的 FinBERT 模型（yiyanghkust/finbert-tone）自動分析新聞、財報、市場評論的情緒傾向。技能輸出標準化的情緒分數（-1 到 1）與信心度，並能自動識別雜訊內容以優化系統資源使用。

## 核心功能

### 1. FinBERT 情緒分析
- **模型選擇**: Hugging Face 的 `yiyanghkust/finbert-tone`（專為財經文本訓練）
- **輸出標準**: 情緒分數 (-1 到 1) + 信心度 (0 到 1)
- **情緒類別**: 強負面、負面、輕微負面、中性、輕微正面、正面、強正面
- **API 優先**: 使用 Hugging Face API，節省本地系統資源

### 2. 雜訊檢測與節能連動
- **雜訊閾值**: 情緒分數在 -0.2 到 0.2 之間
- **節能決策**: 檢測到雜訊時自動阻止 `deepseek-reasoner` 調用
- **信心度要求**: 僅當信心度 ≥ 0.7 時執行節能決策
- **資源優化**: 避免對無關緊要的新聞進行深度分析

### 3. 批量處理與緩存
- **批量分析**: 支援同時處理多條新聞
- **智能緩存**: 自動緩存分析結果，24小時 TTL
- **API 節流**: 自動添加請求延遲，避免 API 限制
- **錯誤處理**: API 不可用時自動切換到模擬分析

### 4. 系統整合
- **與現有技能協同**: 可與 `US-Stock-Sentiment-Earnings`、`TW-Stock-Institutional-Analysis` 等技能整合
- **標準化輸出**: JSON 格式結果，便於其他系統處理
- **摘要報告**: 自動生成情緒分析統計報告

## 快速開始

### 安裝與配置
```bash
# 1. 獲取 Hugging Face API 令牌
# 訪問 https://huggingface.co/settings/tokens 創建令牌

# 2. 編輯配置文件
nano finbert_config.json
# 設置 "huggingface_api_token": "您的令牌"

# 3. 測試技能
python3 scripts/finbert_processor.py demo
```

### 基本使用示例
```python
from scripts.finbert_processor import FinBERTProcessor

# 初始化處理器
processor = FinBERTProcessor()

# 分析單條新聞
news_text = "蘋果公司發布強勁財報，營收增長超過預期"
result = processor.analyze_sentiment(news_text)

print(f"情緒分數: {result['sentiment_score']}")
print(f"信心度: {result['confidence']}")
print(f"是否雜訊: {processor.is_noise(result)}")

# 檢查是否需要阻止 deepseek-reasoner
should_block, reason = processor.should_block_deepseek_reasoner(result)
if should_block:
    print(f"🚫 阻止 deepseek-reasoner: {reason}")
```

### 批量處理示例
```python
# 批量分析新聞
news_items = [
    {"id": "news1", "text": "市場交易平淡，沒有明顯方向"},
    {"id": "news2", "text": "重磅利好！公司獲得巨額訂單"},
    {"id": "news3", "text": "風險警告：行業監管收緊"}
]

results = processor.analyze_news_batch(news_items)

# 生成摘要報告
summary = processor.generate_summary_report(results)
print(summary["summary"])
```

## 腳本資源

### scripts/finbert_processor.py
FinBERT 情緒量化處理器核心模組，負責：
- 調用 Hugging Face API 進行 FinBERT 情緒分析
- 計算情緒分數 (-1 到 1) 與信心度
- 檢測雜訊內容並執行節能決策
- 批量處理新聞與生成摘要報告

**主要類別**:
- `FinBERTProcessor`: 主處理器類
- 方法: `analyze_sentiment()`, `analyze_news_batch()`, `should_block_deepseek_reasoner()`

**關鍵方法**:
- `analyze_sentiment(text)`: 分析單個文本情緒
- `is_noise(result)`: 判斷是否為雜訊內容
- `should_block_deepseek_reasoner(result)`: 檢查是否需要阻止 deepseek-reasoner
- `generate_summary_report(results)`: 生成情緒分析摘要

## 配置說明

### finbert_config.json
```json
{
  "model_name": "yiyanghkust/finbert-tone",
  "huggingface_api_token": "您的_HuggingFace_令牌",
  "sentiment_thresholds": {
    "strong_negative": -0.5,
    "negative": -0.2,
    "neutral_low": -0.2,
    "neutral_high": 0.2,
    "positive": 0.2,
    "strong_positive": 0.5
  },
  "energy_saving": {
    "noise_threshold_low": -0.2,
    "noise_threshold_high": 0.2,
    "block_deepseek_reasoner": true,
    "min_confidence_for_block": 0.7
  }
}
```

### 情緒分數解釋
| 分數範圍 | 情緒類別 | 節能決策 |
|----------|----------|----------|
| ≤ -0.5 | 強負面 | 允許深度分析 |
| -0.5 ~ -0.2 | 負面 | 允許深度分析 |
| -0.2 ~ 0.2 | 中性/雜訊 | 🚫 阻止 deepseek-reasoner |
| 0.2 ~ 0.5 | 正面 | 允許深度分析 |
| ≥ 0.5 | 強正面 | 允許深度分析 |

## 與現有技能整合

### 1. 與 US-Stock-Sentiment-Earnings 整合
```python
# 在獲取財報新聞後進行情緒分析
from finbert_processor import FinBERTProcessor

processor = FinBERTProcessor()
earnings_news = get_earnings_news()  # 從現有技能獲取

for news in earnings_news:
    result = processor.analyze_sentiment(news["text"])
    
    if not processor.is_noise(result):
        # 只有重要新聞才進行深度分析
        deep_analysis = call_deepseek_reasoner(news)
```

### 2. 與 Learning-Feedback-Loop 整合
```python
# 記錄情緒分析結果到學習日誌
sentiment_results = processor.analyze_news_batch(market_news)
summary = processor.generate_summary_report(sentiment_results)

# 更新學習日誌
log_entry = {
    "type": "sentiment_analysis",
    "timestamp": datetime.now().isoformat(),
    "summary": summary,
    "energy_saved": summary["block_percentage"]
}
append_to_learning_log(log_entry)
```

### 3. 與 System-Orchestrator 整合
```python
# 在系統編排器中添加情緒檢查
def before_model_call(requested_model, context_text):
    processor = FinBERTProcessor()
    sentiment_result = processor.analyze_sentiment(context_text)
    
    if processor.should_block_deepseek_reasoner(sentiment_result):
        return "deepseek-chat"  # 降級到 chat 模型
    else:
        return requested_model
```

## 使用場景示例

### 場景1: 財報季新聞過濾
```
輸入: 100條財報相關新聞
處理: FinBERT 情緒分析
輸出: 
  - 20條強烈情緒新聞 → 深度分析
  - 60條中性新聞 → 簡要摘要
  - 20條雜訊新聞 → 忽略
節省: 80% 的 deepseek-reasoner 調用
```

### 場景2: 市場情緒監控
```
輸入: 實時市場新聞流
處理: 每小時批量分析
輸出: 市場情緒指數趨勢圖
行動: 情緒極端時觸發警報
```

### 場景3: 投資決策支援
```
輸入: 公司相關新聞與分析報告
處理: FinBERT 情緒量化
輸出: 情緒分數時間序列
應用: 作為技術分析的補充指標
```

## 性能優化建議

1. **API 令牌管理**: 使用環境變數儲存敏感令牌
2. **緩存策略**: 對重複新聞內容使用緩存
3. **批量處理**: 盡量使用批量分析減少 API 調用
4. **錯誤處理**: 實現優雅的降級機制（API 不可用時使用模擬分析）
5. **監控日誌**: 記錄分析統計與節能效果

## 注意事項

1. **API 限制**: Hugging Face API 有速率限制，請合理控制請求頻率
2. **文本長度**: 過長文本會被自動截斷（默認 512 字符）
3. **語言支援**: FinBERT 主要針對英文財經文本，中文效果可能較差
4. **信心度閾值**: 節能決策僅在信心度 ≥ 0.7 時執行，避免誤判
