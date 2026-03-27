#!/usr/bin/env python3
"""
【市場情緒分析師】FinBERT v2.0 核心整合程式碼
CEO指令：實質代碼優化與開發 - 直接寫入檔案
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentLabel(Enum):
    """情緒標籤定義"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    
class LanguageCode(Enum):
    """支援的語言代碼"""
    EN = "en"  # 英文
    ZH = "zh"  # 中文
    JA = "ja"  # 日文
    KO = "ko"  # 韓文
    ES = "es"  # 西班牙文

@dataclass
class SentimentResult:
    """情緒分析結果數據類"""
    text: str
    language: str
    sentiment: str
    confidence: float
    scores: Dict[str, float]
    processed_at: str
    model_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)

class FinBERTv2Analyzer:
    """
    FinBERT v2.0 核心分析器
    實現多語言情緒分析與實時處理優化
    """
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        初始化FinBERT v2.0分析器
        
        Args:
            model_path: 模型路徑，如果為None則使用預設模型
            use_gpu: 是否使用GPU加速
        """
        self.model_version = "2.0.0"
        self.use_gpu = use_gpu
        self.supported_languages = [lang.value for lang in LanguageCode]
        
        # 初始化模型（這裡是模擬，實際應加載真實模型）
        self._init_model(model_path)
        
        # 初始化緩存系統
        self.cache = {}
        self.cache_max_size = 1000
        self.cache_ttl = 300  # 5分鐘
        
        # 性能監控
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
            "error_count": 0
        }
        
        logger.info(f"FinBERT v2.0分析器初始化完成，版本: {self.model_version}")
        logger.info(f"支援語言: {self.supported_languages}")
        
    def _init_model(self, model_path: Optional[str]):
        """初始化模型（模擬方法）"""
        # 實際實現應加載HuggingFace的FinBERT模型
        # 這裡使用模擬數據展示架構
        self.model_loaded = True
        self.model_name = "FinBERT-v2.0"
        
        # 模擬模型參數
        self.model_config = {
            "max_length": 512,
            "batch_size": 32,
            "thresholds": {
                "positive": 0.6,
                "negative": 0.6,
                "neutral_range": (0.4, 0.6)
            }
        }
        
    def detect_language(self, text: str) -> str:
        """
        檢測文本語言
        
        Args:
            text: 輸入文本
            
        Returns:
            語言代碼
        """
        # 簡化語言檢測（實際應使用專業庫如langdetect）
        if len(text) < 10:
            return LanguageCode.EN.value
            
        # 簡單的啟發式檢測
        import re
        zh_pattern = re.compile(r'[\u4e00-\u9fff]')
        ja_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
        ko_pattern = re.compile(r'[\uac00-\ud7af]')
        
        if zh_pattern.search(text):
            return LanguageCode.ZH.value
        elif ja_pattern.search(text):
            return LanguageCode.JA.value
        elif ko_pattern.search(text):
            return LanguageCode.KO.value
        else:
            return LanguageCode.EN.value
    
    def _get_cache_key(self, text: str, language: str) -> str:
        """生成緩存鍵"""
        import hashlib
        text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()
        return f"sentiment_{text_hash}"
    
    def _clean_cache(self):
        """清理過期緩存"""
        current_time = datetime.now().timestamp()
        keys_to_remove = []
        
        for key, (result, timestamp) in self.cache.items():
            if current_time - timestamp > self.cache_ttl:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.cache[key]
            
        # 如果緩存仍然過大，移除最舊的項目
        if len(self.cache) > self.cache_max_size:
            oldest_keys = sorted(self.cache.items(), key=lambda x: x[1][1])[:100]
            for key, _ in oldest_keys:
                del self.cache[key]
    
    async def analyze_sentiment_async(self, text: str, language: Optional[str] = None) -> SentimentResult:
        """
        異步分析文本情緒
        
        Args:
            text: 輸入文本
            language: 指定語言，如果為None則自動檢測
            
        Returns:
            SentimentResult對象
        """
        start_time = datetime.now()
        self.metrics["total_requests"] += 1
        
        try:
            # 1. 語言檢測
            if language is None:
                language = self.detect_language(text)
            elif language not in self.supported_languages:
                logger.warning(f"不支援的語言: {language}，使用自動檢測")
                language = self.detect_language(text)
            
            # 2. 檢查緩存
            cache_key = self._get_cache_key(text, language)
            if cache_key in self.cache:
                result, _ = self.cache[cache_key]
                self.metrics["cache_hits"] += 1
                logger.debug(f"緩存命中: {cache_key}")
                return result
            
            # 3. 實際情緒分析（這裡是模擬實現）
            # 實際應調用FinBERT v2.0模型
            sentiment, confidence, scores = self._analyze_with_model(text, language)
            
            # 4. 創建結果對象
            result = SentimentResult(
                text=text[:100] + "..." if len(text) > 100 else text,
                language=language,
                sentiment=sentiment,
                confidence=confidence,
                scores=scores,
                processed_at=datetime.now().isoformat(),
                model_version=self.model_version
            )
            
            # 5. 更新緩存
            self.cache[cache_key] = (result, datetime.now().timestamp())
            self._clean_cache()
            
            # 6. 更新性能指標
            processing_time = (datetime.now() - start_time).total_seconds()
            current_avg = self.metrics["avg_processing_time"]
            total_reqs = self.metrics["total_requests"]
            self.metrics["avg_processing_time"] = (
                (current_avg * (total_reqs - 1) + processing_time) / total_reqs
            )
            
            logger.info(f"情緒分析完成: {sentiment} (置信度: {confidence:.2f})")
            return result
            
        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"情緒分析失敗: {str(e)}")
            raise
    
    def _analyze_with_model(self, text: str, language: str) -> Tuple[str, float, Dict[str, float]]:
        """
        使用模型進行情緒分析（模擬實現）
        
        實際實現應調用:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        
        tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        """
        
        # 模擬分析邏輯
        import random
        
        # 根據語言調整基線
        language_bias = {
            LanguageCode.EN.value: 0.0,
            LanguageCode.ZH.value: 0.1,   # 中文稍微偏向正面
            LanguageCode.JA.value: -0.05, # 日文稍微偏向負面
            LanguageCode.KO.value: 0.0,
            LanguageCode.ES.value: 0.05
        }
        
        bias = language_bias.get(language, 0.0)
        
        # 生成模擬分數
        base_positive = 0.3 + random.uniform(-0.1, 0.2) + bias
        base_negative = 0.3 + random.uniform(-0.1, 0.2) - bias
        base_neutral = 0.4 + random.uniform(-0.1, 0.1)
        
        # 正規化
        total = base_positive + base_negative + base_neutral
        positive_score = base_positive / total
        negative_score = base_negative / total
        neutral_score = base_neutral / total
        
        scores = {
            "positive": positive_score,
            "negative": negative_score,
            "neutral": neutral_score
        }
        
        # 確定主要情緒
        max_score = max(scores.values())
        max_sentiment = [k for k, v in scores.items() if v == max_score][0]
        
        # 計算置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        confidence = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else 1.0
        
        return max_sentiment, confidence, scores
    
    async def batch_analyze(self, texts: List[str], languages: Optional[List[str]] = None) -> List[SentimentResult]:
        """
        批量分析文本情緒
        
        Args:
            texts: 文本列表
            languages: 對應的語言列表（可選）
            
        Returns:
            情緒分析結果列表
        """
        if languages is None:
            languages = [None] * len(texts)
        elif len(languages) != len(texts):
            raise ValueError("文本和語言列表長度必須一致")
        
        # 創建任務列表
        tasks = []
        for text, lang in zip(texts, languages):
            task = self.analyze_sentiment_async(text, lang)
            tasks.append(task)
        
        # 並行執行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"文本 {i} 分析失敗: {str(result)}")
                # 創建錯誤結果
                error_result = SentimentResult(
                    text=texts[i][:100] + "..." if len(texts[i]) > 100 else texts[i],
                    language=languages[i] if languages and i < len(languages) else "unknown",
                    sentiment="error",
                    confidence=0.0,
                    scores={},
                    processed_at=datetime.now().isoformat(),
                    model_version=self.model_version
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        return final_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            **self.metrics,
            "cache_size": len(self.cache),
            "model_version": self.model_version,
            "supported_languages": self.supported_languages,
            "using_gpu": self.use_gpu
        }
    
    def clear_cache(self):
        """清空緩存"""
        self.cache.clear()
        logger.info("緩存已清空")

class RealTimeSentimentEngine:
    """
    實時情緒分析引擎
    優化架構，支援高並發處理
    """
    
    def __init__(self, analyzer: FinBERTv2Analyzer, max_concurrent: int = 100):
        """
        初始化實時引擎
        
        Args:
            analyzer: FinBERT分析器實例
            max_concurrent: 最大並發數
        """
        self.analyzer = analyzer
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 實時監控
        self.realtime_metrics = {
            "active_tasks": 0,
            "queue_size": 0,
            "throughput_per_minute": 0,
            "error_rate": 0.0
        }
        
        self.task_queue = asyncio.Queue()
        self.processing_tasks = set()
        
        logger.info(f"實時情緒分析引擎初始化完成，最大並發: {max_concurrent}")
    
    async def process_stream(self, text_stream: List[str]) -> List[SentimentResult]:
        """
        處理文本流
        
        Args:
            text_stream: 文本流
            
        Returns:
            分析結果流
        """
        results = []
        
        async def process_item(text: str):
            async with self.semaphore:
                self.realtime_metrics["active_tasks"] += 1
                try:
                    result = await self.analyzer.analyze_sentiment_async(text)
                    return result
                finally:
                    self.realtime_metrics["active_tasks"] -= 1
        
        # 創建處理任務
        tasks = [process_item(text) for text in text_stream]
        
        # 並行處理
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"流處理失敗: {str(e)}")
                self.realtime_metrics["error_rate"] += 1 / len(text_stream)
        
        return results
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """獲取實時指標"""
        return {
            **self.realtime_metrics,
            "analyzer_metrics": self.analyzer.get_metrics()
        }

# 使用示例
async def main():
    """使用示例"""
    # 1. 初始化分析器
    analyzer = FinBERTv2Analyzer(use_gpu=True)
    
    # 2. 單一文本分析
    text_en = "The company reported strong earnings growth this quarter."
    result_en = await analyzer.analyze_sentiment_async(text_en)
    print(f"英文分析: {result_en.to_dict()}")
    
    # 3. 中文文本分析
    text_zh = "公司本季度財報表現強勁，營收大幅增長。"
    result_zh = await analyzer.analyze_sentiment_async(text_zh)
    print(f"中文分析: {result_zh.to_dict()}")
    
    # 4. 批量分析
    texts = [
        "Stock prices are rising steadily.",
        "市場對經濟前景感到擔憂。",
        "業績不如預期，投資者信心下降。"
    ]
    batch_results = await analyzer.batch_analyze(texts)
    print(f"批量分析完成，共 {len(batch_results)} 個結果")
    
    # 5. 顯示性能指標
    metrics = analyzer.get_metrics()
    print(f"性能指標: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())