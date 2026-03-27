#!/usr/bin/env python3
"""
FinBERT 節能過濾專項測試
專門測試情緒分數在 -0.2 到 0.2 之間時是否正確觸發節能過濾
"""

import os
import sys
import json

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

def test_noise_detection():
    """測試雜訊檢測邏輯"""
    print("FinBERT 節能過濾專項測試")
    print("=" * 60)
    
    # 創建處理器
    processor = FinBERTProcessor()
    
    # 測試案例：情緒分數在 -0.2 到 0.2 之間的不同情況
    test_cases = [
        {
            "text": "市場交易平淡，沒有明顯方向",
            "expected_noise": True,
            "description": "典型中性新聞"
        },
        {
            "text": "蘋果股價在150美元附近震盪",
            "expected_noise": True,
            "description": "股價震盪，中性"
        },
        {
            "text": "微軟季度營收符合分析師預期",
            "expected_noise": True,
            "description": "符合預期，中性"
        },
        {
            "text": "特斯拉小幅上漲0.5%，成交量一般",
            "expected_noise": True,
            "description": "小幅變動，接近中性"
        },
        {
            "text": "聯準會維持利率不變，符合市場預期",
            "expected_noise": True,
            "description": "政策不變，中性"
        }
    ]
    
    print("測試雜訊檢測邏輯:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_case['description']}")
        print(f"新聞: {test_case['text']}")
        
        # 分析情緒
        result = processor.analyze_sentiment(test_case['text'])
        
        sentiment_score = result.get('sentiment_score', 0)
        confidence = result.get('confidence', 0)
        
        print(f"  情緒分數: {sentiment_score}")
        print(f"  信心度: {confidence}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        expected = test_case['expected_noise']
        
        print(f"  是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        print(f"  預期結果: {'✅ 是' if expected else '❌ 否'}")
        
        if is_noise == expected:
            print(f"  🎯 測試通過!")
        else:
            print(f"  ❌ 測試失敗!")
            
            # 顯示詳細原因
            noise_low = processor.energy_saving_config["noise_threshold_low"]
            noise_high = processor.energy_saving_config["noise_threshold_high"]
            min_confidence = processor.energy_saving_config["min_confidence_for_block"]
            
            print(f"    雜訊範圍: {noise_low} 到 {noise_high}")
            print(f"    最小信心度: {min_confidence}")
            print(f"    情緒分數在範圍內: {noise_low <= sentiment_score <= noise_high}")
            print(f"    信心度足夠: {confidence >= min_confidence}")
    
    print("\n" + "=" * 60)
    
def test_energy_saving_decision():
    """測試節能決策邏輯"""
    print("\n測試節能決策邏輯 (是否阻止 deepseek-reasoner):")
    print("-" * 60)
    
    processor = FinBERTProcessor()
    
    # 顯示當前配置
    print("當前節能配置:")
    config = processor.energy_saving_config
    print(f"  雜訊閾值: {config['noise_threshold_low']} 到 {config['noise_threshold_high']}")
    print(f"  阻止 deepseek-reasoner: {config['block_deepseek_reasoner']}")
    print(f"  最小信心度: {config['min_confidence_for_block']}")
    
    # 測試不同情緒分數的決策
    test_scores = [
        (-0.25, "輕微負面，超出雜訊範圍"),
        (-0.15, "輕微負面，在雜訊範圍內"),
        (-0.05, "接近中性，在雜訊範圍內"),
        (0.0, "完全中性，在雜訊範圍內"),
        (0.05, "輕微正面，在雜訊範圍內"),
        (0.15, "輕微正面，在雜訊範圍內"),
        (0.25, "正面，超出雜訊範圍"),
        (0.8, "強烈正面，超出雜訊範圍"),
        (-0.8, "強烈負面，超出雜訊範圍")
    ]
    
    print("\n不同情緒分數的節能決策:")
    print("-" * 60)
    
    for score, description in test_scores:
        # 創建模擬結果
        mock_result = {
            "sentiment_score": score,
            "confidence": 0.75,  # 足夠的信心度
            "label": "neutral" if -0.2 <= score <= 0.2 else ("positive" if score > 0 else "negative")
        }
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(mock_result)
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(mock_result)
        
        print(f"\n情緒分數: {score:.2f} ({description})")
        print(f"  是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        print(f"  阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
        
        if should_block:
            print(f"  🚫 原因: {reason}")
    
    print("\n" + "=" * 60)

def test_with_different_confidence():
    """測試不同信心度下的節能決策"""
    print("\n測試不同信心度下的節能決策:")
    print("-" * 60)
    
    processor = FinBERTProcessor()
    
    # 測試案例：中性情緒分數，不同信心度
    neutral_score = 0.1  # 在雜訊範圍內
    
    confidence_levels = [
        (0.3, "低信心度"),
        (0.5, "中等信心度"),
        (0.7, "高信心度 (閾值)"),
        (0.8, "很高信心度"),
        (0.9, "極高信心度")
    ]
    
    for confidence, description in confidence_levels:
        # 創建模擬結果
        mock_result = {
            "sentiment_score": neutral_score,
            "confidence": confidence,
            "label": "neutral"
        }
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(mock_result)
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(mock_result)
        
        min_confidence = processor.energy_saving_config["min_confidence_for_block"]
        
        print(f"\n情緒分數: {neutral_score:.2f}, 信心度: {confidence:.2f} ({description})")
        print(f"  最小信心度要求: {min_confidence}")
        print(f"  信心度足夠: {'✅ 是' if confidence >= min_confidence else '❌ 否'}")
        print(f"  是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        print(f"  阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
        
        if should_block:
            print(f"  🚫 原因: {reason}")
    
    print("\n" + "=" * 60)

def test_real_scenario():
    """測試真實場景"""
    print("\n真實場景測試: 隨機美股新聞標題")
    print("-" * 60)
    
    processor = FinBERTProcessor()
    
    # 真實新聞標題
    real_news = [
        "美股開盤持平，投資者等待通膨數據",
        "蘋果發布新iPhone，股價微幅上漲",
        "特斯拉中國工廠恢復生產，股價變化不大",
        "微軟雲業務穩定增長，符合市場預期",
        "輝達AI晶片需求強勁，股價大漲8%",
        "亞馬遜季度虧損，股價重挫10%",
        "Netflix用戶增長停滯，分析師下調評級"
    ]
    
    print("分析結果:")
    print("-" * 60)
    
    blocked_count = 0
    total_count = len(real_news)
    
    for news in real_news:
        print(f"\n新聞: {news}")
        
        # 分析情緒
        result = processor.analyze_sentiment(news)
        
        sentiment_score = result.get('sentiment_score', 0)
        confidence = result.get('confidence', 0)
        label = result.get('label', 'unknown')
        
        print(f"  情緒分數: {sentiment_score:.3f}")
        print(f"  信心度: {confidence:.3f}")
        print(f"  標籤: {label}")
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        
        if should_block:
            blocked_count += 1
            print(f"  🚫 阻止 deepseek-reasoner: {reason}")
        else:
            print(f"  ✅ 允許深度分析")
    
    print("\n" + "=" * 60)
    print("節能過濾總結:")
    print(f"  總新聞數: {total_count}")
    print(f"  阻止分析: {blocked_count}")
    print(f"  允許分析: {total_count - blocked_count}")
    print(f"  節能比例: {blocked_count/total_count*100:.1f}%")
    
    if blocked_count > 0:
        print(f"\n🎯 節能過濾器運作正常!")
        print(f"   可節省 {blocked_count/total_count*100:.1f}% 的 deepseek-reasoner 調用")
    else:
        print(f"\n⚠️ 注意: 本次測試未觸發節能過濾")
        print("   可能原因:")
        print("   1. 新聞情緒分數不在 -0.2 到 0.2 範圍內")
        print("   2. 分析信心度低於 0.7")
        print("   3. 模擬分析邏輯需要調整")
    
    print("=" * 60)

def main():
    """主測試函數"""
    # 運行所有測試
    test_noise_detection()
    test_energy_saving_decision()
    test_with_different_confidence()
    test_real_scenario()
    
    print("\n測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()