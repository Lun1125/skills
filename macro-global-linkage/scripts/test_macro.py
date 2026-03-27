#!/usr/bin/env python3
"""
快速測試宏觀風險分析
直接使用模擬數據
"""

import json
import sys
import os
from datetime import datetime

# 模擬數據
MOCK_MACRO_DATA = {
    "DXY": {
        "ticker": "DXY",
        "name": "美元指數",
        "data": {
            "current_price": 103.50,
            "previous_close": 103.25,
            "market_cap": None,
            "trailing_pe": None,
            "forward_pe": None,
            "week52_high": 105.80,
            "week52_low": 99.50,
            "volume": None,
            "average_volume": None,
            "dividend_yield": None,
            "eps": None,
            "currency": "USD",
            "exchange": "INDEX",
            "short_name": "US Dollar Index",
            "long_name": "US Dollar Index (DXY)"
        },
        "status": "success_mock",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"data_source": "Mock Data"}
    },
    "^TNX": {
        "ticker": "^TNX",
        "name": "美國10年期公債殖利率",
        "data": {
            "current_price": 4.35,
            "previous_close": 4.30,
            "market_cap": None,
            "trailing_pe": None,
            "forward_pe": None,
            "week52_high": 4.80,
            "week52_low": 3.50,
            "volume": None,
            "average_volume": None,
            "dividend_yield": None,
            "eps": None,
            "currency": "USD",
            "exchange": "INDEX",
            "short_name": "10-Year Treasury Yield",
            "long_name": "CBOE 10-Year Treasury Note Yield (^TNX)"
        },
        "status": "success_mock",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"data_source": "Mock Data"}
    },
    "^VIX": {
        "ticker": "^VIX",
        "name": "恐慌指數",
        "data": {
            "current_price": 18.50,
            "previous_close": 18.20,
            "market_cap": None,
            "trailing_pe": None,
            "forward_pe": None,
            "week52_high": 32.50,
            "week52_low": 12.80,
            "volume": None,
            "average_volume": None,
            "dividend_yield": None,
            "eps": None,
            "currency": "USD",
            "exchange": "INDEX",
            "short_name": "Volatility Index",
            "long_name": "CBOE Volatility Index (VIX)"
        },
        "status": "success_mock",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"data_source": "Mock Data"}
    },
    "BTC-USD": {
        "ticker": "BTC-USD",
        "name": "比特幣",
        "data": {
            "current_price": 87500.0,
            "previous_close": 87250.0,
            "market_cap": 1.71e12,
            "trailing_pe": None,
            "forward_pe": None,
            "week52_high": 92000.0,
            "week52_low": 45000.0,
            "volume": 32500000000,
            "average_volume": 28000000000,
            "dividend_yield": None,
            "eps": None,
            "currency": "USD",
            "exchange": "CRYPTO",
            "short_name": "Bitcoin USD",
            "long_name": "Bitcoin"
        },
        "status": "success_mock",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"data_source": "Mock Data"}
    }
}

def calculate_risk_score(macro_data):
    """計算風險分數 (簡化版本)"""
    
    # 風險閾值
    thresholds = {
        "DXY": {"low": 95.0, "medium": 100.0, "high": 105.0},
        "^TNX": {"low": 3.0, "medium": 4.0, "high": 5.0},
        "^VIX": {"low": 15.0, "medium": 20.0, "high": 25.0},
        "BTC-USD": {"low": 70000, "medium": 85000, "high": 100000}
    }
    
    # 風險方向
    risk_direction = {
        "DXY": "positive",
        "^TNX": "positive", 
        "^VIX": "positive",
        "BTC-USD": "negative"
    }
    
    # 權重
    weights = {
        "DXY": 0.3,
        "^TNX": 0.3,
        "^VIX": 0.25,
        "BTC-USD": 0.15
    }
    
    indicator_scores = {}
    total_weighted_score = 0
    total_weight = 0
    
    for ticker, data in macro_data.items():
        current_price = data["data"]["current_price"]
        
        if ticker == "DXY":
            if current_price < thresholds[ticker]["low"]:
                score = 25
                level = "low"
            elif current_price < thresholds[ticker]["medium"]:
                score = 50
                level = "medium_low"
            elif current_price < thresholds[ticker]["high"]:
                score = 75
                level = "medium_high"
            else:
                score = 100
                level = "high"
                
        elif ticker == "^TNX":
            if current_price < thresholds[ticker]["low"]:
                score = 25
                level = "low"
            elif current_price < thresholds[ticker]["medium"]:
                score = 50
                level = "medium_low"
            elif current_price < thresholds[ticker]["high"]:
                score = 75
                level = "medium_high"
            else:
                score = 100
                level = "high"
                
        elif ticker == "^VIX":
            if current_price < thresholds[ticker]["low"]:
                score = 25
                level = "low"
            elif current_price < thresholds[ticker]["medium"]:
                score = 50
                level = "medium_low"
            elif current_price < thresholds[ticker]["high"]:
                score = 75
                level = "medium_high"
            else:
                score = 100
                level = "high"
                
        elif ticker == "BTC-USD":
            if current_price < thresholds[ticker]["low"]:
                score = 75
                level = "medium_high"
            elif current_price < thresholds[ticker]["medium"]:
                score = 50
                level = "medium_low"
            elif current_price < thresholds[ticker]["high"]:
                score = 25
                level = "low"
            else:
                score = 10
                level = "very_low"
        
        # 反向指標調整
        if risk_direction[ticker] == "negative":
            score = 100 - score
        
        weight = weights[ticker]
        weighted_score = score * weight
        
        indicator_scores[ticker] = {
            "score": score,
            "weighted_score": weighted_score,
            "level": level,
            "price": current_price,
            "weight": weight
        }
        
        total_weighted_score += weighted_score
        total_weight += weight
    
    # 整體風險分數
    if total_weight > 0:
        overall_score = total_weighted_score / total_weight
    else:
        overall_score = 0
    
    # 風險等級
    if overall_score < 30:
        overall_risk = "low"
        risk_color = "green"
        risk_level = "低風險"
    elif overall_score < 50:
        overall_risk = "medium_low"
        risk_color = "yellow-green"
        risk_level = "中低風險"
    elif overall_score < 70:
        overall_risk = "medium"
        risk_color = "yellow"
        risk_level = "中風險"
    elif overall_score < 85:
        overall_risk = "medium_high"
        risk_color = "orange"
        risk_level = "中高風險"
    else:
        overall_risk = "high"
        risk_color = "red"
        risk_level = "高風險"
    
    # 風險情境檢測
    risk_scenarios = []
    
    # 情境1: 美元與殖利率雙升
    if (indicator_scores["DXY"]["level"] in ["high", "medium_high"] and
        indicator_scores["^TNX"]["level"] in ["high", "medium_high"]):
        
        if indicator_scores["^VIX"]["level"] in ["high", "medium_high"]:
            risk_scenarios.append({
                "name": "系統性風險上升",
                "description": "美元與公債殖利率同時上漲，且恐慌指數偏高",
                "impact": "高",
                "action": "建議降低科技股與加密貨幣槓桿，增加避險資產"
            })
    
    # 情境2: 殖利率下降 + BTC上漲
    if (indicator_scores["^TNX"]["level"] in ["low", "medium_low"] and
        indicator_scores["BTC-USD"]["level"] in ["low", "very_low"]):
        
        risk_scenarios.append({
            "name": "Risk-On 環境",
            "description": "公債殖利率下降且比特幣上漲，顯示資金寬鬆與風險偏好",
            "impact": "中",
            "action": "可適度增加風險資產配置，關注成長型標的"
        })
    
    return {
        "overall_risk": overall_risk,
        "risk_level": risk_level,
        "risk_score": round(overall_score, 2),
        "risk_color": risk_color,
        "indicators": indicator_scores,
        "risk_scenarios": risk_scenarios,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """主函數"""
    print("🌍 全球宏觀風險分析 (模擬數據)")
    print("=" * 60)
    
    # 計算風險
    risk_analysis = calculate_risk_score(MOCK_MACRO_DATA)
    
    # 輸出結果
    print(f"\n📊 整體風險評估:")
    print(f"   風險燈號: {risk_analysis['risk_color'].upper()} ({risk_analysis['risk_level']})")
    print(f"   風險分數: {risk_analysis['risk_score']}/100")
    
    print(f"\n📈 核心指標數據:")
    for ticker, data in MOCK_MACRO_DATA.items():
        price = data["data"]["current_price"]
        print(f"   {ticker}: {price}")
    
    print(f"\n🔍 指標風險分數:")
    for ticker, score_info in risk_analysis["indicators"].items():
        print(f"   {ticker}: 分數={score_info['score']}/100, 等級={score_info['level']}")
    
    print(f"\n💡 風險情境檢測:")
    if risk_analysis["risk_scenarios"]:
        for scenario in risk_analysis["risk_scenarios"]:
            print(f"   • {scenario['name']}: {scenario['description']}")
            print(f"     建議: {scenario['action']}")
    else:
        print("   未檢測到特殊風險情境")
    
    print(f"\n📋 JSON 輸出:")
    print(json.dumps(risk_analysis, indent=2, ensure_ascii=False))
    
    print(f"\n⏰ 分析時間: {risk_analysis['timestamp']}")
    print("=" * 60)

if __name__ == "__main__":
    main()