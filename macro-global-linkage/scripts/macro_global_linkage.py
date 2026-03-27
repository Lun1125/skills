#!/usr/bin/env python3
"""
Macro-Global-Linkage - 全球總經連動模組
跨市場宏觀風險評估模組，分析 DXY、^TNX、^VIX、BTC-USD 等指標
生成宏觀風險地圖與燈號系統
"""

import sys
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

# 嘗試導入 AlertNotifier
try:
    from alert_notifier import AlertNotifier, get_notifier_from_env
except ImportError:
    AlertNotifier = None
    get_notifier_from_env = None
    logger = logging.getLogger(__name__)
    logger.warning("AlertNotifier 不可用，警報功能將被禁用")

# 添加 skills 目錄到路徑以便導入 MarketDataFetcher
# 嘗試多種路徑以適應不同安裝位置
possible_paths = [
    os.path.join(os.path.dirname(__file__), '../../market-data-fetcher/scripts'),
    os.path.join(os.path.dirname(__file__), 'skills/market-data-fetcher/scripts'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'market-data-fetcher/scripts'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'skills/market-data-fetcher/scripts')
]

for path in possible_paths:
    if os.path.exists(os.path.join(path, 'market_data_fetcher.py')):
        sys.path.insert(0, path)
        break
else:
    # 如果找不到，使用第一個路徑
    sys.path.insert(0, possible_paths[0])

try:
    from market_data_fetcher import MarketDataFetcher
except ImportError:
    # 如果無法直接導入，嘗試相對導入
    try:
        import importlib.util
        # 嘗試多種路徑查找 market_data_fetcher.py
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '../../market-data-fetcher/scripts/market_data_fetcher.py'),
            os.path.join(os.path.dirname(__file__), 'skills/market-data-fetcher/scripts/market_data_fetcher.py'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'market-data-fetcher/scripts/market_data_fetcher.py'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'skills/market-data-fetcher/scripts/market_data_fetcher.py')
        ]
        
        market_data_fetcher_path = None
        for path in possible_paths:
            if os.path.exists(path):
                market_data_fetcher_path = path
                break
        
        if market_data_fetcher_path is None:
            raise ImportError("無法找到 market_data_fetcher.py 文件")
        
        spec = importlib.util.spec_from_file_location(
            "market_data_fetcher",
            market_data_fetcher_path
        )
        market_data_fetcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(market_data_fetcher)
        MarketDataFetcher = market_data_fetcher.MarketDataFetcher
    except Exception as e:
        print(f"無法導入 MarketDataFetcher: {e}")
        MarketDataFetcher = None

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 自定義異常 ====================
class CriticalDataError(Exception):
    """關鍵數據缺失異常，當無法獲取足夠的宏觀數據時拋出"""
    def __init__(self, message, missing_indicators=None):
        super().__init__(message)
        self.missing_indicators = missing_indicators or []
        self.message = message
    
    def __str__(self):
        if self.missing_indicators:
            return f"{self.message} (缺失指標: {', '.join(self.missing_indicators)})"
        return self.message


# ==================== 文件緩存系統 ====================
class FileCache:
    """文件緩存系統，支持持久化存儲與TTL管理"""
    
    def __init__(self, cache_dir=".macro_cache", default_ttl=300):
        """
        初始化文件緩存
        
        Args:
            cache_dir: 緩存目錄路徑
            default_ttl: 默認緩存時間(秒)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"文件緩存初始化完成，目錄: {os.path.abspath(self.cache_dir)}")
    
    def _get_cache_path(self, key):
        """獲取緩存文件路徑"""
        safe_key = key.replace("^", "_").replace("=", "_").replace("-", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def set(self, key, data, ttl=None):
        """
        設置緩存
        
        Args:
            key: 緩存鍵
            data: 緩存數據
            ttl: 緩存時間(秒)，None使用默認值
        """
        cache_path = self._get_cache_path(key)
        ttl = ttl if ttl is not None else self.default_ttl
        
        cache_entry = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
            "key": key
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            logger.debug(f"緩存已設置: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"設置緩存失敗 {key}: {e}")
            return False
    
    def get(self, key):
        """
        獲取緩存
        
        Args:
            key: 緩存鍵
            
        Returns:
            緩存數據或None
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            # 檢查是否過期
            if time.time() > cache_entry["expires_at"]:
                logger.debug(f"緩存已過期: {key}")
                os.remove(cache_path)
                return None
            
            logger.debug(f"緩存命中: {key}")
            return cache_entry["data"]
        except Exception as e:
            logger.error(f"讀取緩存失敗 {key}: {e}")
            return None
    
    def delete(self, key):
        """刪除緩存"""
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.debug(f"緩存已刪除: {key}")
            return True
        return False
    
    def clear(self):
        """清除所有緩存"""
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info(f"緩存目錄已清空: {self.cache_dir}")
            return True
        return False
    
    def get_stats(self):
        """獲取緩存統計信息"""
        if not os.path.exists(self.cache_dir):
            return {"total": 0, "valid": 0, "expired": 0}
        
        total = 0
        valid = 0
        expired = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                total += 1
                cache_path = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)
                    
                    if time.time() > cache_entry["expires_at"]:
                        expired += 1
                    else:
                        valid += 1
                except:
                    expired += 1
        
        return {
            "total": total,
            "valid": valid,
            "expired": expired,
            "cache_dir": os.path.abspath(self.cache_dir)
        }


class MacroGlobalLinkage:
    """全球總經連動分析器"""
    
    def __init__(self, fetcher=None, test_mode=False, enable_file_cache=True, cache_dir=".macro_cache"):
        """
        初始化宏觀分析器
        
        Args:
            fetcher: MarketDataFetcher 實例，如果為 None 則創建新實例
            test_mode: 測試模式，如果為 True 則使用模擬數據
            enable_file_cache: 是否啟用文件緩存持久化
            cache_dir: 文件緩存目錄
        """
        self.test_mode = test_mode
        self.enable_file_cache = enable_file_cache
        
        # 初始化文件緩存系統
        if enable_file_cache:
            self.file_cache = FileCache(cache_dir=cache_dir, default_ttl=600)  # 10分鐘默認TTL
            logger.info(f"文件緩存持久化已啟用，目錄: {cache_dir}")
        else:
            self.file_cache = None
            logger.info("文件緩存持久化已禁用")
        
        if test_mode:
            self.fetcher = None
            logger.info("測試模式啟用，將使用模擬數據")
        elif fetcher is None and MarketDataFetcher is not None:
            self.fetcher = MarketDataFetcher(cache_enabled=True, cache_ttl=300)
        else:
            self.fetcher = fetcher
        
        # 定義核心宏觀指標 (v1.5 - 擴展至6大指標)
        self.core_indicators = {
            "DXY": {
                "name": "美元指數",
                "description": "美元對一籃子貨幣的匯率指數，反映美元強弱",
                "risk_direction": "positive",  # 上漲通常表示避險情緒
                "weight": 0.2  # 風險權重 (調整)
            },
            "^TNX": {
                "name": "美國10年期公債殖利率",
                "description": "美國10年期國債收益率，反映通脹預期和經濟前景",
                "risk_direction": "positive",  # 上漲可能表示通脹壓力
                "weight": 0.2  # 風險權重 (調整)
            },
            "^VIX": {
                "name": "恐慌指數",
                "description": "CBOE波動率指數，反映市場預期波動性和避險情緒",
                "risk_direction": "positive",  # 上漲表示市場恐慌
                "weight": 0.2  # 風險權重 (調整)
            },
            "BTC-USD": {
                "name": "比特幣",
                "description": "比特幣價格，作為高風險資產和市場情緒指標",
                "risk_direction": "negative",  # 上漲表示風險偏好
                "weight": 0.15  # 風險權重 (保持)
            },
            "GC=F": {
                "name": "黃金期貨",
                "description": "黃金期貨價格，反映避險情緒與通脹預期",
                "risk_direction": "positive",  # 上漲表示避險情緒
                "weight": 0.15  # 風險權重
            },
            "CL=F": {
                "name": "原油期貨",
                "description": "原油期貨價格，反映通脹壓力與經濟活動",
                "risk_direction": "positive",  # 上漲表示通脹壓力
                "weight": 0.1  # 風險權重
            }
        }
        
        # 風險閾值設定
        self.risk_thresholds = {
            "DXY": {
                "low": 95.0,    # 低於此為弱美元 (風險偏好)
                "medium": 100.0, # 100附近為中性
                "high": 105.0    # 高於此為強美元 (避險)
            },
            "^TNX": {
                "low": 3.0,     # 低於3%為寬鬆環境
                "medium": 4.0,   # 4%附近為中性
                "high": 5.0      # 高於5%為緊縮壓力
            },
            "^VIX": {
                "low": 15.0,    # 低於15為市場平靜
                "medium": 20.0,  # 15-20為正常波動
                "high": 25.0     # 高於25為市場恐慌
            },
            "BTC-USD": {
                "low": 70000,   # 低於7萬美元為弱勢
                "medium": 85000, # 8.5萬附近為中性
                "high": 100000   # 高於10萬美元為強勢
            },
            "GC=F": {
                "low": 1800.0,   # 低於1800美元為弱勢
                "medium": 2000.0, # 2000美元附近為中性
                "high": 2200.0    # 高於2200美元為強勢避險
            },
            "CL=F": {
                "low": 70.0,     # 低於70美元為弱勢
                "medium": 85.0,   # 85美元附近為中性
                "high": 100.0     # 高於100美元為高通脹壓力
            }
        }
        
        logger.info("MacroGlobalLinkage 初始化完成")
    
    def fetch_macro_data(self, use_cache=True, min_success_count=3) -> Dict[str, Any]:
        """
        獲取所有核心宏觀指標數據，支持文件緩存持久化與故障安全機制
        
        Args:
            use_cache: 是否使用文件緩存
            min_success_count: 最小成功數據指標數量，低於此值拋出CriticalDataError
            
        Returns:
            包含所有指標數據的字典
            
        Raises:
            CriticalDataError: 當無法獲取足夠的關鍵數據時拋出
        """
        tickers = list(self.core_indicators.keys())
        cache_key = "macro_data_all"
        
        # 1. 嘗試從文件緩存獲取數據
        if use_cache and self.file_cache is not None:
            cached_data = self.file_cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"✅ 從文件緩存加載宏觀數據 (共{len(cached_data)}個指標)")
                # 檢查緩存數據的有效性
                valid_count = sum(1 for ticker in tickers if ticker in cached_data and 
                                 cached_data[ticker].get("status") in ["success", "success_mock"])
                if valid_count >= min_success_count:
                    logger.info(f"緩存數據有效，有效指標數: {valid_count}/{len(tickers)}")
                    return cached_data
                else:
                    logger.warning(f"緩存數據有效性不足，有效指標數: {valid_count}/{len(tickers)}，重新獲取數據")
        
        # 2. 如果沒有緩存或緩存無效，從API獲取數據
        if self.fetcher is None:
            logger.error("MarketDataFetcher 不可用，無法獲取數據")
            # 檢查是否有可用的緩存數據（即使有效性不足）
            if use_cache and self.file_cache is not None:
                cached_data = self.file_cache.get(cache_key)
                if cached_data is not None:
                    logger.warning("使用有效性不足的緩存數據（API不可用）")
                    return cached_data
            raise CriticalDataError("MarketDataFetcher 不可用且無有效緩存數據")
        
        logger.info(f"開始從API獲取宏觀數據: {tickers}")
        
        try:
            # 使用批量獲取以提高效率
            results = self.fetcher.fetch_multiple(tickers)
            
            macro_data = {}
            success_count = 0
            failed_indicators = []
            
            for result in results:
                ticker = result.get("ticker", "")
                if ticker in self.core_indicators:
                    status = result.get("status", "unknown")
                    macro_data[ticker] = {
                        "ticker": ticker,
                        "name": self.core_indicators[ticker]["name"],
                        "data": result.get("data", {}),
                        "status": status,
                        "timestamp": result.get("timestamp", ""),
                        "metadata": result.get("metadata", {})
                    }
                    
                    # 記錄獲取狀態
                    if status == "success":
                        logger.info(f"✅ {ticker} 數據獲取成功 (真實數據)")
                        success_count += 1
                    elif status == "success_mock":
                        logger.warning(f"⚠️  {ticker} 使用模擬數據")
                        success_count += 1  # 模擬數據也算成功
                    else:
                        logger.error(f"❌ {ticker} 數據獲取失敗")
                        failed_indicators.append(ticker)
            
            # 3. 檢查是否獲取到足夠的關鍵數據
            if success_count < min_success_count:
                error_msg = f"關鍵數據獲取不足，成功指標數: {success_count}/{len(tickers)}，最小要求: {min_success_count}"
                logger.error(error_msg)
                
                # 如果啟用了緩存，嘗試使用緩存數據
                if use_cache and self.file_cache is not None:
                    cached_data = self.file_cache.get(cache_key)
                    if cached_data is not None:
                        logger.warning("API數據不足，但使用緩存數據作為備用")
                        return cached_data
                
                # 沒有可用的緩存數據，拋出CriticalDataError
                raise CriticalDataError(error_msg, failed_indicators)
            
            logger.info(f"✅ 宏觀數據獲取成功，成功指標數: {success_count}/{len(tickers)}")
            
            # 4. 將數據保存到文件緩存
            if use_cache and self.file_cache is not None and success_count > 0:
                if self.file_cache.set(cache_key, macro_data, ttl=600):  # 10分鐘TTL
                    logger.info(f"✅ 宏觀數據已保存到文件緩存，有效期10分鐘")
            
            return macro_data
            
        except CriticalDataError:
            # 重新拋出CriticalDataError
            raise
        except Exception as e:
            logger.error(f"獲取宏觀數據時發生錯誤: {e}")
            
            # 嘗試使用緩存數據
            if use_cache and self.file_cache is not None:
                cached_data = self.file_cache.get(cache_key)
                if cached_data is not None:
                    logger.warning(f"API獲取失敗，使用緩存數據作為備用: {e}")
                    return cached_data
            
            # 沒有可用的緩存數據，拋出CriticalDataError
            raise CriticalDataError(f"無法獲取宏觀數據: {e}")
    
    def calculate_risk_score(self, macro_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算各指標風險分數與整體風險評級
        
        Args:
            macro_data: 宏觀指標數據
            
        Returns:
            風險分析結果
        """
        if not macro_data:
            return {
                "overall_risk": "unknown",
                "risk_score": 0,
                "risk_color": "gray",
                "indicators": {},
                "error": "無可用數據"
            }
        
        indicator_scores = {}
        total_weighted_score = 0
        total_weight = 0
        
        for ticker, indicator_info in self.core_indicators.items():
            if ticker not in macro_data:
                logger.warning(f"缺少 {ticker} 數據，跳過計算")
                continue
            
            data = macro_data[ticker].get("data", {})
            current_price = data.get("current_price")
            
            if current_price is None:
                logger.warning(f"{ticker} 無當前價格數據")
                indicator_scores[ticker] = {
                    "score": 0,
                    "level": "unknown",
                    "price": None,
                    "weight": indicator_info["weight"],
                    "delta_pct": None,
                    "trend": "unknown",
                    "momentum_alert": False
                }
                continue
            
            # 計算變化率與趨勢狀態
            previous_close = data.get("previous_close")
            delta_pct = None
            trend = "unknown"
            momentum_alert = False
            
            if current_price is not None and previous_close is not None and previous_close != 0:
                delta_pct = ((current_price - previous_close) / previous_close) * 100
                if delta_pct > 1.0:
                    trend = "上升"
                elif delta_pct < -1.0:
                    trend = "下降"
                else:
                    trend = "盤整"
                
                # 動能警報: 單日變化率大於15%
                if abs(delta_pct) > 15.0:
                    momentum_alert = True
                    logger.warning(f"⚠️  {ticker} 觸發動能警報: 單日變化率 {delta_pct:.2f}%")
            
            # 根據指標類型和閾值計算風險分數 (0-100)
            thresholds = self.risk_thresholds[ticker]
            risk_direction = indicator_info["risk_direction"]
            
            if ticker == "DXY":
                # DXY: 越高越避險
                if current_price < thresholds["low"]:
                    score = 25  # 低風險 (弱美元)
                    level = "low"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 75  # 中高風險
                    level = "medium_high"
                else:
                    score = 100  # 高風險 (強美元)
                    level = "high"
                    
            elif ticker == "^TNX":
                # 10年期殖利率: 越高越緊縮
                if current_price < thresholds["low"]:
                    score = 25  # 低風險 (寬鬆)
                    level = "low"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 75  # 中高風險
                    level = "medium_high"
                else:
                    score = 100  # 高風險 (緊縮)
                    level = "high"
                    
            elif ticker == "^VIX":
                # VIX: 越高越恐慌
                if current_price < thresholds["low"]:
                    score = 25  # 低風險 (市場平靜)
                    level = "low"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 75  # 中高風險
                    level = "medium_high"
                else:
                    score = 100  # 高風險 (市場恐慌)
                    level = "high"
                    
            elif ticker == "BTC-USD":
                # BTC: 上漲表示風險偏好 (反向指標)
                if current_price < thresholds["low"]:
                    score = 75  # 中高風險 (避險)
                    level = "medium_high"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 25  # 低風險 (風險偏好)
                    level = "low"
                else:
                    score = 10  # 極低風險 (強風險偏好)
                    level = "very_low"
            
            elif ticker == "GC=F":
                # 黃金: 越高越避險
                if current_price < thresholds["low"]:
                    score = 25  # 低風險 (弱避險)
                    level = "low"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 75  # 中高風險
                    level = "medium_high"
                else:
                    score = 100  # 高風險 (強避險)
                    level = "high"
                    
            elif ticker == "CL=F":
                # 原油: 越高越通脹
                if current_price < thresholds["low"]:
                    score = 25  # 低風險 (低通脹)
                    level = "low"
                elif current_price < thresholds["medium"]:
                    score = 50  # 中低風險
                    level = "medium_low"
                elif current_price < thresholds["high"]:
                    score = 75  # 中高風險
                    level = "medium_high"
                else:
                    score = 100  # 高風險 (高通脹)
                    level = "high"
            
            # 根據風險方向調整分數
            if risk_direction == "negative":
                # 反向指標: 分數反轉
                score = 100 - score
            
            # 計算加權分數
            weight = indicator_info["weight"]
            weighted_score = score * weight
            
            indicator_scores[ticker] = {
                "score": score,
                "weighted_score": weighted_score,
                "level": level,
                "price": current_price,
                "weight": weight,
                "thresholds": thresholds,
                "direction": risk_direction,
                "delta_pct": delta_pct,
                "trend": trend,
                "momentum_alert": momentum_alert,
                "previous_close": previous_close if previous_close is not None else None
            }
            
            total_weighted_score += weighted_score
            total_weight += weight
        
        # 計算整體風險分數 (0-100)
        if total_weight > 0:
            overall_score = total_weighted_score / total_weight
        else:
            overall_score = 0
        
        # 確定整體風險等級和燈號
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
        
        # 生成投資建議
        recommendations = self.generate_recommendations(
            overall_risk, indicator_scores, macro_data
        )
        
        return {
            "overall_risk": overall_risk,
            "risk_level": risk_level,
            "risk_score": round(overall_score, 2),
            "risk_color": risk_color,
            "indicators": indicator_scores,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
            "data_status": {
                ticker: macro_data[ticker].get("status", "unknown") 
                for ticker in macro_data.keys()
            }
        }
    
    def generate_recommendations(self, overall_risk: str, 
                                indicator_scores: Dict[str, Any],
                                macro_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據風險分析生成投資建議
        
        Args:
            overall_risk: 整體風險等級
            indicator_scores: 各指標風險分數
            macro_data: 原始宏觀數據
            
        Returns:
            投資建議字典
        """
        recommendations = {
            "overall": "",
            "asset_allocation": {},
            "specific_actions": [],
            "risk_scenarios": []
        }
        
        # 整體建議
        if overall_risk == "low":
            recommendations["overall"] = "✅ 低風險環境：適合積極投資，可增加風險資產配置"
            recommendations["asset_allocation"] = {
                "stocks": "60-70%",
                "bonds": "20-25%",
                "cash": "5-10%",
                "crypto": "5-10%"
            }
            recommendations["specific_actions"] = [
                "增加科技股和成長股配置",
                "考慮適度槓桿操作",
                "加密貨幣可作為衛星配置"
            ]
            
        elif overall_risk == "medium_low":
            recommendations["overall"] = "🟢 中低風險環境：穩健投資，平衡配置"
            recommendations["asset_allocation"] = {
                "stocks": "50-60%",
                "bonds": "25-30%",
                "cash": "10-15%",
                "crypto": "3-7%"
            }
            recommendations["specific_actions"] = [
                "維持核心持股，分散配置",
                "關注防禦性板塊",
                "加密貨幣配置保持謹慎"
            ]
            
        elif overall_risk == "medium":
            recommendations["overall"] = "🟡 中風險環境：謹慎投資，降低風險暴露"
            recommendations["asset_allocation"] = {
                "stocks": "40-50%",
                "bonds": "30-35%",
                "cash": "15-20%",
                "crypto": "0-5%"
            }
            recommendations["specific_actions"] = [
                "減持高估值科技股",
                "增加現金部位",
                "考慮避險工具 (如黃金、美元)"
            ]
            
        elif overall_risk == "medium_high":
            recommendations["overall"] = "🟠 中高風險環境：防禦性配置，降低槓桿"
            recommendations["asset_allocation"] = {
                "stocks": "30-40%",
                "bonds": "35-40%",
                "cash": "20-25%",
                "crypto": "0-3%"
            }
            recommendations["specific_actions"] = [
                "減持風險資產",
                "增加債券和現金配置",
                "避免新增槓桿",
                "設定停損點位"
            ]
            
        else:  # high risk
            recommendations["overall"] = "🔴 高風險環境：極度謹慎，優先保本"
            recommendations["asset_allocation"] = {
                "stocks": "20-30%",
                "bonds": "40-50%",
                "cash": "25-35%",
                "crypto": "0%"
            }
            recommendations["specific_actions"] = [
                "大幅減持股票部位",
                "增加現金和短期債券",
                "避免任何槓桿操作",
                "準備危機應對計劃"
            ]
        
        # 檢測特定風險情境
        risk_scenarios = []
        
        # 情境1: 美元與殖利率雙升 (系統性風險)
        if ("DXY" in indicator_scores and "^TNX" in indicator_scores and
            indicator_scores["DXY"]["level"] in ["high", "medium_high"] and
            indicator_scores["^TNX"]["level"] in ["high", "medium_high"]):
            
            vix_level = indicator_scores.get("^VIX", {}).get("level", "unknown")
            if vix_level in ["high", "medium_high"]:
                risk_scenarios.append({
                    "name": "系統性風險上升",
                    "description": "美元與公債殖利率同時上漲，且恐慌指數偏高",
                    "impact": "高",
                    "action": "建議降低科技股與加密貨幣槓桿，增加避險資產"
                })
        
        # 情境2: 殖利率下降 + BTC上漲 (風險偏好)
        if ("^TNX" in indicator_scores and "BTC-USD" in indicator_scores and
            indicator_scores["^TNX"]["level"] in ["low", "medium_low"] and
            indicator_scores["BTC-USD"]["level"] in ["low", "very_low"]):
            
            risk_scenarios.append({
                "name": "Risk-On 環境",
                "description": "公債殖利率下降且比特幣上漲，顯示資金寬鬆與風險偏好",
                "impact": "中",
                "action": "可適度增加風險資產配置，關注成長型標的"
            })
        
        # 情境3: VIX 極度高 (市場恐慌)
        if "^VIX" in indicator_scores and indicator_scores["^VIX"]["level"] == "high":
            risk_scenarios.append({
                "name": "市場恐慌情緒",
                "description": "恐慌指數(VIX)處於高位，市場波動加劇",
                "impact": "高",
                "action": "避免追高殺低，保持現金等待機會"
            })
        
        # 情境4: 動能警報 (單日變化率大於15%)
        momentum_alerts = []
        for ticker, score_info in indicator_scores.items():
            if score_info.get("momentum_alert", False):
                delta_pct = score_info.get("delta_pct", 0)
                momentum_alerts.append({
                    "ticker": ticker,
                    "delta_pct": delta_pct,
                    "description": f"{ticker} 單日變化率達 {delta_pct:.2f}%，顯示劇烈波動"
                })
        
        if momentum_alerts:
            alert_tickers = [alert["ticker"] for alert in momentum_alerts]
            alert_descriptions = [alert["description"] for alert in momentum_alerts]
            risk_scenarios.append({
                "name": "動能警報觸發",
                "description": f"{', '.join(alert_tickers)} 單日變化率超過15%，市場劇烈波動",
                "impact": "高",
                "action": "立即檢視持倉風險，避免追漲殺跌，考慮暫時減倉觀望",
                "details": alert_descriptions
            })
        
        recommendations["risk_scenarios"] = risk_scenarios
        
        return recommendations
    
    def generate_risk_map(self, use_cache=True) -> Dict[str, Any]:
        """
        生成完整的全球宏觀風險地圖，包含故障安全機制
        
        Args:
            use_cache: 是否使用文件緩存
            
        Returns:
            風險地圖 JSON，即使在數據不足時也會返回結構化的錯誤響應
        """
        logger.info("開始生成全球宏觀風險地圖...")
        
        try:
            # 1. 獲取宏觀數據（可能拋出CriticalDataError）
            macro_data = self.fetch_macro_data(use_cache=use_cache)
            
            # 2. 計算風險分數
            risk_analysis = self.calculate_risk_score(macro_data)
            
            # 3. 構建完整風險地圖
            risk_map = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "module": "Macro-Global-Linkage",
                    "version": "1.5.0",
                    "indicators_analyzed": list(self.core_indicators.keys()),
                    "data_status": "success",
                    "cache_used": use_cache and self.file_cache is not None
                },
                "macro_data_summary": {
                    ticker: {
                        "name": self.core_indicators[ticker]["name"],
                        "current_price": macro_data[ticker].get("data", {}).get("current_price", "N/A") if ticker in macro_data else "N/A",
                        "status": macro_data[ticker].get("status", "unknown") if ticker in macro_data else "missing",
                        "description": self.core_indicators[ticker]["description"]
                    }
                    for ticker in self.core_indicators.keys()
                },
                "risk_analysis": risk_analysis,
                "visualization": {
                    "risk_lights": {
                        "color": risk_analysis.get("risk_color", "gray"),
                        "level": risk_analysis.get("risk_level", "未知"),
                        "score": risk_analysis.get("risk_score", 0)
                    },
                    "indicator_status": {
                        ticker: {
                            "score": risk_analysis.get("indicators", {}).get(ticker, {}).get("score", 0),
                            "level": risk_analysis.get("indicators", {}).get(ticker, {}).get("level", "unknown"),
                            "weight": self.core_indicators[ticker]["weight"]
                        }
                        for ticker in self.core_indicators.keys()
                    }
                }
            }
            
            logger.info(f"✅ 風險地圖生成完成，整體風險等級: {risk_analysis.get('risk_level', '未知')}")
            
            return risk_map
            
        except CriticalDataError as e:
            # 處理關鍵數據缺失錯誤
            logger.error(f"❌ 生成風險地圖時發生關鍵數據錯誤: {e}")
            
            # 返回錯誤狀態的風險地圖
            error_risk_map = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "module": "Macro-Global-Linkage",
                    "version": "1.5.0",
                    "indicators_analyzed": list(self.core_indicators.keys()),
                    "data_status": "critical_error",
                    "error_message": str(e),
                    "cache_used": use_cache and self.file_cache is not None
                },
                "macro_data_summary": {
                    ticker: {
                        "name": self.core_indicators[ticker]["name"],
                        "current_price": "N/A",
                        "status": "error",
                        "description": self.core_indicators[ticker]["description"]
                    }
                    for ticker in self.core_indicators.keys()
                },
                "risk_analysis": {
                    "overall_risk": "critical_error",
                    "risk_level": "關鍵數據錯誤",
                    "risk_score": 0,
                    "risk_color": "gray",
                    "indicators": {},
                    "error": str(e),
                    "recommendations": {
                        "overall": f"❌ 關鍵數據缺失: {e.message if hasattr(e, 'message') else str(e)}",
                        "asset_allocation": {
                            "stocks": "N/A",
                            "bonds": "N/A", 
                            "cash": "N/A",
                            "crypto": "N/A"
                        },
                        "specific_actions": [
                            "檢查網絡連接",
                            "驗證MarketDataFetcher配置",
                            "查看緩存數據狀態"
                        ],
                        "risk_scenarios": [{
                            "name": "數據獲取失敗",
                            "description": "無法獲取足夠的宏觀數據進行分析",
                            "impact": "高",
                            "action": "請檢查系統配置與網絡連接"
                        }]
                    }
                },
                "visualization": {
                    "risk_lights": {
                        "color": "gray",
                        "level": "關鍵數據錯誤",
                        "score": 0
                    },
                    "indicator_status": {
                        ticker: {
                            "score": 0,
                            "level": "error",
                            "weight": self.core_indicators[ticker]["weight"]
                        }
                        for ticker in self.core_indicators.keys()
                    }
                }
            }
            
            # 如果有缺失指標信息，添加到錯誤地圖
            if hasattr(e, 'missing_indicators') and e.missing_indicators:
                error_risk_map["metadata"]["missing_indicators"] = e.missing_indicators
                error_risk_map["risk_analysis"]["missing_indicators"] = e.missing_indicators
            
            return error_risk_map
            
        except Exception as e:
            # 處理其他異常
            logger.error(f"❌ 生成風險地圖時發生未預期錯誤: {e}")
            
            error_risk_map = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "module": "Macro-Global-Linkage",
                    "version": "1.5.0",
                    "indicators_analyzed": list(self.core_indicators.keys()),
                    "data_status": "unexpected_error",
                    "error_message": str(e),
                    "cache_used": use_cache and self.file_cache is not None
                },
                "macro_data_summary": {
                    ticker: {
                        "name": self.core_indicators[ticker]["name"],
                        "current_price": "N/A",
                        "status": "error",
                        "description": self.core_indicators[ticker]["description"]
                    }
                    for ticker in self.core_indicators.keys()
                },
                "risk_analysis": {
                    "overall_risk": "error",
                    "risk_level": "系統錯誤",
                    "risk_score": 0,
                    "risk_color": "gray",
                    "indicators": {},
                    "error": str(e),
                    "recommendations": {
                        "overall": f"❌ 系統錯誤: {str(e)}",
                        "asset_allocation": {
                            "stocks": "N/A",
                            "bonds": "N/A",
                            "cash": "N/A",
                            "crypto": "N/A"
                        },
                        "specific_actions": [
                            "檢查系統日誌",
                            "驗證依賴庫安裝",
                            "重試操作"
                        ]
                    }
                },
                "visualization": {
                    "risk_lights": {
                        "color": "gray",
                        "level": "系統錯誤",
                        "score": 0
                    },
                    "indicator_status": {
                        ticker: {
                            "score": 0,
                            "level": "error",
                            "weight": self.core_indicators[ticker]["weight"]
                        }
                        for ticker in self.core_indicators.keys()
                    }
                }
            }
            
            return error_risk_map
    
    def print_human_readable(self, risk_map: Dict[str, Any]):
        """
        輸出人類可讀格式的風險地圖
        
        Args:
            risk_map: 風險地圖數據
        """
        print("\n" + "="*60)
        print("🌍 全球宏觀風險地圖 (Macro Global Risk Map)")
        print("="*60)
        
        # 整體風險燈號
        risk_lights = risk_map["visualization"]["risk_lights"]
        risk_color = risk_lights["color"]
        risk_level = risk_lights["level"]
        risk_score = risk_lights["score"]
        
        color_emoji = {
            "green": "🟢",
            "yellow-green": "🟡",
            "yellow": "🟡",
            "orange": "🟠",
            "red": "🔴",
            "gray": "⚪"
        }
        
        emoji = color_emoji.get(risk_color, "⚪")
        
        print(f"\n📊 整體風險評估:")
        print(f"   {emoji} 風險燈號: {risk_color.upper()} ({risk_level})")
        print(f"   📈 風險分數: {risk_score}/100")
        print(f"   ⏰ 更新時間: {risk_map['metadata']['generated_at']}")
        
        # 宏觀數據摘要 (包含變化率)
        print(f"\n📈 核心宏觀指標 (6大指標):")
        summary = risk_map["macro_data_summary"]
        indicators = risk_map["risk_analysis"].get("indicators", {})
        
        for ticker, data in summary.items():
            status_emoji = "✅" if data["status"] == "success" else "⚠️" if data["status"] == "success_mock" else "❌"
            
            # 獲取變化率與趨勢
            indicator_info = indicators.get(ticker, {})
            delta_pct = indicator_info.get("delta_pct")
            trend = indicator_info.get("trend", "unknown")
            momentum_alert = indicator_info.get("momentum_alert", False)
            
            if delta_pct is not None:
                delta_str = f" ({trend} {delta_pct:+.2f}%)"
                if momentum_alert:
                    delta_str += " ⚠️"
                print(f"   {status_emoji} {ticker} ({data['name']}): {data['current_price']}{delta_str} ({data['status']})")
            else:
                print(f"   {status_emoji} {ticker} ({data['name']}): {data['current_price']} ({data['status']})")
        
        # 風險分析詳情 (包含變化率)
        print(f"\n🔍 風險分析詳情:")
        indicators = risk_map["risk_analysis"].get("indicators", {})
        for ticker, info in indicators.items():
            level = info.get("level", "unknown")
            score = info.get("score", 0)
            price = info.get("price", "N/A")
            delta_pct = info.get("delta_pct")
            trend = info.get("trend", "unknown")
            momentum_alert = info.get("momentum_alert", False)
            
            if delta_pct is not None:
                alert_str = " ⚠️" if momentum_alert else ""
                print(f"   • {ticker}: 分數={score}/100, 等級={level}, 價格={price}, 變化率={delta_pct:+.2f}% ({trend}){alert_str}")
            else:
                print(f"   • {ticker}: 分數={score}/100, 等級={level}, 價格={price}")
        
        # 投資建議
        print(f"\n💡 投資建議:")
        recommendations = risk_map["risk_analysis"].get("recommendations", {})
        print(f"   {recommendations.get('overall', '無建議')}")
        
        if recommendations.get("specific_actions"):
            print(f"\n   📝 具體行動:")
            for action in recommendations["specific_actions"]:
                print(f"     • {action}")
        
        if recommendations.get("risk_scenarios"):
            print(f"\n   ⚠️  風險情境檢測:")
            for scenario in recommendations["risk_scenarios"]:
                print(f"     • {scenario['name']}: {scenario['description']}")
                print(f"       建議: {scenario['action']}")
        
        print(f"\n" + "="*60)
        print("📋 數據來源: Yahoo Finance (透過 Market-Data-Fetcher)")
        print("⚠️  免責聲明: 此分析僅供參考，不構成投資建議")
        print("="*60)


def main():
    """命令行主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Macro-Global-Linkage: 全球總經連動分析")
    parser.add_argument("--json", action="store_true", help="輸出 JSON 格式")
    parser.add_argument("--test", action="store_true", help="測試模式 (使用模擬數據)")
    parser.add_argument("--quiet", action="store_true", help="安靜模式 (僅輸出 JSON)")
    
    args = parser.parse_args()
    
    # 初始化分析器
    analyzer = MacroGlobalLinkage()
    
    # 生成風險地圖
    risk_map = analyzer.generate_risk_map()
    
    # 輸出結果
    if args.json or args.quiet:
        # JSON 輸出
        print(json.dumps(risk_map, indent=2, ensure_ascii=False))
    else:
        # 人類可讀格式
        analyzer.print_human_readable(risk_map)


if __name__ == "__main__":
    main()