"""
إرسال التنبيهات عبر Telegram
"""

import requests
from typing import Dict, Optional
import config
from datetime import datetime


class TelegramNotifier:
    """
    إرسال الرسائل عبر Telegram Bot
    """
    
    def __init__(self):
        """
        تهيئة البوت
        """
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        إرسال رسالة نصية
        
        Args:
            text: نص الرسالة
            parse_mode: نوع التنسيق (HTML أو Markdown)
        
        Returns:
            True إذا تم الإرسال بنجاح
        """
        if not self.bot_token or not self.chat_id:
            print("⚠️ لم يتم تكوين Telegram Bot")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ فشل إرسال الرسالة: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في إرسال الرسالة: {e}")
            return False
    
    def send_signal(self, signal: Dict) -> bool:
        """
        إرسال إشارة تداول
        
        Args:
            signal: قاموس يحتوي على معلومات الإشارة
        
        Returns:
            True إذا تم الإرسال بنجاح
        """
        # تحديد الأيقونة حسب نوع الإشارة
        icon = self._get_signal_icon(signal['type'])
        
        # تنسيق الرسالة
        message = self._format_signal_message(signal, icon)
        
        return self.send_message(message)
    
    def _get_signal_icon(self, signal_type: str) -> str:
        """
        الحصول على الأيقونة المناسبة لنوع الإشارة
        
        Args:
            signal_type: نوع الإشارة
        
        Returns:
            رمز الأيقونة
        """
        icons = {
            'ready_buy': '🟡',
            'entry_buy': '🟢',
            'ready_sell': '🟡',
            'entry_sell': '🔴'
        }
        return icons.get(signal_type, '⚪')
    
    def _format_signal_message(self, signal: Dict, icon: str) -> str:
        """
        تنسيق رسالة الإشارة
        
        Args:
            signal: معلومات الإشارة
            icon: أيقونة الإشارة
        
        Returns:
            الرسالة المنسقة
        """
        timestamp = signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # العنوان
        header = f"{icon} <b>إشارة جديدة</b> {icon}\n"
        header += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # معلومات الزوج
        pair_info = f"💱 <b>الزوج:</b> {signal['symbol']}\n"
        pair_info += f"💰 <b>السعر:</b> {signal['price']:.5f}\n"
        pair_info += f"⏰ <b>الوقت:</b> {timestamp}\n\n"
        
        # السبب
        reason = f"📊 <b>التحليل:</b>\n{signal['reason']}\n\n"
        
        # التذييل
        footer = "━━━━━━━━━━━━━━━━━━━━\n"
        footer += "🤖 <i>Manus Trading Bot</i>"
        
        return header + pair_info + reason + footer
    
    def send_startup_message(self) -> bool:
        """
        إرسال رسالة بدء التشغيل
        
        Returns:
            True إذا تم الإرسال بنجاح
        """
        message = (
            "🚀 <b>البوت بدأ العمل</b> 🚀\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 الأزواج المراقبة: {len(config.TRADING_PAIRS)}\n"
            f"🔄 التحديث كل: {config.UPDATE_INTERVAL} ثانية\n\n"
            "✅ جاهز لمراقبة السوق\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        return self.send_message(message)
    
    def send_error_message(self, error: str) -> bool:
        """
        إرسال رسالة خطأ
        
        Args:
            error: وصف الخطأ
        
        Returns:
            True إذا تم الإرسال بنجاح
        """
        message = (
            "❌ <b>خطأ في البوت</b> ❌\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📝 الخطأ: {error}\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        return self.send_message(message)
