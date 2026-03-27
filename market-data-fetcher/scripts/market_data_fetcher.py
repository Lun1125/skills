#!/usr/bin/env python3
"""
Market-Data-Fetcher - 即時市場數據檢索模組
使用 yfinance 套件抓取股票、ETF、加密貨幣的即時財務數據
作為 RAG (檢索增強生成) 的資料源，消除 AI 幻覺
"""

import yfinance as yf
import pandas as pd
import json
import sys
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import time
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CriticalDataError(Exception):
    """關鍵數據獲取失敗錯誤"""
    def __init__(self, message, ticker=None, attempts=None):
        self.message = message
        self.ticker = ticker
        self.attempts = attempts
        super().__init__(self.message)


class MarketDataFetcher:
    """市場數據獲取器"""
    
    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 300, cache_file: str = None):
        """
        初始化市場數據獲取器 (生產環境版本)
        
        Args:
            cache_enabled: 是否啟用緩存
            cache_ttl: 緩存存活時間 (秒)
            cache_file: 緩存文件路徑，如果為 None 則使用默認路徑
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        # 設置緩存文件路徑
        if cache_file is None:
            # 默認緩存文件路徑: 技能目錄下的 cache 文件夾
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cache_dir = os.path.join(script_dir, "..", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            self.cache_file = os.path.join(cache_dir, "market_data_cache.json")
        else:
            self.cache_file = cache_file
        
        # 初始化記憶體緩存 (用於快速訪問)
        self.data_cache = {}
        # 從文件加載現有緩存
        if self.cache_enabled:
            self._load_cache_from_file()
        
        self.request_delay = 2.0  # 請求間隔延遲 (秒) - 增加以避免速率限制
        self.max_retries = 3  # 最大重試次數
        self.retry_delay = 5  # 重試延遲 (秒)
        
        logger.info(f"MarketDataFetcher 初始化完成 (緩存: {cache_enabled}, TTL: {cache_ttl}秒, 文件: {self.cache_file})")
    
    def _get_cache_key(self, ticker: str) -> str:
        """生成緩存鍵"""
        return f"ticker_{ticker}"
    
    def _load_cache_from_file(self):
        """從文件加載緩存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 轉換緩存數據格式
                for key, value in cache_data.items():
                    if isinstance(value, dict) and 'data' in value and 'timestamp' in value:
                        try:
                            cached_time = datetime.fromisoformat(value['timestamp'])
                            self.data_cache[key] = (value['data'], cached_time)
                        except (ValueError, KeyError):
                            continue
                
                logger.info(f"從文件加載緩存: {len(self.data_cache)} 個項目")
            else:
                logger.info("緩存文件不存在，創建新緩存")
        except Exception as e:
            logger.error(f"加載緩存文件失敗: {e}")
            self.data_cache = {}
    
    def _save_cache_to_file(self):
        """保存緩存到文件"""
        try:
            cache_data = {}
            for key, (data, cached_time) in self.data_cache.items():
                cache_data[key] = {
                    'data': data,
                    'timestamp': cached_time.isoformat()
                }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"緩存已保存到文件: {self.cache_file}")
        except Exception as e:
            logger.error(f"保存緩存到文件失敗: {e}")
    
    def _check_cache(self, ticker: str) -> Optional[Dict]:
        """檢查緩存"""
        if not self.cache_enabled:
            return None
        
        cache_key = self._get_cache_key(ticker)
        if cache_key in self.data_cache:
            cached_data, cached_time = self.data_cache[cache_key]
            
            # 檢查緩存是否過期
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.debug(f"從緩存讀取數據: {ticker}")
                return cached_data
        
        return None
    
    def _update_cache(self, ticker: str, data: Dict):
        """更新緩存"""
        if not self.cache_enabled:
            return
        
        cache_key = self._get_cache_key(ticker)
        self.data_cache[cache_key] = (data, datetime.now())
        logger.debug(f"更新緩存: {ticker}")
        
        # 保存到文件
        self._save_cache_to_file()
    
    def _safe_get_info(self, ticker_obj: Any, key: str, default: Any = None) -> Any:
        """安全獲取 ticker 資訊"""
        try:
            info = ticker_obj.info
            if key in info:
                return info[key]
            else:
                logger.debug(f"鍵 '{key}' 不存在於 {ticker_obj.ticker} 的資訊中")
                return default
        except Exception as e:
            logger.warning(f"獲取 {key} 時出錯: {e}")
            return default
    
    def _format_price(self, value: Any) -> Optional[float]:
        """格式化價格值"""
        if value is None:
            return None
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return None
    
    def _format_large_number(self, value: Any) -> Optional[str]:
        """格式化大數字 (市值等)"""
        if value is None:
            return None
        try:
            num = float(value)
            if num >= 1e12:  # 兆
                return f"{num/1e12:.2f}T"
            elif num >= 1e9:  # 十億
                return f"{num/1e9:.2f}B"
            elif num >= 1e6:  # 百萬
                return f"{num/1e6:.2f}M"
            else:
                return f"{num:,.0f}"
        except (ValueError, TypeError):
            return None
    
    def _generate_mock_data(self, ticker: str) -> Dict[str, Any]:
        """生成模擬數據 (當 API 不可用時使用)"""
        
        # 根據股票代碼生成不同的模擬數據
        mock_data_templates = {
            "NVDA": {
                "current_price": 950.25,
                "previous_close": 945.50,
                "market_cap": 2.35e12,  # 2.35兆
                "trailing_pe": 65.3,
                "forward_pe": 55.2,
                "week52_high": 980.75,
                "week52_low": 450.25,
                "volume": 42500000,
                "average_volume": 38000000,
                "dividend_yield": 0.003,
                "eps": 14.55,
                "currency": "USD",
                "exchange": "NASDAQ",
                "short_name": "NVIDIA Corp",
                "long_name": "NVIDIA Corporation"
            },
            "2330.TW": {
                "current_price": 850.0,
                "previous_close": 845.5,
                "market_cap": 22.1e12,  # 22.1兆新台幣
                "trailing_pe": 18.5,
                "forward_pe": 16.8,
                "week52_high": 890.0,
                "week52_low": 550.0,
                "volume": 28500000,
                "average_volume": 25000000,
                "dividend_yield": 0.018,
                "eps": 45.9,
                "currency": "TWD",
                "exchange": "TWSE",
                "short_name": "台積電",
                "long_name": "台灣積體電路製造股份有限公司"
            },
            "BTC-USD": {
                "current_price": 87500.0,
                "previous_close": 87250.0,
                "market_cap": 1.71e12,  # 1.71兆
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
            "DXY": {
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
            "^TNX": {
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
            "^VIX": {
                "current_price": 18.50,
                "previous_close": 12.00,  # 修改為12.0以觸發 >15% 動能警報
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
            "GC=F": {
                "current_price": 2150.0,
                "previous_close": 2135.0,
                "market_cap": None,
                "trailing_pe": None,
                "forward_pe": None,
                "week52_high": 2250.0,
                "week52_low": 1850.0,
                "volume": None,
                "average_volume": None,
                "dividend_yield": None,
                "eps": None,
                "currency": "USD",
                "exchange": "COMMODITY",
                "short_name": "Gold Futures",
                "long_name": "Gold Futures (GC=F)"
            },
            "CL=F": {
                "current_price": 88.50,
                "previous_close": 87.80,
                "market_cap": None,
                "trailing_pe": None,
                "forward_pe": None,
                "week52_high": 95.50,
                "week52_low": 68.30,
                "volume": None,
                "average_volume": None,
                "dividend_yield": None,
                "eps": None,
                "currency": "USD",
                "exchange": "COMMODITY",
                "short_name": "Crude Oil Futures",
                "long_name": "Crude Oil Futures (CL=F)"
            }
        }
        
        # 默認模板 (用於其他股票)
        default_template = {
            "current_price": round(random.uniform(50, 500), 2),
            "previous_close": round(random.uniform(48, 495), 2),
            "market_cap": random.uniform(1e9, 500e9),
            "trailing_pe": round(random.uniform(10, 30), 1),
            "forward_pe": round(random.uniform(8, 25), 1),
            "week52_high": round(random.uniform(550, 600), 2),
            "week52_low": round(random.uniform(40, 45), 2),
            "volume": random.randint(1000000, 50000000),
            "average_volume": random.randint(800000, 45000000),
            "dividend_yield": round(random.uniform(0.01, 0.05), 3),
            "eps": round(random.uniform(1, 10), 2),
            "currency": "USD",
            "exchange": "NYSE",
            "short_name": ticker,
            "long_name": ticker
        }
        
        # 選擇模板
        if ticker in mock_data_templates:
            template = mock_data_templates[ticker]
        else:
            template = default_template
        
        # 添加隨機波動 (當前價格在前日收盤價基礎上 ±2%)
        if "current_price" in template and "previous_close" in template:
            base_price = template["previous_close"]
            fluctuation = random.uniform(-0.02, 0.02)
            template["current_price"] = round(base_price * (1 + fluctuation), 2)
        
        # 格式化數據
        formatted_data = {}
        for key, value in template.items():
            if key in ["current_price", "previous_close", "week52_high", "week52_low"]:
                formatted_data[key] = self._format_price(value)
            elif key == "market_cap":
                formatted_data[key] = self._format_large_number(value)
            elif key in ["trailing_pe", "forward_pe", "dividend_yield", "eps"]:
                formatted_data[key] = value
            else:
                formatted_data[key] = value
        
        return formatted_data
    
    def fetch_single(self, ticker: str) -> Dict[str, Any]:
        """
        獲取單個股票代碼的數據
        
        Args:
            ticker: 股票代碼 (如 'NVDA', '2330.TW', 'BTC-USD')
            
        Returns:
            結構化的市場數據字典
        """
        logger.info(f"獲取數據: {ticker}")
        
        # 檢查緩存
        cached_data = self._check_cache(ticker)
        if cached_data:
            return cached_data
        
        # 重試機制
        for attempt in range(self.max_retries):
            try:
                logger.info(f"嘗試 {attempt + 1}/{self.max_retries}: {ticker}")
                
                # 創建 Ticker 對象
                ticker_obj = yf.Ticker(ticker)
                
                # 獲取基本信息
                info = ticker_obj.info
                
                # 獲取歷史數據用於前日收盤價
                history = ticker_obj.history(period="2d")
                
                # 構建數據結構
                data = {
                    "ticker": ticker,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "data": {
                        "current_price": self._format_price(self._safe_get_info(ticker_obj, "currentPrice")),
                        "previous_close": self._format_price(self._safe_get_info(ticker_obj, "previousClose")),
                        "market_cap": self._format_large_number(self._safe_get_info(ticker_obj, "marketCap")),
                        "trailing_pe": self._safe_get_info(ticker_obj, "trailingPE"),
                        "forward_pe": self._safe_get_info(ticker_obj, "forwardPE"),
                        "week52_high": self._format_price(self._safe_get_info(ticker_obj, "fiftyTwoWeekHigh")),
                        "week52_low": self._format_price(self._safe_get_info(ticker_obj, "fiftyTwoWeekLow")),
                        "volume": self._safe_get_info(ticker_obj, "volume"),
                        "average_volume": self._safe_get_info(ticker_obj, "averageVolume"),
                        "dividend_yield": self._safe_get_info(ticker_obj, "dividendYield"),
                        "eps": self._safe_get_info(ticker_obj, "trailingEps"),
                        "currency": self._safe_get_info(ticker_obj, "currency", "USD"),
                        "exchange": self._safe_get_info(ticker_obj, "exchange", "Unknown"),
                        "short_name": self._safe_get_info(ticker_obj, "shortName", ticker),
                        "long_name": self._safe_get_info(ticker_obj, "longName", ticker)
                    },
                    "metadata": {
                        "data_source": "Yahoo Finance (yfinance)",
                        "cache_hit": False,
                        "request_time": datetime.now().isoformat(),
                        "attempt": attempt + 1
                    }
                }
                
                # 如果從 info 無法獲取當前價格，嘗試從歷史數據獲取
                if data["data"]["current_price"] is None and not history.empty:
                    try:
                        latest_close = history.iloc[-1]["Close"]
                        data["data"]["current_price"] = self._format_price(latest_close)
                    except Exception as e:
                        logger.warning(f"從歷史數據獲取當前價格失敗: {e}")
                
                # 如果從 info 無法獲取前日收盤價，嘗試從歷史數據獲取
                if data["data"]["previous_close"] is None and len(history) >= 2:
                    try:
                        previous_close = history.iloc[-2]["Close"]
                        data["data"]["previous_close"] = self._format_price(previous_close)
                    except Exception as e:
                        logger.warning(f"從歷史數據獲取前日收盤價失敗: {e}")
                
                # 更新緩存
                self._update_cache(ticker, data)
                
                # 添加請求延遲以避免速率限制
                time.sleep(self.request_delay)
                
                return data
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"嘗試 {attempt + 1} 失敗: {error_msg}")
                
                # 如果是速率限制錯誤，等待更長時間
                if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
                    wait_time = self.retry_delay * (attempt + 1)  # 指數退避
                    logger.info(f"速率限制，等待 {wait_time} 秒後重試")
                    time.sleep(wait_time)
                elif attempt < self.max_retries - 1:  # 如果不是最後一次嘗試
                    time.sleep(self.retry_delay)
                else:  # 最後一次嘗試失敗，拋出關鍵錯誤
                    error_msg = f"獲取 {ticker} 真實數據失敗，已重試 {self.max_retries} 次: {str(e)}"
                    logger.error(error_msg)
                    
                    # 拋出關鍵數據錯誤
                    raise CriticalDataError(
                        message=f"[CRITICAL ERROR] 無法取得真實數據，為保護資金安全，暫停 R1 決策。",
                        ticker=ticker,
                        attempts=self.max_retries
                    )
    
    def fetch_multiple(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """
        獲取多個股票代碼的數據 (同步版本)
        
        Args:
            tickers: 股票代碼列表
            
        Returns:
            數據字典列表
        """
        results = []
        
        for ticker in tickers:
            result = self.fetch_single(ticker)
            results.append(result)
        
        return results
    
    async def async_fetch_multiple(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """
        異步獲取多個股票代碼的數據 (生產環境版本)
        使用 asyncio 進行併發請求，目標 1 秒內完成
        
        Args:
            tickers: 股票代碼列表
            
        Returns:
            數據字典列表
        """
        import asyncio
        
        async def fetch_ticker(ticker: str) -> Dict[str, Any]:
            """異步獲取單個股票數據"""
            try:
                # 檢查緩存
                cached_data = self._check_cache(ticker)
                if cached_data:
                    return cached_data
                
                # 使用線程池執行同步的 fetch_single 方法
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.fetch_single, ticker)
                return result
                
            except CriticalDataError as e:
                # 重新拋出關鍵錯誤
                raise e
            except Exception as e:
                # 其他錯誤，拋出關鍵數據錯誤
                raise CriticalDataError(
                    message=f"[CRITICAL ERROR] 異步獲取 {ticker} 數據失敗: {str(e)}",
                    ticker=ticker,
                    attempts=1
                )
        
        # 創建所有任務
        tasks = [fetch_ticker(ticker) for ticker in tickers]
        
        # 併發執行所有任務
        logger.info(f"開始異步獲取 {len(tickers)} 個指標數據...")
        start_time = time.time()
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=False)
            elapsed_time = time.time() - start_time
            
            logger.info(f"✅ 異步數據獲取完成: {len(results)} 個指標, 耗時 {elapsed_time:.2f} 秒")
            
            # 驗證結果
            valid_results = []
            for result in results:
                if isinstance(result, dict) and result.get("status") == "success":
                    valid_results.append(result)
                else:
                    # 如果結果不是有效的成功數據，拋出錯誤
                    raise CriticalDataError(
                        message=f"[CRITICAL ERROR] 數據獲取返回無效結果",
                        ticker="multiple",
                        attempts=1
                    )
            
            return valid_results
            
        except asyncio.CancelledError:
            logger.error("異步數據獲取被取消")
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ 異步數據獲取失敗 (耗時 {elapsed_time:.2f} 秒): {e}")
            raise
    
    def fetch_batch(self, tickers: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        批量獲取數據 (優化版本)
        
        Args:
            tickers: 股票代碼列表
            max_concurrent: 最大並發請求數
            
        Returns:
            數據字典列表
        """
        # 簡單實現 - 可擴展為真正的並發
        return self.fetch_multiple(tickers)
    
    def get_available_indicators(self, ticker: str) -> List[str]:
        """
        獲取可用的數據指標
        
        Args:
            ticker: 股票代碼
            
        Returns:
            可用指標列表
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            return list(info.keys())
        except Exception as e:
            logger.error(f"獲取可用指標時出錯: {e}")
            return []
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        清除緩存
        
        Args:
            ticker: 指定清除的代碼，None 則清除全部
        """
        if ticker:
            cache_key = self._get_cache_key(ticker)
            if cache_key in self.data_cache:
                del self.data_cache[cache_key]
                logger.info(f"清除緩存: {ticker}")
        else:
            self.data_cache.clear()
            logger.info("清除全部緩存")
        
        # 保存到文件
        if self.cache_enabled:
            self._save_cache_to_file()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_size": len(self.data_cache),
            "cache_keys": list(self.data_cache.keys())
        }


def format_for_rag(data: Dict[str, Any]) -> str:
    """
    格式化數據為 RAG 友好的文本
    
    Args:
        data: 市場數據字典
        
    Returns:
        格式化文本
    """
    if data["status"] not in ["success", "success_mock"] or not data["data"]:
        return f"無法獲取 {data['ticker']} 的市場數據: {data.get('error', '未知錯誤')}"
    
    ticker = data["ticker"]
    d = data["data"]
    
    # 根據數據類型添加註釋
    data_source_note = ""
    if data["status"] == "success_mock":
        data_source_note = " (模擬數據 - 真實API暫時不可用)"
    
    text = f"""
{ticker} ({d.get('short_name', ticker)}) 市場數據{data_source_note}:
- 當前價格: {d.get('current_price', 'N/A')} {d.get('currency', 'USD')}
- 前日收盤: {d.get('previous_close', 'N/A')} {d.get('currency', 'USD')}
- 市值: {d.get('market_cap', 'N/A')}
- 本益比 (滾動): {d.get('trailing_pe', 'N/A')}
- 本益比 (預估): {d.get('forward_pe', 'N/A')}
- 52週高點: {d.get('week52_high', 'N/A')} {d.get('currency', 'USD')}
- 52週低點: {d.get('week52_low', 'N/A')} {d.get('currency', 'USD')}
- 成交量: {d.get('volume', 'N/A'):,}
- 平均成交量: {d.get('average_volume', 'N/A'):,}
- 股息收益率: {d.get('dividend_yield', 'N/A')}
- 每股盈餘 (EPS): {d.get('eps', 'N/A')}
- 交易所: {d.get('exchange', 'N/A')}
- 數據時間: {data['timestamp']}
"""
    
    return text.strip()


def main():
    """命令行主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Market-Data-Fetcher: 即時市場數據檢索")
    parser.add_argument("tickers", nargs="+", help="股票代碼列表 (如: NVDA 2330.TW BTC-USD)")
    parser.add_argument("--json", action="store_true", help="輸出 JSON 格式")
    parser.add_argument("--rag", action="store_true", help="輸出 RAG 友好格式")
    parser.add_argument("--no-cache", action="store_true", help="禁用緩存")
    parser.add_argument("--clear-cache", action="store_true", help="清除緩存")
    parser.add_argument("--cache-stats", action="store_true", help="顯示緩存統計")
    
    args = parser.parse_args()
    
    # 初始化獲取器
    fetcher = MarketDataFetcher(cache_enabled=not args.no_cache)
    
    # 處理特殊命令
    if args.clear_cache:
        fetcher.clear_cache()
        print("✅ 已清除全部緩存")
        return
    
    if args.cache_stats:
        stats = fetcher.get_cache_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return
    
    # 獲取數據
    results = fetcher.fetch_multiple(args.tickers)
    
    # 輸出結果
    if args.json:
        # JSON 輸出
        output = {
            "timestamp": datetime.now().isoformat(),
            "ticker_count": len(results),
            "results": results
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif args.rag:
        # RAG 格式輸出
        for result in results:
            print(format_for_rag(result))
            print("-" * 50)
    else:
        # 人類可讀格式
        for result in results:
            if result["status"] == "success":
                print(f"\n✅ {result['ticker']} 數據獲取成功 (真實數據)")
                data = result["data"]
                if data:
                    print(f"   當前價格: {data.get('current_price', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   前日收盤: {data.get('previous_close', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   市值: {data.get('market_cap', 'N/A')}")
                    print(f"   本益比: {data.get('trailing_pe', 'N/A')} (滾動) / {data.get('forward_pe', 'N/A')} (預估)")
                    print(f"   52週範圍: {data.get('week52_low', 'N/A')} - {data.get('week52_high', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   數據時間: {result['timestamp']}")
            elif result["status"] == "success_mock":
                print(f"\n⚠️  {result['ticker']} 數據獲取成功 (模擬數據)")
                data = result["data"]
                if data:
                    print(f"   當前價格: {data.get('current_price', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   前日收盤: {data.get('previous_close', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   市值: {data.get('market_cap', 'N/A')}")
                    print(f"   本益比: {data.get('trailing_pe', 'N/A')} (滾動) / {data.get('forward_pe', 'N/A')} (預估)")
                    print(f"   52週範圍: {data.get('week52_low', 'N/A')} - {data.get('week52_high', 'N/A')} {data.get('currency', 'USD')}")
                    print(f"   數據時間: {result['timestamp']}")
                print(f"   ⚠️  註釋: {result.get('error', '模擬數據')}")
            else:
                print(f"\n❌ {result['ticker']} 數據獲取失敗")
                print(f"   錯誤: {result.get('error', '未知錯誤')}")


if __name__ == "__main__":
    main()