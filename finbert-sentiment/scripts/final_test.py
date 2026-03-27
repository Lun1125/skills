#!/usr/bin/env python3
"""
FinBERT 情緒分析與節能過濾最終測試
驗證當分析結果為『中性 (Neutral)』時，系統是否如期顯示節能過濾訊息
"""

import os
import sys

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

def main():
    print("FinBERT 情緒分析與節能過濾最終測試")
    print("=" * 60)
    
    # 檢查環境變數
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
    if not api_token:
        print("❌ 錯誤: HUGGINGFACE_API_TOKEN 環境變數未設置")
        return
    
    print(f"✅ API Token 已設置 (長度: {len(api_token)})")
    
    # 創建處理器
    processor = FinBERTProcessor()
    
    # 測試案例：典型中性美股新聞
    test_news = "美股開盤持平，投資者等待通膨數據公布"
    
    print(f"\n測試新聞標題: {test_news}")
    print("-" * 60)
    
    # 分析情緒
    print("進行 FinBERT 情緒分析...")
    result = processor.analyze_sentiment(test_news)
    
    print(f"\n分析結果:")
    print(f"  情緒分數: {result.get('sentiment_score', 'N/A')}")
    print(f"  信心度: {result.get('confidence', 'N/A')}")
    print(f"  標籤: {result.get('label', 'N/A')}")
    print(f"  是否模擬分析: {result.get('is_simulated', 'N/A')}")
    
    # 檢查是否為雜訊
    is_noise = processor.is_noise(result)
    print(f"\n雜訊檢測:")
    print(f"  是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
    
    # 檢查是否需要阻止 deepseek-reasoner
    should_block, reason = processor.should_block_deepseek_reasoner(result)
    
    print(f"\n節能過濾決策:")
    print(f"  阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
    
    if should_block:
        print(f"\n🚫 {reason}")
        print("\n✅ 節能過濾器運作正常!")
        print("   系統正確識別中性新聞為雜訊，並阻止 deepseek-reasoner 調用")
    else:
        print(f"\n✅ 允許深度分析")
        print("\n⚠️ 注意: 未觸發節能過濾")
        
        # 顯示詳細原因
        sentiment_score = result.get('sentiment_score', 0)
        confidence = result.get('confidence', 0)
        
        noise_low = processor.energy_saving_config["noise_threshold_low"]
        noise_high = processor.energy_saving_config["noise_threshold_high"]
        min_confidence = processor.energy_saving_config["min_confidence_for_block"]
        
        print(f"\n詳細分析:")
        print(f"  情緒分數: {sentiment_score}")
        print(f"  雜訊範圍: {noise_low} 到 {noise_high}")
        print(f"  在雜訊範圍內: {noise_low <= sentiment_score <= noise_high}")
        print(f"  信心度: {confidence}")
        print(f"  最小信心度要求: {min_confidence}")
        print(f"  信心度足夠: {confidence >= min_confidence}")
    
    print("\n" + "=" * 60)
    
    # 額外測試：強烈情緒新聞（不應該觸發節能過濾）
    print("\n對照測試: 強烈情緒新聞")
    print("-" * 60)
    
    strong_news = "蘋果發布強勁財報，營收增長超預期，股價大漲5%"
    print(f"測試新聞: {strong_news}")
    
    strong_result = processor.analyze_sentiment(strong_news)
    strong_should_block, strong_reason = processor.should_block_deepseek_reasoner(strong_result)
    
    print(f"情緒分數: {strong_result.get('sentiment_score', 'N/A')}")
    print(f"阻止 deepseek-reasoner: {'✅ 是' if strong_should_block else '❌ 否'}")
    
    if not strong_should_block:
        print("✅ 對照測試通過: 強烈情緒新聞未觸發節能過濾")
    else:
        print("❌ 對照測試失敗: 強烈情緒新聞不應觸發節能過濾")
    
    print("\n" + "=" * 60)
    print("測試完成!")

if __name__ == "__main__":
    main()