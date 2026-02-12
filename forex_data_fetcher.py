"""
جلب بيانات الفوركس الحقيقية باستخدام Twelve Data API
"""

import pandas as pd
import requests
from typing import Optional
from datetime import datetime
import config
from indicators import add_indicators


class ForexDataFetcher:
    """
    جلب وتحليل بيانات الفوركس الحقيقية
    """
    
    def __init__(self):
        """
        تهيئة الاتصال بـ Twelve Data API
        """
        # Twelve Data Paid Plan
        self.api_key = config.TWELVE_DATA_API_KEY
        self.base_url = "https://api.twelvedata.com"
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """
        تحويل صيغة الرمز
        
        Args:
            symbol: رمز الزوج (مثل EUR/USD)
        
        Returns:
            الرمز بصيغة Twelve Data (مثل EUR/USD)
        """
        return symbol  # Twelve Data يقبل الصيغة مباشرة
    
    def get_historical_data(self, symbol: str, interval: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        جلب البيانات التاريخية الحقيقية
        
        Args:
            symbol: رمز الزوج (مثل EUR/USD)
            interval: الفريم الزمني (1min, 5min, 1h, 1day)
            limit: عدد الشموع
        
        Returns:
            DataFrame يحتوي على OHLC أو None في حالة الخطأ
        """
        try:
            # تحويل الفريم الزمني
            interval_map = {
                '1m': '1min',
                '5m': '5min',
                '15m': '15min',
                '1h': '1h',
                '1d': '1day'
            }
            
            twelve_interval = interval_map.get(interval, '5min')
            
            # بناء الطلب
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': symbol,
                'interval': twelve_interval,
                'outputsize': min(limit, 5000),  # الحد الأقصى
                'apikey': self.api_key,
                'format': 'JSON'
            }
            
            # إرسال الطلب
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  خطأ HTTP {response.status_code} لـ {symbol}")
                return None
            
            data = response.json()
            
            # التحقق من وجود خطأ
            if 'status' in data and data['status'] == 'error':
                print(f"⚠️  خطأ API: {data.get('message', 'Unknown error')}")
                return None
            
            # استخراج البيانات
            if 'values' not in data:
                print(f"⚠️  لا توجد بيانات لـ {symbol}")
                return None
            
            values = data['values']
            
            if not values:
                print(f"⚠️  بيانات فارغة لـ {symbol}")
                return None
            
            # بناء DataFrame
            df_data = []
            for item in reversed(values):  # عكس الترتيب (من القديم للجديد)
                try:
                    df_data.append({
                        'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M:%S'),
                        'open': float(item['open']),
                        'high': float(item['high']),
                        'low': float(item['low']),
                        'close': float(item['close']),
                        'volume': int(item.get('volume', 0))
                    })
                except (KeyError, ValueError) as e:
                    continue
            
            if not df_data:
                print(f"⚠️  فشل تحويل البيانات لـ {symbol}")
                return None
            
            df = pd.DataFrame(df_data)
            
            # أخذ آخر limit شمعة
            if len(df) > limit:
                df = df.tail(limit)
            
            df = df.reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الاتصال بـ API لـ {symbol}: {e}")
            return None
        except Exception as e:
            print(f"❌ خطأ في جلب البيانات لـ {symbol}: {e}")
            return None
    
    def get_data_with_indicators(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        """
        جلب البيانات مع المؤشرات المحسوبة
        
        Args:
            symbol: رمز الزوج
            interval: الفريم الزمني
        
        Returns:
            DataFrame مع المؤشرات أو None
        """
        df = self.get_historical_data(symbol, interval, config.CANDLES_LIMIT)
        
        if df is None or df.empty:
            return None
        
        # إضافة المؤشرات
        df = add_indicators(
            df,
            ema_fast=config.EMA_FAST,
            ema_slow=config.EMA_SLOW,
            rsi_period=config.RSI_PERIOD,
            atr_period=config.ATR_PERIOD
        )
        
        return df
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        جلب السعر الحالي
        
        Args:
            symbol: رمز الزوج
        
        Returns:
            السعر الحالي أو None
        """
        try:
            url = f"{self.base_url}/price"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'price' in data:
                    return float(data['price'])
            
            return None
        except Exception as e:
            print(f"❌ خطأ في جلب السعر لـ {symbol}: {e}")
            return None


# ملاحظة:
# ═══════════════════════════════════════════════════════════════════════════════
# هذا الملف يستخدم Twelve Data API المجاني!
# 
# المميزات:
# ✅ بيانات حقيقية من السوق
# ✅ مجاني - 800 طلب يومياً
# ✅ يدعم جميع أزواج الفوركس
# ✅ بيانات دقيقة (1min, 5min, إلخ)
#
# للحصول على مفتاح API مجاني:
# 1. اذهب إلى: https://twelvedata.com/pricing
# 2. اختر "Free Plan" (800 requests/day)
# 3. سجل وانسخ API key
# 4. استبدل "demo" في السطر 17 بالمفتاح الخاص بك
#
# ملاحظة: مفتاح "demo" يعمل للاختبار لكن مع حدود أكثر
# ═══════════════════════════════════════════════════════════════════════════════
