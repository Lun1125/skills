#!/usr/bin/env python3
"""
V3 橋接方案測試腳本
測試輕量化橋接方案：使用 deepseek-chat (V3) 進行情緒分析
並計算實際節省的 R1 (deepseek-reasoner) 調用比例
"""

import os
import sys
import json
from datetime import datetime

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

def test_v3_bridge_with_7_news():
    """使用 V3 橋接方案測試 7 條新聞"""
    print("V3 輕量化橋接方案測試")
    print("=" * 70)
    print("策略: 用便宜的 V3 看大門，擋掉雜訊，守護昂貴的 R1 Token")
    print("=" * 70)
    
    # 創建處理器
    processor = FinBERTProcessor()
    
    # 7 條真實美股新聞標題
    news_items = [
        {
            "id": "news_001",
            "text": "美股開盤持平，投資者等待通膨數據",
            "expected_type": "neutral"  # 預期中性，應觸發節能過濾
        },
        {
            "id": "news_002",
            "text": "蘋果發布新iPhone，股價微幅上漲",
            "expected_type": "slightly_positive"  # 輕微正面
        },
        {
            "id": "news_003",
            "text": "特斯拉中國工廠恢復生產，股價變化不大",
            "expected_type": "neutral"  # 中性
        },
        {
            "id": "news_004",
            "text": "微軟雲業務穩定增長，符合市場預期",
            "expected_type": "positive"  # 正面
        },
        {
            "id": "news_005",
            "text": "輝達AI晶片需求強勁，股價大漲8%",
            "expected_type": "strong_positive"  # 強烈正面
        },
        {
            "id": "news_006",
            "text": "亞馬遜季度虧損，股價重挫10%",
            "expected_type": "strong_negative"  # 強烈負面
        },
        {
            "id": "news_007",
            "text": "Netflix用戶增長停滯，分析師下調評級",
            "expected_type": "negative"  # 負面
        }
    ]
    
    print(f"\n測試 {len(news_items)} 條美股新聞標題:")
    print("-" * 70)
    
    # 統計數據
    stats = {
        "total_news": len(news_items),
        "v3_analyses": 0,
        "blocked_r1": 0,
        "allowed_r1": 0,
        "neutral_news": 0,
        "total_v3_tokens": 0,
        "estimated_r1_tokens_saved": 0
    }
    
    # 成本假設 (Token 成本比例)
    v3_token_cost = processor.energy_saving_config.get("cost_comparison", {}).get("v3_token_cost", 1)
    r1_token_cost = processor.energy_saving_config.get("cost_comparison", {}).get("r1_token_cost", 10)
    savings_per_block = processor.energy_saving_config.get("cost_comparison", {}).get("estimated_savings_per_block", 9)
    
    print(f"成本假設: V3 Token 成本 = {v3_token_cost}, R1 Token 成本 = {r1_token_cost}")
    print(f"每次阻止 R1 調用可節省: {savings_per_block} Token 成本單位")
    print("-" * 70)
    
    for i, news in enumerate(news_items, 1):
        print(f"\n{i}. {news['text']}")
        print(f"   預期類型: {news['expected_type']}")
        print("   " + "-" * 40)
        
        # 使用 V3 橋接方案分析情緒
        print("   🔍 V3 情緒分析中...")
        result = processor.analyze_sentiment(news['text'])
        
        stats["v3_analyses"] += 1
        
        # 估算 V3 Token 消耗 (簡單估算：文本長度 + 提示長度)
        estimated_v3_tokens = len(news['text']) + 200  # 提示約 200 tokens
        stats["total_v3_tokens"] += estimated_v3_tokens
        
        sentiment_score = result.get('sentiment_score', 0)
        confidence = result.get('confidence', 0)
        label = result.get('label', 'unknown')
        source = result.get('source', 'unknown')
        
        print(f"   來源: {source}")
        print(f"   情緒分數: {sentiment_score:.3f}")
        print(f"   信心度: {confidence:.3f}")
        print(f"   標籤: {label}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        
        if is_noise:
            stats["neutral_news"] += 1
            print(f"   是否雜訊: ✅ 是 (中性新聞)")
        else:
            print(f"   是否雜訊: ❌ 否")
        
        # 檢查是否需要阻止 deepseek-reasoner (R1)
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        
        if should_block:
            stats["blocked_r1"] += 1
            stats["estimated_r1_tokens_saved"] += savings_per_block
            print(f"   🚫 阻止 R1 調用: {reason}")
            print(f"   💰 節省 {savings_per_block} Token 成本單位")
        else:
            stats["allowed_r1"] += 1
            print(f"   ✅ 允許 R1 深度分析")
        
        # 估算 R1 Token 消耗 (如果允許分析)
        if not should_block:
            estimated_r1_tokens = len(news['text']) * 3  # R1 分析通常消耗更多 tokens
            # 這裡只是估算，實際會更多
    
    print("\n" + "=" * 70)
    print("節能過濾統計報告")
    print("=" * 70)
    
    # 計算比例
    blocked_percentage = (stats["blocked_r1"] / stats["total_news"]) * 100
    allowed_percentage = (stats["allowed_r1"] / stats["total_news"]) * 100
    neutral_percentage = (stats["neutral_news"] / stats["total_news"]) * 100
    
    print(f"📊 基本統計:")
    print(f"   總新聞數: {stats['total_news']}")
    print(f"   V3 分析次數: {stats['v3_analyses']}")
    print(f"   中性新聞: {stats['neutral_news']} ({neutral_percentage:.1f}%)")
    print(f"   阻止 R1 調用: {stats['blocked_r1']} ({blocked_percentage:.1f}%)")
    print(f"   允許 R1 調用: {stats['allowed_r1']} ({allowed_percentage:.1f}%)")
    
    print(f"\n💰 成本效益分析:")
    print(f"   總 V3 Token 消耗: ~{stats['total_v3_tokens']}")
    print(f"   估計 R1 Token 節省: {stats['estimated_r1_tokens_saved']} 成本單位")
    
    # 計算淨節省
    v3_cost = stats['total_v3_tokens'] * v3_token_cost
    r1_savings = stats['estimated_r1_tokens_saved'] * r1_token_cost
    
    print(f"   V3 分析成本: {v3_cost} 單位")
    print(f"   R1 節省價值: {r1_savings} 單位")
    
    if r1_savings > v3_cost:
        net_savings = r1_savings - v3_cost
        print(f"   ✅ 淨節省: {net_savings} 單位 (投資回報率: {(net_savings/v3_cost)*100:.1f}%)")
    else:
        net_cost = v3_cost - r1_savings
        print(f"   ⚠️ 淨成本: {net_cost} 單位")
    
    print(f"\n🎯 節能效果:")
    print(f"   實際節省的 R1 調用比例: {blocked_percentage:.1f}%")
    
    if blocked_percentage > 0:
        print(f"   ✅ V3 看大門策略成功!")
        print(f"   每 100 條新聞可節省 {blocked_percentage:.0f} 次 R1 調用")
        
        # 估算實際 Token 節省
        avg_r1_tokens_per_analysis = 500  # 假設每次 R1 分析平均 500 tokens
        tokens_saved = stats['blocked_r1'] * avg_r1_tokens_per_analysis
        
        print(f"\n💡 實際 Token 節省估算:")
        print(f"   每次 R1 分析約 {avg_r1_tokens_per_analysis} tokens")
        print(f"   總節省 tokens: {tokens_saved:,}")
        print(f"   相當於節省了 {tokens_saved/1000:.1f}K tokens")
    else:
        print(f"   ⚠️ 本次測試未觸發節能過濾")
        print(f"   可能原因:")
        print(f"   1. 新聞情緒較強烈，不在雜訊範圍內")
        print(f"   2. V3 分析信心度不足")
        print(f"   3. 需要調整雜訊閾值")
    
    print("\n" + "=" * 70)
    print("V3 橋接方案總結")
    print("=" * 70)
    
    print("✅ 優勢:")
    print("   1. 無需外部 API，完全自包含")
    print("   2. 使用便宜的 V3 模型過濾雜訊")
    print("   3. 保護昂貴的 R1 Token 消耗")
    print("   4. 可配置的提示模板和閾值")
    
    print("\n📋 配置建議:")
    print(f"   當前雜訊閾值: {processor.energy_saving_config['noise_threshold_low']} 到 {processor.energy_saving_config['noise_threshold_high']}")
    print(f"   最小信心度: {processor.energy_saving_config['min_confidence_for_block']}")
    print("   可根據實際需求調整這些參數以優化節能效果")
    
    print("\n" + "=" * 70)

def main():
    """主測試函數"""
    print("V3 輕量化橋接方案 - 7 條新聞測試")
    print("測試時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    test_v3_bridge_with_7_news()
    
    print("\n測試完成!")
    print("=" * 70)

if __name__ == "__main__":
    main()