#!/usr/bin/env python3
"""
V3 哨兵協議整合模組
為 US-Stock-Sentiment-Earnings 技能提供 deepseek-reasoner 調用前的 FinBERT 情緒過濾
"""

import os
import sys
import json
from datetime import datetime

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

class V3Sentry:
    """V3 哨兵協議 - 保護 R1 (deepseek-reasoner) 調用"""
    
    def __init__(self, config_path: str = None):
        """
        初始化 V3 哨兵
        
        Args:
            config_path: 配置文件路徑
        """
        self.processor = FinBERTProcessor(config_path)
        self.interception_log = []
        
        # 加載配置
        self.noise_low = self.processor.energy_saving_config["noise_threshold_low"]
        self.noise_high = self.processor.energy_saving_config["noise_threshold_high"]
        self.min_confidence = self.processor.energy_saving_config["min_confidence_for_block"]
        
        print(f"V3 哨兵協議已啟動")
        print(f"雜訊閾值: {self.noise_low} 到 {self.noise_high}")
        print(f"最小信心度: {self.min_confidence}")
    
    def guard_deepseek_reasoner(self, text: str, context: str = "美股分析") -> dict:
        """
        守護 deepseek-reasoner 調用
        
        Args:
            text: 要分析的文本內容
            context: 分析上下文
            
        Returns:
            包含決策和詳細信息的字典
        """
        print(f"🔍 V3 哨兵檢查: {context}")
        print(f"   文本長度: {len(text)} 字符")
        
        # 1. 使用 V3 進行情緒分析
        sentiment_result = self.processor.analyze_sentiment(text)
        
        sentiment_score = sentiment_result.get('sentiment_score', 0)
        confidence = sentiment_result.get('confidence', 0)
        label = sentiment_result.get('label', 'unknown')
        source = sentiment_result.get('source', 'unknown')
        
        print(f"   V3 情緒分析: 分數={sentiment_score:.3f}, 信心度={confidence:.3f}, 標籤={label}")
        
        # 2. 檢查是否需要阻止 R1 調用
        should_block, reason = self.processor.should_block_deepseek_reasoner(sentiment_result)
        
        # 3. 構建決策結果
        decision = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
            "text_length": len(text),
            "sentiment_analysis": sentiment_result,
            "should_block_r1": should_block,
            "block_reason": reason if should_block else None,
            "estimated_tokens_saved": 0
        }
        
        # 4. 如果阻止 R1 調用，記錄日誌並估算節省
        if should_block:
            # 估算節省的 tokens (假設 R1 分析會消耗更多 tokens)
            estimated_r1_tokens = len(text) * 3  # 簡單估算
            decision["estimated_tokens_saved"] = estimated_r1_tokens
            
            # 記錄攔截日誌
            self._log_interception(decision)
            
            print(f"   🚫 V3 哨兵攔截: {reason}")
            print(f"   💰 節省約 {estimated_r1_tokens} tokens")
        else:
            print(f"   ✅ 允許 R1 深度分析")
        
        return decision
    
    def _log_interception(self, decision: dict):
        """記錄攔截日誌"""
        self.interception_log.append(decision)
        
        # 更新 learning_log.md
        self._update_learning_log(decision)
        
        # 也可以記錄到獨立日誌文件
        log_entry = {
            "timestamp": decision["timestamp"],
            "action": "V3_SENTRY_INTERCEPTION",
            "details": {
                "context": decision["context"],
                "sentiment_score": decision["sentiment_analysis"].get("sentiment_score"),
                "confidence": decision["sentiment_analysis"].get("confidence"),
                "estimated_tokens_saved": decision["estimated_tokens_saved"],
                "block_reason": decision["block_reason"]
            }
        }
        
        log_file = os.path.join(skill_dir, "v3_sentry_log.json")
        try:
            # 讀取現有日誌
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 添加新日誌
            logs.append(log_entry)
            
            # 寫回文件
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"寫入日誌文件時出錯: {e}")
    
    def _update_learning_log(self, decision: dict):
        """更新 learning_log.md"""
        learning_log_path = os.path.join(skill_dir, "learning_log.md")
        
        # 如果 learning_log.md 不存在，創建它
        if not os.path.exists(learning_log_path):
            content = f"""# Learning Log - V3 哨兵協議

## 概述
此文件記錄 V3 哨兵協議的攔截記錄與節能效果。

## 攔截記錄

"""
        else:
            with open(learning_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # 添加新的攔截記錄
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sentiment_score = decision["sentiment_analysis"].get("sentiment_score", 0)
        confidence = decision["sentiment_analysis"].get("confidence", 0)
        tokens_saved = decision["estimated_tokens_saved"]
        
        new_entry = f"""
### [{timestamp}] V3 哨兵攔截記錄

**上下文**: {decision['context']}
**文本預覽**: {decision['text_preview']}
**情緒分數**: {sentiment_score:.3f}
**信心度**: {confidence:.3f}
**攔截原因**: {decision['block_reason']}
**節省 tokens**: 約 {tokens_saved}

**記錄**: [V3-Sentry] 已攔截中性新聞，節省約 {tokens_saved} Token。

---
"""
        
        # 找到攔截記錄部分並插入新記錄
        if "## 攔截記錄" in content:
            # 在攔截記錄部分後插入
            parts = content.split("## 攔截記錄")
            if len(parts) > 1:
                header = parts[0] + "## 攔截記錄"
                rest = parts[1]
                # 在現有記錄前插入新記錄
                content = header + new_entry + rest
        else:
            # 直接添加到文件末尾
            content += f"\n## 攔截記錄\n{new_entry}"
        
        # 寫回文件
        with open(learning_log_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📝 已更新 learning_log.md")
    
    def get_interception_stats(self) -> dict:
        """獲取攔截統計"""
        total_interceptions = len(self.interception_log)
        total_tokens_saved = sum(d.get("estimated_tokens_saved", 0) for d in self.interception_log)
        
        return {
            "total_interceptions": total_interceptions,
            "total_tokens_saved": total_tokens_saved,
            "avg_tokens_saved_per_interception": total_tokens_saved / total_interceptions if total_interceptions > 0 else 0,
            "interception_log": self.interception_log[-10:] if total_interceptions > 10 else self.interception_log  # 最近10條
        }
    
    def integrate_with_us_stock_sentiment(self):
        """為 US-Stock-Sentiment-Earnings 技能生成整合代碼"""
        integration_code = """
# ====================================================
# V3 哨兵協議整合代碼 - US-Stock-Sentiment-Earnings
# ====================================================

# 在 US-Stock-Sentiment-Earnings 技能中，在調用 deepseek-reasoner 之前添加以下代碼：

import sys
import os

# 添加 FinBERT 技能目錄到路徑
finbert_skill_path = "/home/node/.openclaw/workspace/skills/finbert-sentiment"
if finbert_skill_path not in sys.path:
    sys.path.append(finbert_skill_path)

from scripts.sentry_integration import V3Sentry

def analyze_with_sentry_guard(text, context="美股情緒分析"):
    \"\"\"
    使用 V3 哨兵保護的深度分析
    
    Args:
        text: 要分析的文本
        context: 分析上下文
        
    Returns:
        分析結果或攔截信息
    \"\"\"
    # 初始化哨兵
    sentry = V3Sentry()
    
    # 檢查是否允許 R1 調用
    decision = sentry.guard_deepseek_reasoner(text, context)
    
    if decision["should_block_r1"]:
        # 被攔截 - 返回簡要分析
        return {
            "status": "intercepted",
            "message": "V3 哨兵攔截: 內容為中性新聞，無需深度分析",
            "sentiment_score": decision["sentiment_analysis"]["sentiment_score"],
            "confidence": decision["sentiment_analysis"]["confidence"],
            "estimated_tokens_saved": decision["estimated_tokens_saved"],
            "recommendation": "此新聞情緒中性，建議關注其他更具分析價值的內容"
        }
    else:
        # 允許深度分析 - 調用 deepseek-reasoner
        # 這裡替換為實際的 deepseek-reasoner 調用代碼
        try:
            # deepseek-reasoner 分析代碼
            r1_result = call_deepseek_reasoner_analysis(text, context)
            
            return {
                "status": "analyzed",
                "analysis": r1_result,
                "sentiment_score": decision["sentiment_analysis"]["sentiment_score"],
                "v3_guard_applied": True
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_sentiment": decision["sentiment_analysis"]
            }

# 在現有分析函數中調用
def analyze_stock_sentiment(stock_symbol, news_text, earnings_data):
    \"\"\"
    分析股票情緒 (已整合 V3 哨兵)
    \"\"\"
    # 構建分析文本
    analysis_text = f\"股票: {stock_symbol}\\n相關新聞: {news_text}\\n財報數據: {earnings_data}\"
    
    # 使用哨兵保護的分析
    result = analyze_with_sentry_guard(analysis_text, f\"{stock_symbol} 情緒分析\")
    
    return result

# ====================================================
# 使用示例
# ====================================================

if __name__ == "__main__":
    # 示例新聞
    test_news = \"蘋果發布新iPhone，股價微幅上漲\"
    test_context = \"AAPL 產品發布新聞分析\"
    
    result = analyze_with_sentry_guard(test_news, test_context)
    print(f\"分析結果: {result}\")
"""
        
        # 保存整合代碼到文件
        integration_file = os.path.join(skill_dir, "us_stock_sentiment_integration.py")
        with open(integration_file, 'w', encoding='utf-8') as f:
            f.write(integration_code)
        
        print(f"✅ 已生成整合代碼: {integration_file}")
        return integration_code

def main():
    """主函數"""
    print("V3 哨兵協議整合模組")
    print("=" * 60)
    
    # 創建哨兵實例
    sentry = V3Sentry()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 測試攔截
            test_text = "美股開盤持平，投資者等待通膨數據"
            result = sentry.guard_deepseek_reasoner(test_text, "美股新聞測試")
            print(f"\n測試結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        elif sys.argv[1] == "stats":
            # 顯示統計
            stats = sentry.get_interception_stats()
            print(f"\n攔截統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        elif sys.argv[1] == "integrate":
            # 生成整合代碼
            sentry.integrate_with_us_stock_sentiment()
        elif sys.argv[1] == "demo":
            # 演示多個測試案例
            test_cases = [
                ("市場交易平淡，沒有重大消息", "中性新聞測試"),
                ("蘋果發布強勁財報，營收增長超預期", "正面新聞測試"),
                ("特斯拉面臨供應鏈問題，股價下跌", "負面新聞測試"),
                ("微軟季度營收符合分析師預期", "符合預期測試")
            ]
            
            for text, context in test_cases:
                print(f"\n測試: {context}")
                print(f"文本: {text}")
                result = sentry.guard_deepseek_reasoner(text, context)
                print(f"結果: {'攔截' if result['should_block_r1'] else '允許'}")
    else:
        print("命令:")
        print("  test     - 測試哨兵攔截")
        print("  stats    - 顯示攔截統計")
        print("  integrate - 生成 US-Stock-Sentiment-Earnings 整合代碼")
        print("  demo     - 運行演示測試")

if __name__ == "__main__":
    main()