#!/usr/bin/env python3
"""
FinBERT 情緒分析測試腳本
測試真實美股新聞標題的情緒分析與節能過濾功能
"""

import os
import sys
import json
from datetime import datetime

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(skill_dir)

from scripts.finbert_processor import FinBERTProcessor

def test_neutral_news():
    """測試中性新聞（應該觸發節能過濾）"""
    print("測試 1: 中性美股新聞標題")
    print("=" * 50)
    
    # 中性新聞示例 - 市場平淡，沒有重大消息
    neutral_news = [
        "市場交易平淡，投資者觀望聯準會會議結果",
        "蘋果股價在150美元附近震盪，成交量一般",
        "標準普爾500指數微幅上漲0.1%，市場缺乏方向",
        "特斯拉股價持平，等待季度財報發布",
        "微軟季度營收符合分析師預期，股價變化不大"
    ]
    
    processor = FinBERTProcessor()
    
    for i, news in enumerate(neutral_news, 1):
        print(f"\n{i}. 新聞標題: {news}")
        print("-" * 40)
        
        # 分析情緒
        result = processor.analyze_sentiment(news)
        
        print(f"   情緒分數: {result.get('sentiment_score', 'N/A')}")
        print(f"   信心度: {result.get('confidence', 'N/A')}")
        print(f"   標籤: {result.get('label', 'N/A')}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        print(f"   是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        print(f"   阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
        
        if should_block:
            print(f"   🚫 原因: {reason}")
        else:
            print(f"   ✅ 允許深度分析")
    
    print("\n" + "=" * 50)

def test_positive_news():
    """測試正面新聞（不應該觸發節能過濾）"""
    print("\n測試 2: 正面美股新聞標題")
    print("=" * 50)
    
    # 正面新聞示例
    positive_news = [
        "蘋果發布強勁財報，營收增長超預期，股價大漲5%",
        "特斯拉獲得巨額電動車訂單，分析師上調目標價",
        "微軟雲業務強勁增長，季度利潤創歷史新高",
        "輝達AI晶片需求旺盛，營收預測大幅上調",
        "亞馬遜宣布大規模回購計劃，股價應聲上漲"
    ]
    
    processor = FinBERTProcessor()
    
    for i, news in enumerate(positive_news, 1):
        print(f"\n{i}. 新聞標題: {news}")
        print("-" * 40)
        
        # 分析情緒
        result = processor.analyze_sentiment(news)
        
        print(f"   情緒分數: {result.get('sentiment_score', 'N/A')}")
        print(f"   信心度: {result.get('confidence', 'N/A')}")
        print(f"   標籤: {result.get('label', 'N/A')}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        print(f"   是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        print(f"   阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
        
        if should_block:
            print(f"   🚫 原因: {reason}")
        else:
            print(f"   ✅ 允許深度分析")
    
    print("\n" + "=" * 50)

def test_negative_news():
    """測試負面新聞（不應該觸發節能過濾）"""
    print("\n測試 3: 負面美股新聞標題")
    print("=" * 50)
    
    # 負面新聞示例
    negative_news = [
        "特斯拉因供應鏈問題下調生產目標，股價重挫8%",
        "蘋果面臨反壟斷調查，股價下跌3%",
        "微軟雲業務增長放緩，分析師下調評級",
        "輝達面臨晶片出口限制，股價大幅下跌",
        "亞馬遜季度虧損超預期，股價創今年新低"
    ]
    
    processor = FinBERTProcessor()
    
    for i, news in enumerate(negative_news, 1):
        print(f"\n{i}. 新聞標題: {news}")
        print("-" * 40)
        
        # 分析情緒
        result = processor.analyze_sentiment(news)
        
        print(f"   情緒分數: {result.get('sentiment_score', 'N/A')}")
        print(f"   信心度: {result.get('confidence', 'N/A')}")
        print(f"   標籤: {result.get('label', 'N/A')}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        print(f"   是否雜訊: {'✅ 是' if is_noise else '❌ 否'}")
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        print(f"   阻止 deepseek-reasoner: {'✅ 是' if should_block else '❌ 否'}")
        
        if should_block:
            print(f"   🚫 原因: {reason}")
        else:
            print(f"   ✅ 允許深度分析")
    
    print("\n" + "=" * 50)

def test_real_time_news():
    """測試實時新聞標題（混合情緒）"""
    print("\n測試 4: 實時美股新聞標題混合測試")
    print("=" * 50)
    
    # 混合情緒新聞示例
    mixed_news = [
        "聯準會維持利率不變，符合市場預期",  # 中性
        "蘋果Vision Pro預購火爆，分析師看好AR市場",  # 正面
        "特斯拉中國工廠因疫情暫時停工",  # 負面
        "微軟與OpenAI深化合作，股價微幅上漲",  # 輕微正面
        "亞馬遜Prime Day銷售數據即將公布",  # 中性
        "輝達AI晶片供不應求，股價創歷史新高",  # 強烈正面
        "Netflix用戶增長放緩，股價下跌2%"  # 負面
    ]
    
    processor = FinBERTProcessor()
    
    stats = {
        "total": 0,
        "noise": 0,
        "blocked": 0,
        "allowed": 0
    }
    
    for i, news in enumerate(mixed_news, 1):
        print(f"\n{i}. 新聞標題: {news}")
        print("-" * 40)
        
        stats["total"] += 1
        
        # 分析情緒
        result = processor.analyze_sentiment(news)
        
        sentiment_score = result.get('sentiment_score', 0)
        label = result.get('label', 'unknown')
        
        print(f"   情緒分數: {sentiment_score}")
        print(f"   標籤: {label}")
        
        # 檢查是否為雜訊
        is_noise = processor.is_noise(result)
        if is_noise:
            stats["noise"] += 1
            print(f"   是否雜訊: ✅ 是")
        else:
            print(f"   是否雜訊: ❌ 否")
        
        # 檢查是否需要阻止 deepseek-reasoner
        should_block, reason = processor.should_block_deepseek_reasoner(result)
        if should_block:
            stats["blocked"] += 1
            print(f"   阻止 deepseek-reasoner: ✅ 是")
            print(f"   🚫 原因: {reason}")
        else:
            stats["allowed"] += 1
            print(f"   阻止 deepseek-reasoner: ❌ 否")
            print(f"   ✅ 允許深度分析")
    
    print("\n" + "=" * 50)
    print("節能過濾統計報告:")
    print(f"   總新聞數: {stats['total']}")
    print(f"   雜訊新聞: {stats['noise']} ({stats['noise']/stats['total']*100:.1f}%)")
    print(f"   阻止分析: {stats['blocked']} ({stats['blocked']/stats['total']*100:.1f}%)")
    print(f"   允許分析: {stats['allowed']} ({stats['allowed']/stats['total']*100:.1f}%)")
    
    if stats['blocked'] > 0:
        print(f"\n🎯 節能效果: 可節省 {stats['blocked']/stats['total']*100:.1f}% 的 deepseek-reasoner 調用")
    else:
        print(f"\n⚠️ 注意: 本次測試未觸發節能過濾")
    
    print("=" * 50)

def main():
    """主測試函數"""
    print("FinBERT 情緒分析與節能過濾測試")
    print("測試時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 檢查 API Token
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
    if not api_token:
        print("❌ 錯誤: HUGGINGFACE_API_TOKEN 環境變數未設置")
        print("請設置環境變數: export HUGGINGFACE_API_TOKEN='您的令牌'")
        return
    
    print(f"✅ API Token 已設置 (長度: {len(api_token)})")
    
    # 運行測試
    test_neutral_news()
    test_positive_news()
    test_negative_news()
    test_real_time_news()
    
    print("\n測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()