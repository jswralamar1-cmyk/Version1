"""
جلب بيانات الأسعار من Twelve Data API
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import config


def fetch_forex_data_twelve(pair, timeframe="5min", outputsize=100):
    """
    جلب بيانات الفوركس من Twelve Data
    
    Args:
        pair: زوج العملات (مثل: EUR/USD)
        timeframe: الإطار الزمني (1min, 5min, 15min, 1h, إلخ)
        outputsize: عدد الشموع المطلوبة
    
    Returns:
        DataFrame: بيانات OHLCV
    """
    # تحويل صيغة الزوج من EURUSD إلى EUR/USD
    if len(pair) == 6:
        pair_formatted = f"{pair[:3]}/{pair[3:]}"
    else:
        pair_formatted = pair
    
    # بناء URL
    url = "https://api.twelvedata.com/time_series"
    
    params = {
        "symbol": pair_formatted,
        "interval": timeframe,
        "outputsize": outputsize,
        "apikey": config.TWELVE_DATA_API_KEY,
        "format": "JSON"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # التحقق من وجود بيانات
        if "values" not in data or not data["values"]:
            if "message" in data:
                print(f"⚠️  خطأ API لـ {pair}: {data['message']}")
            return None
        
        # تحويل إلى DataFrame
        df = pd.DataFrame(data["values"])
        
        # إعادة تسمية الأعمدة
        df = df.rename(columns={
            "datetime": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        })
        
        # تحويل الأنواع
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # تحويل الوقت
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # ترتيب حسب الوقت (من القديم للجديد)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # إضافة اسم الزوج
        df['pair'] = pair
        
        return df[['timestamp', 'pair', 'open', 'high', 'low', 'close', 'volume']]
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  خطأ في جلب البيانات لـ {pair}: {e}")
        return None
    except Exception as e:
        print(f"⚠️  خطأ غير متوقع لـ {pair}: {e}")
        return None


def get_latest_candles_twelve(pair, timeframe="5min", count=100):
    """
    جلب آخر N شمعة من Twelve Data
    
    Args:
        pair: زوج العملات
        timeframe: الإطار الزمني
        count: عدد الشموع المطلوبة
    
    Returns:
        DataFrame: آخر N شمعة
    """
    df = fetch_forex_data_twelve(pair, timeframe=timeframe, outputsize=count)
    
    if df is None or len(df) == 0:
        return None
    
    # إرجاع آخر N شمعة
    return df.tail(count).reset_index(drop=True)
