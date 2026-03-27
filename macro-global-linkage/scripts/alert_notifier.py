#!/usr/bin/env python3
"""
Alert Notifier - 主動警報框架
用於在宏觀風險觸發警報時發送緊急推播
支援 LINE Notify 和 Telegram Bot Webhook
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertNotifier:
    """警報通知器"""
    
    def __init__(self, 
                 line_channel_access_token: Optional[str] = None,
                 line_channel_secret: Optional[str] = None,
                 line_user_id: Optional[str] = None,
                 telegram_bot_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None,
                 webhook_urls: Optional[List[str]] = None):
        """
        初始化警報通知器
        
        Args:
            line_channel_access_token: LINE Channel Access Token (對齊 bitfinex-lending)
            line_channel_secret: LINE Channel Secret (zeabur 設置)
            line_user_id: LINE User ID (對齊 bitfinex-lending)
            telegram_bot_token: Telegram Bot 令牌
            telegram_chat_id: Telegram 聊天 ID
            webhook_urls: 自定義 Webhook URL 列表
        """
        self.line_channel_access_token = line_channel_access_token
        self.line_channel_secret = line_channel_secret
        self.line_user_id = line_user_id
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.webhook_urls = webhook_urls or []
        
        # 檢查配置
        self.line_enabled = bool(line_channel_access_token and line_user_id)
        self.line_secret_available = bool(line_channel_secret)
        self.telegram_enabled = bool(telegram_bot_token and telegram_chat_id)
        self.webhook_enabled = bool(webhook_urls)
        
        logger.info(f"AlertNotifier 初始化完成: LINE={self.line_enabled}, "
                   f"Telegram={self.telegram_enabled}, Webhook={self.webhook_enabled}")
        if self.line_enabled:
            logger.info(f"LINE 配置: channel_access_token 存在, user_id={self.line_user_id[:6]}..., secret_available={self.line_secret_available}")
    
    async def send_line_notify(self, message: str) -> bool:
        """
        發送 LINE 訊息 (使用 LINE Messaging API，對齊 bitfinex-lending 模組)
        
        Args:
            message: 要發送的訊息
            
        Returns:
            發送是否成功
        """
        if not self.line_enabled:
            logger.warning("LINE 未配置，跳過發送")
            return False
        
        # 對齊 bitfinex-lending 模組的 LINE Messaging API
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.line_channel_access_token}'
        }
        
        payload = {
            'to': self.line_user_id,
            'messages': [{
                'type': 'text',
                'text': message
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ LINE 訊息發送成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ LINE 發送失敗: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ LINE 發送錯誤: {e}")
            return False
    
    async def send_telegram_message(self, message: str) -> bool:
        """
        發送 Telegram 訊息
        
        Args:
            message: 要發送的訊息
            
        Returns:
            發送是否成功
        """
        if not self.telegram_enabled:
            logger.warning("Telegram Bot 未配置，跳過發送")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("✅ Telegram 訊息發送成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Telegram 發送失敗: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Telegram 發送錯誤: {e}")
            return False
    
    async def send_webhook(self, payload: Dict[str, Any], url: str) -> bool:
        """
        發送 Webhook 通知
        
        Args:
            payload: 要發送的資料
            url: Webhook URL
            
        Returns:
            發送是否成功
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 201, 204]:
                        logger.info(f"✅ Webhook 發送到 {url} 成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Webhook 發送到 {url} 失敗: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Webhook 發送到 {url} 錯誤: {e}")
            return False
    
    def format_risk_alert(self, risk_map: Dict[str, Any]) -> str:
        """
        格式化風險警報訊息
        
        Args:
            risk_map: 風險地圖數據
            
        Returns:
            格式化後的警報訊息
        """
        risk_lights = risk_map.get("visualization", {}).get("risk_lights", {})
        risk_color = risk_lights.get("color", "unknown")
        risk_level = risk_lights.get("level", "未知")
        risk_score = risk_lights.get("score", 0)
        
        # 檢測動能警報
        momentum_alerts = []
        indicators = risk_map.get("risk_analysis", {}).get("indicators", {})
        for ticker, info in indicators.items():
            if info.get("momentum_alert", False):
                delta_pct = info.get("delta_pct", 0)
                momentum_alerts.append(f"{ticker}: {delta_pct:+.2f}%")
        
        # 構建訊息
        timestamp = risk_map.get("metadata", {}).get("generated_at", datetime.now().isoformat())
        
        if risk_color == "red":
            emoji = "🔴"
            severity = "【緊急警報】"
        elif risk_color == "orange":
            emoji = "🟠"
            severity = "【高風險警報】"
        elif momentum_alerts:
            emoji = "⚠️"
            severity = "【動能警報】"
        else:
            emoji = "🟡"
            severity = "【風險警示】"
        
        message = f"{emoji} {severity} 全球宏觀風險警報\n"
        message += f"⏰ 時間: {timestamp}\n"
        message += f"📊 風險等級: {risk_level} ({risk_score}/100)\n"
        message += f"🚦 風險燈號: {risk_color.upper()}\n"
        
        if momentum_alerts:
            message += f"⚡ 動能警報: {', '.join(momentum_alerts)}\n"
        
        # 添加具體警報情境
        risk_scenarios = risk_map.get("risk_analysis", {}).get("recommendations", {}).get("risk_scenarios", [])
        if risk_scenarios:
            message += f"🔍 檢測情境:\n"
            for scenario in risk_scenarios[:2]:  # 只顯示前兩個情境
                message += f"  • {scenario.get('name', '未知')}: {scenario.get('description', '')}\n"
        
        message += f"\n📋 建議操作: 請立即檢視持倉風險，必要時減倉或增加避險資產。"
        
        return message
    
    def format_critical_error(self, error_msg: str, ticker: Optional[str] = None) -> str:
        """
        格式化關鍵錯誤訊息
        
        Args:
            error_msg: 錯誤訊息
            ticker: 相關的股票代碼
            
        Returns:
            格式化後的錯誤訊息
        """
        timestamp = datetime.now().isoformat()
        
        message = "🚨【系統關鍵錯誤】🚨\n"
        message += f"⏰ 時間: {timestamp}\n"
        message += f"❌ 錯誤: {error_msg}\n"
        
        if ticker:
            message += f"📈 影響指標: {ticker}\n"
        
        message += f"\n⚠️  系統已暫停 R1 決策，請立即檢查數據源與網絡連接。"
        
        return message
    
    async def notify_risk_alert(self, risk_map: Dict[str, Any]) -> Dict[str, bool]:
        """
        發送風險警報通知
        
        Args:
            risk_map: 風險地圖數據
            
        Returns:
            各通道發送結果
        """
        results = {
            "line": False,
            "telegram": False,
            "webhooks": []
        }
        
        # 檢查是否需要發送警報
        risk_lights = risk_map.get("visualization", {}).get("risk_lights", {})
        risk_color = risk_lights.get("color", "unknown")
        
        # 檢測動能警報
        has_momentum_alert = False
        indicators = risk_map.get("risk_analysis", {}).get("indicators", {})
        for ticker, info in indicators.items():
            if info.get("momentum_alert", False):
                has_momentum_alert = True
                break
        
        # 觸發條件: 紅色燈號或動能警報
        should_alert = (risk_color in ["red", "orange"]) or has_momentum_alert
        
        if not should_alert:
            logger.info("未觸發警報條件，跳過通知發送")
            return results
        
        # 格式化訊息
        message = self.format_risk_alert(risk_map)
        
        # 併發發送到所有配置的通道
        tasks = []
        
        if self.line_enabled:
            tasks.append(self.send_line_notify(message))
        
        if self.telegram_enabled:
            tasks.append(self.send_telegram_message(message))
        
        # Webhook 發送
        if self.webhook_enabled:
            webhook_payload = {
                "event_type": "risk_alert",
                "timestamp": datetime.now().isoformat(),
                "risk_map": risk_map,
                "formatted_message": message
            }
            for url in self.webhook_urls:
                tasks.append(self.send_webhook(webhook_payload, url))
        
        # 執行所有任務
        if tasks:
            send_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            result_idx = 0
            
            if self.line_enabled:
                results["line"] = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                result_idx += 1
            
            if self.telegram_enabled:
                results["telegram"] = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                result_idx += 1
            
            if self.webhook_enabled:
                for url in self.webhook_urls:
                    if result_idx < len(send_results):
                        webhook_result = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                        results["webhooks"].append({
                            "url": url,
                            "success": webhook_result
                        })
                        result_idx += 1
        
        logger.info(f"警報通知發送完成: LINE={results.get('line')}, "
                   f"Telegram={results.get('telegram')}, "
                   f"Webhooks={len(results.get('webhooks', []))}")
        
        return results
    
    async def notify_critical_error(self, error_msg: str, ticker: Optional[str] = None) -> Dict[str, bool]:
        """
        發送關鍵錯誤通知
        
        Args:
            error_msg: 錯誤訊息
            ticker: 相關的股票代碼
            
        Returns:
            各通道發送結果
        """
        results = {
            "line": False,
            "telegram": False,
            "webhooks": []
        }
        
        # 格式化錯誤訊息
        message = self.format_critical_error(error_msg, ticker)
        
        # 併發發送到所有配置的通道
        tasks = []
        
        if self.line_enabled:
            tasks.append(self.send_line_notify(message))
        
        if self.telegram_enabled:
            tasks.append(self.send_telegram_message(message))
        
        # Webhook 發送
        if self.webhook_enabled:
            webhook_payload = {
                "event_type": "critical_error",
                "timestamp": datetime.now().isoformat(),
                "error_message": error_msg,
                "ticker": ticker,
                "formatted_message": message
            }
            for url in self.webhook_urls:
                tasks.append(self.send_webhook(webhook_payload, url))
        
        # 執行所有任務
        if tasks:
            send_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            result_idx = 0
            
            if self.line_enabled:
                results["line"] = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                result_idx += 1
            
            if self.telegram_enabled:
                results["telegram"] = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                result_idx += 1
            
            if self.webhook_enabled:
                for url in self.webhook_urls:
                    if result_idx < len(send_results):
                        webhook_result = send_results[result_idx] if not isinstance(send_results[result_idx], Exception) else False
                        results["webhooks"].append({
                            "url": url,
                            "success": webhook_result
                        })
                        result_idx += 1
        
        logger.info(f"關鍵錯誤通知發送完成: LINE={results.get('line')}, "
                   f"Telegram={results.get('telegram')}, "
                   f"Webhooks={len(results.get('webhooks', []))}")
        
        return results


def get_notifier_from_env() -> AlertNotifier:
    """
    從環境變數創建 AlertNotifier 實例
    對齊 bitfinex-lending 模組的環境變數名稱，並支援 LINE_CHANNEL_SECRET
    
    Returns:
        AlertNotifier 實例
    """
    # 對齊 bitfinex-lending 模組的環境變數名稱
    line_channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
    line_user_id = os.environ.get("LINE_USER_ID")
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # 從環境變數讀取 Webhook URLs (逗號分隔)
    webhook_urls_str = os.environ.get("WEBHOOK_URLS", "")
    webhook_urls = [url.strip() for url in webhook_urls_str.split(",") if url.strip()]
    
    return AlertNotifier(
        line_channel_access_token=line_channel_access_token,
        line_channel_secret=line_channel_secret,
        line_user_id=line_user_id,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        webhook_urls=webhook_urls
    )


async def main():
    """測試主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Alert Notifier 測試")
    parser.add_argument("--test-alert", action="store_true", help="測試風險警報")
    parser.add_argument("--test-error", action="store_true", help="測試錯誤警報")
    parser.add_argument("--message", type=str, help="自定義測試訊息")
    
    args = parser.parse_args()
    
    # 從環境變數創建通知器
    notifier = get_notifier_from_env()
    
    if args.test_alert:
        # 測試風險警報
        test_risk_map = {
            "metadata": {
                "generated_at": datetime.now().isoformat()
            },
            "visualization": {
                "risk_lights": {
                    "color": "red",
                    "level": "高風險",
                    "score": 85
                }
            },
            "risk_analysis": {
                "indicators": {
                    "^VIX": {
                        "momentum_alert": True,
                        "delta_pct": 18.5
                    }
                },
                "recommendations": {
                    "risk_scenarios": [
                        {
                            "name": "系統性風險上升",
                            "description": "美元與公債殖利率同時上漲"
                        }
                    ]
                }
            }
        }
        
        print("發送測試風險警報...")
        results = await notifier.notify_risk_alert(test_risk_map)
        print(f"結果: {results}")
    
    elif args.test_error:
        # 測試錯誤警報
        print("發送測試錯誤警報...")
        results = await notifier.notify_critical_error("測試關鍵錯誤訊息", "BTC-USD")
        print(f"結果: {results}")
    
    elif args.message:
        # 發送自定義訊息
        print(f"發送自定義訊息: {args.message}")
        if notifier.line_enabled:
            await notifier.send_line_notify(args.message)
        if notifier.telegram_enabled:
            await notifier.send_telegram_message(args.message)
    
    else:
        print("請指定測試類型: --test-alert, --test-error, 或 --message")


if __name__ == "__main__":
    asyncio.run(main())