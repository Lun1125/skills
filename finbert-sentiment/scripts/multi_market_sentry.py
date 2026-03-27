#!/usr/bin/env python3
"""
多市場 V3 哨兵協議
為美股、台股、加密貨幣三大市場提供 deepseek-reasoner 調用保護
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

class MultiMarketSentry:
    """多市場 V3 哨兵 - 保護三大市場的 R1 調用"""
    
    def __init__(self, config_path: str = None):
        """
        初始化多市場哨兵
        
        Args:
            config_path: 配置文件路徑
        """
        self.processor = FinBERTProcessor(config_path)
        self.interception_log = []
        
        # 加載市場特定配置
        self.market_configs = self._load_market_configs()
        
        print("多市場 V3 哨兵協議已啟動")
        print("=" * 60)
        for market, config in self.market_configs.items():
            print(f"{market}: 閾值 ±{config['noise_threshold_high']}, 信心度 {config['min_confidence_for_block']}")
        print("=" * 60)
    
    def _load_market_configs(self) -> Dict[str, Dict]:
        """加載市場特定配置"""
        energy_saving = self.processor.config.get("energy_saving", {})
        
        # 市場配置映射
        market_configs = {
            "us_stock": energy_saving.get("us_stock", energy_saving.get("default", {})),
            "tw_stock": energy_saving.get("tw_stock", energy_saving.get("default", {})),
            "crypto": energy_saving.get("crypto", energy_saving.get("default", {}))
        }
        
        # 確保每個市場都有必要的配置
        default_config = energy_saving.get("default", {
            "noise_threshold_low": -0.25,
            "noise_threshold_high": 0.25,
            "block_deepseek_reasoner": True,
            "min_confidence_for_block": 0.65
        })
        
        for market in market_configs:
            if not market_configs[market]:
                market_configs[market] = default_config.copy()
        
        return market_configs
    
    def guard_market_analysis(self, text: str, market: str = "us_stock", context: str = "") -> dict:
        """
        守護指定市場的分析調用
        
        Args:
            text: 要分析的文本內容
            market: 市場類型 (us_stock, tw_stock, crypto)
            context: 分析上下文
            
        Returns:
            包含決策和詳細信息的字典
        """
        # 驗證市場類型
        valid_markets = ["us_stock", "tw_stock", "crypto"]
        if market not in valid_markets:
            print(f"⚠️ 警告: 未知市場 '{market}'，使用默認配置")
            market = "us_stock"
        
        market_config = self.market_configs[market]
        market_display = {
            "us_stock": "🇺🇸 美股",
            "tw_stock": "🇹🇼 台股", 
            "crypto": "₿ 加密貨幣"
        }.get(market, market)
        
        print(f"🔍 {market_display} 哨兵檢查: {context}")
        print(f"   市場配置: {market_config.get('description', '')}")
        print(f"   雜訊閾值: {market_config['noise_threshold_low']} 到 {market_config['noise_threshold_high']}")
        print(f"   文本長度: {len(text)} 字符")
        
        # 1. 使用 V3 進行情緒分析
        sentiment_result = self.processor.analyze_sentiment(text)
        
        sentiment_score = sentiment_result.get('sentiment_score', 0)
        confidence = sentiment_result.get('confidence', 0)
        label = sentiment_result.get('label', 'unknown')
        source = sentiment_result.get('source', 'unknown')
        
        print(f"   V3 情緒分析: 分數={sentiment_score:.3f}, 信心度={confidence:.3f}, 標籤={label}")
        
        # 2. 使用市場特定配置檢查是否需要阻止 R1 調用
        should_block, reason = self._check_with_market_config(
            sentiment_result, market_config, market
        )
        
        # 3. 構建決策結果
        decision = {
            "timestamp": datetime.now().isoformat(),
            "market": market,
            "market_display": market_display,
            "context": context,
            "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
            "text_length": len(text),
            "market_config": market_config,
            "sentiment_analysis": sentiment_result,
            "should_block_r1": should_block,
            "block_reason": reason if should_block else None,
            "estimated_tokens_saved": 0
        }
        
        # 4. 如果阻止 R1 調用，記錄日誌並估算節省
        if should_block:
            # 估算節省的 tokens (市場不同，估算也不同)
            estimated_r1_tokens = self._estimate_tokens_saved(text, market)
            decision["estimated_tokens_saved"] = estimated_r1_tokens
            
            # 記錄攔截日誌
            self._log_interception(decision)
            
            print(f"   🚫 {market_display} 哨兵攔截: {reason}")
            print(f"   💰 節省約 {estimated_r1_tokens} tokens")
        else:
            print(f"   ✅ 允許 R1 深度分析")
        
        return decision
    
    def _check_with_market_config(self, sentiment_result: Dict, market_config: Dict, market: str) -> tuple:
        """
        使用市場特定配置檢查是否需要阻止 R1 調用
        
        Returns:
            (should_block, reason)
        """
        if not market_config.get("block_deepseek_reasoner", True):
            return False, "此市場的節能過濾已禁用"
        
        sentiment_score = sentiment_result.get("sentiment_score", 0)
        confidence = sentiment_result.get("confidence", 0)
        
        noise_low = market_config["noise_threshold_low"]
        noise_high = market_config["noise_threshold_high"]
        min_confidence = market_config["min_confidence_for_block"]
        
        # 檢查是否在雜訊範圍內
        is_in_noise_range = (noise_low <= sentiment_score <= noise_high)
        
        # 檢查信心度是否足夠
        has_sufficient_confidence = (confidence >= min_confidence)
        
        if is_in_noise_range and has_sufficient_confidence:
            # 根據市場生成不同的原因訊息
            if market == "crypto":
                reason = f"加密貨幣情緒分數 {sentiment_score:.3f} 在敏感範圍內 (±{noise_high})"
            else:
                reason = f"情緒分數 {sentiment_score:.3f} 在雜訊範圍內 ({noise_low} 到 {noise_high})"
            return True, reason
        
        if is_in_noise_range and not has_sufficient_confidence:
            return False, f"情緒分數在雜訊範圍內，但信心度 {confidence:.3f} 低於要求 {min_confidence}"
        
        return False, "情緒分數超出雜訊範圍"
    
    def _estimate_tokens_saved(self, text: str, market: str) -> int:
        """估算節省的 tokens"""
        base_tokens = len(text) * 2  # 基礎估算
        
        # 根據市場調整
        market_multipliers = {
            "us_stock": 3,   # 美股分析通常更複雜
            "tw_stock": 2.5, # 台股分析中等複雜度
            "crypto": 4      # 加密貨幣分析通常更複雜（技術分析多）
        }
        
        multiplier = market_multipliers.get(market, 3)
        return int(base_tokens * multiplier)
    
    def _log_interception(self, decision: dict):
        """記錄攔截日誌"""
        self.interception_log.append(decision)
        
        # 更新 learning_log.md
        self._update_learning_log(decision)
        
        # 記錄到獨立日誌文件
        log_entry = {
            "timestamp": decision["timestamp"],
            "market": decision["market"],
            "action": "MULTI_MARKET_SENTRY_INTERCEPTION",
            "details": {
                "market_display": decision["market_display"],
                "context": decision["context"],
                "sentiment_score": decision["sentiment_analysis"].get("sentiment_score"),
                "confidence": decision["sentiment_analysis"].get("confidence"),
                "estimated_tokens_saved": decision["estimated_tokens_saved"],
                "block_reason": decision["block_reason"]
            }
        }
        
        log_file = os.path.join(skill_dir, "multi_market_sentry_log.json")
        try:
            # 讀取現有日誌
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 添加新日誌
            logs.append(log_entry)
            
            # 寫回文件（只保留最近100條）
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"寫入日誌文件時出錯: {e}")
    
    def _update_learning_log(self, decision: dict):
        """更新 learning_log.md"""
        learning_log_path = os.path.join(skill_dir, "learning_log.md")
        
        # 如果 learning_log.md 不存在，創建它
        if not os.path.exists(learning_log_path):
            content = f"""# Learning Log - 多市場 V3 哨兵協議

## 概述
此文件記錄多市場 V3 哨兵協議的攔截記錄與節能效果。

## 攔截記錄

"""
        else:
            with open(learning_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # 添加新的攔截記錄
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        market_display = decision["market_display"]
        sentiment_score = decision["sentiment_analysis"].get("sentiment_score", 0)
        confidence = decision["sentiment_analysis"].get("confidence", 0)
        tokens_saved = decision["estimated_tokens_saved"]
        
        new_entry = f"""
### [{timestamp}] {market_display} 哨兵攔截記錄

**市場**: {market_display}
**上下文**: {decision['context']}
**文本預覽**: {decision['text_preview']}
**情緒分數**: {sentiment_score:.3f}
**信心度**: {confidence:.3f}
**攔截原因**: {decision['block_reason']}
**節省 tokens**: 約 {tokens_saved}

**記錄**: [V3-Sentry] {market_display} 已攔截中性新聞，節省約 {tokens_saved} Token。

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
    
    def test_market_scenarios(self):
        """測試三大市場的典型場景"""
        print("🧪 三大市場哨兵協議測試")
        print("=" * 60)
        
        test_cases = [
            {
                "market": "us_stock",
                "text": "蘋果發布強勁財報，營收增長超預期，股價大漲5%",
                "context": "美股正面新聞測試",
                "expected": "允許"  # 強烈情緒，應允許
            },
            {
                "market": "us_stock", 
                "text": "市場交易平淡，投資者觀望聯準會會議結果",
                "context": "美股中性新聞測試",
                "expected": "攔截"  # 中性，應攔截
            },
            {
                "market": "tw_stock",
                "text": "台積電3奈米製程良率提升，營收展望樂觀",
                "context": "台股正面新聞測試",
                "expected": "允許"  # 正面情緒
            },
            {
                "market": "tw_stock",
                "text": "台股加權指數在17500點附近震盪，成交量一般",
                "context": "台股中性新聞測試", 
                "expected": "攔截"  # 中性
            },
            {
                "market": "crypto",
                "text": "比特幣突破90000美元，創歷史新高",
                "context": "加密貨幣正面新聞測試",
                "expected": "允許"  # 強烈正面
            },
            {
                "market": "crypto",
                "text": "比特幣在85000-86000美元區間整理，市場觀望",
                "context": "加密貨幣中性新聞測試",
                "expected": "攔截"  # 中性（加密貨幣閾值更敏感）
            }
        ]
        
        results = []
        for test in test_cases:
            print(f"\n測試: {test['context']}")
            print(f"市場: {test['market']}")
            print(f"文本: {test['text']}")
            
            result = self.guard_market_analysis(
                test["text"], 
                test["market"], 
                test["context"]
            )
            
            actual = "攔截" if result["should_block_r1"] else "允許"
            passed = (actual == test["expected"])
            
            results.append({
                "test": test["context"],
                "expected": test["expected"],
                "actual": actual,
                "passed": passed,
                "sentiment": result["sentiment_analysis"].get("sentiment_score", 0)
            })
            
            status = "✅ 通過" if passed else "❌ 失敗"
            print(f"結果: {status} (預期: {test['expected']}, 實際: {actual})")
        
        # 顯示統計
        print("\n" + "=" * 60)
        print("測試統計:")
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        
        print(f"總測試數: {total}")
        print(f"通過: {passed} ({passed/total*100:.1f}%)")
        print(f"失敗: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\n失敗的測試:")
            for r in results:
                if not r["passed"]:
                    print(f"  - {r['test']}: 預期 {r['expected']}, 實際 {r['actual']}, 情緒分數 {r['sentiment']:.3f}")
        
        return results

def main():
    """主函數"""
    print("多市場 V3 哨兵協議")
    print("=" * 60)
    
    # 創建哨兵實例
    sentry = MultiMarketSentry()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 運行三大市場測試
            sentry.test_market_scenarios()
        elif sys.argv[1] == "demo":
            # 運行用戶指定的演示案例
            print("\n🧪 用戶指定案例演示")
            print("-" * 60)
            
            # 案例1: 台積電營收亮眼
            print("\n1. 台股案例: '台積電營收亮眼'")
            tsmo_text = "台積電公布3月營收，月增15%，年增25%，表現亮眼"
            result1 = sentry.guard_market_analysis(
                tsmo_text, 
                "tw_stock", 
                "台積電營收新聞分析"
            )
            print(f"   決策: {'攔截' if result1['should_block_r1'] else '允許深度分析'}")
            
            # 案例2: BTC 鏈上大額轉移
            print("\n2. 加密貨幣案例: 'BTC 鏈上大額轉移'")
            btc_text = "比特幣鏈上出現大額轉移，10,000 BTC從未知錢包轉至交易所，可能預示大戶動向"
            result2 = sentry.guard_market_analysis(
                btc_text,
                "crypto",
                "BTC鏈上轉移分析"
            )
            print(f"   決策: {'攔截' if result2['should_block_r1'] else '允許深度分析'}")
            
            print("\n" + "=" * 60)
            print("演示完成!")
        elif sys.argv[1] == "stats":
            # 顯示統計
            print(f"總攔截記錄: {len(sentry.interception_log)}")
            if sentry.interception_log:
                total_saved = sum(d.get("estimated_tokens_saved", 0) for d in sentry.interception_log)
                print(f"總節省 tokens: {total_saved:,}")
                
                # 按市場分類
                market_stats = {}
                for log in sentry.interception_log:
                    market = log.get("market", "unknown")
                    if market not in market_stats:
                        market_stats[market] = {"count": 0, "tokens_saved": 0}
                    market_stats[market]["count"] += 1
                    market_stats[market]["tokens_saved"] += log.get("estimated_tokens_saved", 0)
                
                print("\n按市場統計:")
                for market, stats in market_stats.items():
                    print(f"  {market}: {stats['count']}次攔截, 節省 {stats['tokens_saved']:,} tokens")
    else:
        print("命令:")
        print("  test  - 運行三大市場測試")
        print("  demo  - 運行用戶案例演示")
        print("  stats - 顯示攔截統計")

if __name__ == "__main__":
    main()