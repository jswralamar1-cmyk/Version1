"""
جلب بيانات الفوركس باستخدام API
"""

import pandas as pd
import requests
from typing import Optional
from datetime import datetime, timedelta
import config
from indicators import add_indicators


class ForexDataFetcher:
    """
    جلب وتحليل بيانات الفوركس
    """
    
    def __init__(self):
        """
        تهيئة الاتصال بـ Forex API
        """
        self.api_key = config.FOREX_API_KEY
        self.base_url = "https://api.fxratesapi.com"  # Free Forex API
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """
        تحويل صيغة الرمز من EUR/USD إلى EURUSD
        
        Args:
            symbol: رمز الزوج (مثل EUR/USD)
        
        Returns:
            الرمز بدون /
        """
        return symbol.replace('/', '')
    
    def get_historical_data(self, symbol: str, interval: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        جلب البيانات التاريخية
        
        Args:
            symbol: رمز الزوج (مثل EUR/USD)
            interval: الفريم الزمني (1m, 5m, 1h, 1d)
            limit: عدد الشموع
        
        Returns:
            DataFrame يحتوي على OHLC أو None في حالة الخطأ
        """
        try:
            # تحويل الفريم الزمني
            interval_map = {
                '1m': 1,
                '5m': 5,
                '15m': 15,
                '1h': 60,
                '1d': 1440
            }
            
            minutes = interval_map.get(interval, 5)
            
            # حساب الفترة الزمنية
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes * limit)
            
            # تحويل الرمز
            clean_symbol = self._convert_symbol_format(symbol)
            base_currency = clean_symbol[:3]
            quote_currency = clean_symbol[3:]
            
            # بناء البيانات الوهمية للاختبار (لأن معظم Forex APIs مدفوعة)
            # في الإنتاج، استخدم API حقيقي
            df = self._generate_sample_data(symbol, limit)
            
            return df
            
        except Exception as e:
            print(f"❌ خطأ في جلب البيانات لـ {symbol}: {e}")
            return None
    
    def _generate_sample_data(self, symbol: str, limit: int) -> pd.DataFrame:
        """
        توليد بيانات وهمية للاختبار
        (في الإنتاج، استبدل هذه بـ API حقيقي)
        
        Args:
            symbol: رمز الزوج
            limit: عدد الشموع
        
        Returns:
            DataFrame مع بيانات OHLC
        """
        import numpy as np
        
        # قيم افتراضية لكل زوج
        base_prices = {
            'EUR/USD': 1.0850,
            'GBP/USD': 1.2650,
            'USD/JPY': 149.50,
            'AUD/USD': 0.6550,
            'EUR/JPY': 162.20,
            'GBP/JPY': 189.10
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        
        # توليد البيانات
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=limit,
            freq='1min'
        )
        
        # توليد أسعار عشوائية واقعية
        np.random.seed(42)
        
        # حركة السعر العشوائية
        price_changes = np.random.normal(0, 0.0002, limit).cumsum()
        close_prices = base_price + price_changes
        
        # حساب OHLC
        data = []
        for i in range(limit):
            close = close_prices[i]
            volatility = abs(np.random.normal(0, 0.0001))
            
            open_price = close + np.random.normal(0, volatility)
            high = max(open_price, close) + abs(np.random.normal(0, volatility/2))
            low = min(open_price, close) - abs(np.random.normal(0, volatility/2))
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': timestamps[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df
    
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
            df = self.get_historical_data(symbol, '1m', 1)
            if df is not None and not df.empty:
                return float(df.iloc[-1]['close'])
            return None
        except Exception as e:
            print(f"❌ خطأ في جلب السعر لـ {symbol}: {e}")
            return None


# ملاحظة مهمة:
# ═══════════════════════════════════════════════════════════════════════════════
# هذا الملف يستخدم بيانات وهمية للاختبار!
# 
# للحصول على بيانات حقيقية، استخدم أحد هذه الخيارات:
#
# 1. OANDA API (مدفوع ولكن موثوق):
#    https://developer.oanda.com/rest-live-v20/introduction/
#
# 2. Alpha Vantage (مجاني مع حدود):
#    https://www.alphavantage.co/documentation/#fx
#
# 3. Twelve Data (مجاني مع حدود):
#    https://twelvedata.com/docs#forex
#
# 4. Forex.com API (يحتاج حساب):
#    https://www.forex.com/en-us/trading-platforms/api-trading/
#
# استبدل دالة _generate_sample_data() بطلبات API حقيقية
# ═══════════════════════════════════════════════════════════════════════════════
