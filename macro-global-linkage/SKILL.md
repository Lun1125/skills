---
name: macro-global-linkage
description: 全球宏觀風險分析技能，監測 DXY、^TNX、^VIX、BTC-USD、GC=F、CL=F 等6大指標，計算風險分數，生成投資建議與風險地圖。當用戶需要分析全球宏觀風險、市場連動、風險評估或獲取投資配置建議時使用此技能。支援歷史數據對比、動能警報、異步併發處理與主動警報通知。
---

# Macro-Global-Linkage 技能

全球總經連動分析模組，提供即時宏觀風險評估與投資決策支援。

## 核心功能

### 1. 6大宏觀指標監控
- **DXY (美元指數)**: 美元強弱與避險情緒
- **^TNX (美國10年期公債殖利率)**: 通脹預期與經濟前景
- **^VIX (恐慌指數)**: 市場波動性與避險情緒
- **BTC-USD (比特幣)**: 高風險資產與市場情緒
- **GC=F (黃金期貨)**: 避險情緒與通脹預期
- **CL=F (原油期貨)**: 通脹壓力與經濟活動

### 2. 風險評估系統
- **風險分數計算**: 0-100 分風險評分系統
- **風險燈號**: 綠、黃綠、黃、橙、紅五級風險燈號
- **動態權重**: 根據指標重要性分配不同權重
- **歷史對比**: 即時數據與前日收盤價對比，計算變化率

### 3. 投資建議引擎
- **資產配置建議**: 根據風險等級提供股票、債券、現金、加密貨幣配置比例
- **具體行動指南**: 風險等級對應的具體投資行動
- **風險情境檢測**: 自動檢測系統性風險、Risk-On環境、市場恐慌等特殊情境
- **動能警報**: 單日變化率超過15%時觸發動能警報

### 4. 技術特性
- **異步併發處理**: 使用 asyncio 併發請求，1秒內完成6大指標抓取
- **緩存持久化**: 文件緩存系統，容器重啟數據不丟失
- **故障安全機制**: API失敗時拋出 CriticalDataError，避免使用過時數據
- **主動警報框架**: 整合 AlertNotifier 支援 LINE Notify/Telegram/Webhook 通知

## 快速開始

### 命令行使用
```bash
# 人類可讀格式輸出
python scripts/macro_global_linkage.py

# JSON 格式輸出
python scripts/macro_global_linkage.py --json

# 測試模式 (使用模擬數據)
python scripts/macro_global_linkage.py --test

# 安靜模式 (僅輸出 JSON)
python scripts/macro_global_linkage.py --quiet
```

### Python API 使用
```python
from scripts.macro_global_linkage import MacroGlobalLinkage

# 初始化分析器
analyzer = MacroGlobalLinkage()

# 生成完整風險地圖
risk_map = analyzer.generate_risk_map()

# 輸出人類可讀格式
analyzer.print_human_readable(risk_map)

# 僅獲取風險分數
risk_analysis = analyzer.calculate_risk_score(macro_data)
```

### 即時分析示例
```python
from scripts.macro_global_linkage import MacroGlobalLinkage

analyzer = MacroGlobalLinkage()
risk_map = analyzer.generate_risk_map()

print(f"整體風險等級: {risk_map['risk_analysis']['risk_level']}")
print(f"風險分數: {risk_map['risk_analysis']['risk_score']}/100")
print(f"建議: {risk_map['risk_analysis']['recommendations']['overall']}")
```

## 輸出格式

### 人類可讀格式
```
🌍 全球宏觀風險地圖 (Macro Global Risk Map)
📊 整體風險評估:
   🟡 風險燈號: YELLOW (中風險)
   📈 風險分數: 58.5/100
   
📈 核心宏觀指標:
   ✅ DXY (美元指數): 103.50 (上升 +0.24%)
   ✅ ^TNX (美國10年期公債殖利率): 4.35 (上升 +1.16%)
   ✅ ^VIX (恐慌指數): 18.50 (上升 +1.65%)
   ✅ BTC-USD (比特幣): 87500.0 (上升 +0.29%)
```

### JSON 結構
```json
{
  "metadata": {
    "generated_at": "2026-03-23T15:00:00.000000",
    "module": "Macro-Global-Linkage",
    "version": "1.5.0",
    "indicators_analyzed": ["DXY", "^TNX", "^VIX", "BTC-USD", "GC=F", "CL=F"]
  },
  "macro_data_summary": {
    "DXY": {
      "name": "美元指數",
      "current_price": 103.50,
      "status": "success",
      "description": "美元對一籃子貨幣的匯率指數，反映美元強弱"
    }
  },
  "risk_analysis": {
    "overall_risk": "medium",
    "risk_level": "中風險",
    "risk_score": 58.5,
    "risk_color": "yellow",
    "indicators": {
      "DXY": {
        "score": 65,
        "level": "medium_high",
        "price": 103.50,
        "weight": 0.2,
        "delta_pct": 0.24,
        "trend": "上升",
        "momentum_alert": false
      }
    },
    "recommendations": {
      "overall": "🟡 中風險環境：謹慎投資，降低風險暴露",
      "asset_allocation": {
        "stocks": "40-50%",
        "bonds": "30-35%",
        "cash": "15-20%",
        "crypto": "0-5%"
      }
    }
  }
}
```

## 配置選項

### 指標權重配置 (config/indicator_weights.json)
```json
{
  "DXY": 0.2,
  "^TNX": 0.2,
  "^VIX": 0.2,
  "BTC-USD": 0.15,
  "GC=F": 0.15,
  "CL=F": 0.1
}
```

### 風險閾值配置 (config/risk_thresholds.json)
```json
{
  "DXY": {
    "low": 95.0,
    "medium": 100.0,
    "high": 105.0
  },
  "^TNX": {
    "low": 3.0,
    "medium": 4.0,
    "high": 5.0
  }
}
```

### 警報配置 (config/alert_config.json)
```json
{
  "enabled": true,
  "momentum_alert_threshold": 15.0,
  "notification_channels": ["telegram", "line"],
  "webhook_url": "",
  "min_risk_level_for_alert": "medium_high"
}
```

## 依賴關係

### Python 套件
```bash
pip install yfinance pandas asyncio requests
```

### 內部依賴
- **Market-Data-Fetcher 技能**: 用於獲取市場數據
- **AlertNotifier 模組**: 用於警報通知（可選）

### 環境變數
```bash
# Telegram 通知 (可選)
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# LINE Notify (可選)
export LINE_NOTIFY_TOKEN="your_token"
```

## 進階用法

### 自定義指標集合
```python
analyzer = MacroGlobalLinkage()

# 替換核心指標
analyzer.core_indicators = {
    "DXY": {"name": "美元指數", "weight": 0.3, "risk_direction": "positive"},
    "NEW_INDICATOR": {"name": "新指標", "weight": 0.7, "risk_direction": "negative"}
}

# 重新計算風險
risk_map = analyzer.generate_risk_map()
```

### 歷史數據分析
```python
from scripts.macro_global_linkage import MacroGlobalLinkage
import pandas as pd

analyzer = MacroGlobalLinkage()

# 獲取多個時間點的風險分數
timestamps = []
risk_scores = []

for _ in range(5):
    risk_map = analyzer.generate_risk_map()
    timestamps.append(risk_map['metadata']['generated_at'])
    risk_scores.append(risk_map['risk_analysis']['risk_score'])
    time.sleep(300)  # 每5分鐘一次

# 創建趨勢圖表
df = pd.DataFrame({
    'timestamp': pd.to_datetime(timestamps),
    'risk_score': risk_scores
})
```

### 與交易系統整合
```python
class TradingSystemWithMacro:
    def __init__(self):
        self.macro_analyzer = MacroGlobalLinkage()
        self.portfolio = {}
    
    def adjust_allocation_based_on_risk(self):
        risk_map = self.macro_analyzer.generate_risk_map()
        risk_level = risk_map['risk_analysis']['overall_risk']
        
        allocation = risk_map['risk_analysis']['recommendations']['asset_allocation']
        
        # 根據風險等級調整倉位
        if risk_level == "high":
            self.reduce_leverage()
            self.increase_cash_position(allocation['cash'])
        elif risk_level == "low":
            self.increase_risk_assets(allocation['stocks'])
```

## 錯誤處理

### 常見錯誤與解決方案
1. **數據獲取失敗**: 檢查網絡連接與 Yahoo Finance 可訪問性
2. **API 速率限制**: 增加請求間隔，使用緩存機制
3. **指標代碼無效**: 驗證代碼格式與交易所後綴
4. **依賴缺失**: 確保 Market-Data-Fetcher 技能已安裝

### 故障安全模式
當無法獲取真實數據時，系統提供兩種應對方案：
1. **模擬數據模式**: 使用歷史數據或預設值進行分析
2. **錯誤拋出模式**: 拋出 CriticalDataError，避免基於過時數據決策

```python
try:
    analyzer = MacroGlobalLinkage(test_mode=False)
    risk_map = analyzer.generate_risk_map()
except CriticalDataError as e:
    logger.error(f"關鍵數據缺失: {e}")
    # 切換到安全模式或使用緩存數據
```

## 更新日誌

### v1.5.0 (2026-03-23)
- 擴展至6大宏觀指標 (新增 GC=F, CL=F)
- 引入歷史數據對比與動能分析
- 實現異步併發處理，提升數據獲取速度
- 完善故障安全機制與緩存持久化
- 整合主動警報框架

### v1.0.0 (初始版本)
- 基礎4指標監控 (DXY, ^TNX, ^VIX, BTC-USD)
- 風險分數計算與燈號系統
- 基本投資建議生成

## 性能指標

- **數據獲取時間**: < 1秒 (6指標併發)
- **內存使用**: < 50MB
- **緩存命中率**: > 80% (5分鐘TTL)
- **API 呼叫頻率**: 每5分鐘 (可配置)

## 注意事項

1. **數據延遲**: Yahoo Finance 數據約有15-20分鐘延遲
2. **投資風險**: 本分析僅供參考，不構成投資建議
3. **市場時間**: 非交易時段數據更新較慢
4. **國際市場**: 考慮不同市場的交易時間差異

## 貢獻與反饋

歡迎提供以下反饋：
1. 新指標建議
2. 風險模型改進
3. 性能優化方案
4. 錯誤報告與修復

---

**免責聲明**: 本技能提供的分析基於公開市場數據，僅供教育與研究目的。投資涉及風險，過往表現不代表未來結果。使用者應根據自身情況做出獨立投資決策。