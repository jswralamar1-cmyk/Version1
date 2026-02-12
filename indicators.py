"""
حساب المؤشرات الفنية
EMA, RSI, ATR
"""

import pandas as pd
import numpy as np


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    حساب المتوسط المتحرك الأسي (EMA)
    
    Args:
        data: سلسلة الأسعار
        period: الفترة الزمنية
    
    Returns:
        سلسلة EMA
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    حساب مؤشر القوة النسبية (RSI)
    
    Args:
        data: سلسلة الأسعار
        period: الفترة الزمنية (افتراضي 14)
    
    Returns:
        سلسلة RSI
    """
    # حساب التغيرات
    delta = data.diff()
    
    # فصل المكاسب والخسائر
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # حساب المتوسطات
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()
    
    # حساب RS و RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    حساب متوسط المدى الحقيقي (ATR)
    
    Args:
        high: سلسلة الأسعار العليا
        low: سلسلة الأسعار الدنيا
        close: سلسلة أسعار الإغلاق
        period: الفترة الزمنية (افتراضي 14)
    
    Returns:
        سلسلة ATR
    """
    # حساب True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # حساب ATR
    atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr


def add_indicators(df: pd.DataFrame, ema_fast: int = 20, ema_slow: int = 50, 
                   rsi_period: int = 14, atr_period: int = 14) -> pd.DataFrame:
    """
    إضافة جميع المؤشرات إلى DataFrame
    
    Args:
        df: DataFrame يحتوي على OHLCV
        ema_fast: فترة EMA السريع
        ema_slow: فترة EMA البطيء
        rsi_period: فترة RSI
        atr_period: فترة ATR
    
    Returns:
        DataFrame مع المؤشرات المضافة
    """
    # نسخ DataFrame لتجنب التعديل على الأصل
    df = df.copy()
    
    # حساب EMA
    df['ema_fast'] = calculate_ema(df['close'], ema_fast)
    df['ema_slow'] = calculate_ema(df['close'], ema_slow)
    
    # حساب RSI
    df['rsi'] = calculate_rsi(df['close'], rsi_period)
    
    # حساب ATR
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'], atr_period)
    
    return df


def is_price_near_ema(price: float, ema: float, proximity_points: float) -> bool:
    """
    التحقق من قرب السعر من EMA
    
    Args:
        price: السعر الحالي
        ema: قيمة EMA
        proximity_points: المسافة المسموحة بالنقاط
    
    Returns:
        True إذا كان السعر قريب من EMA
    """
    distance = abs(price - ema)
    return distance <= proximity_points


def get_trend_direction(df: pd.DataFrame) -> str:
    """
    تحديد اتجاه السوق بناءً على EMA
    
    Args:
        df: DataFrame مع المؤشرات
    
    Returns:
        'bullish' أو 'bearish' أو 'neutral'
    """
    if df.empty or len(df) < 2:
        return 'neutral'
    
    last_row = df.iloc[-1]
    
    # شروط الاتجاه الصاعد
    if last_row['ema_fast'] > last_row['ema_slow'] and last_row['close'] > last_row['ema_slow']:
        return 'bullish'
    
    # شروط الاتجاه الهابط
    elif last_row['ema_fast'] < last_row['ema_slow'] and last_row['close'] < last_row['ema_slow']:
        return 'bearish'
    
    return 'neutral'


def check_rsi_cross(current_rsi: float, previous_rsi: float, level: float, direction: str) -> bool:
    """
    التحقق من عبور RSI لمستوى معين
    
    Args:
        current_rsi: قيمة RSI الحالية
        previous_rsi: قيمة RSI السابقة
        level: المستوى المراد عبوره
        direction: 'above' للعبور فوق، 'below' للعبور تحت
    
    Returns:
        True إذا حدث العبور
    """
    if direction == 'above':
        return previous_rsi <= level < current_rsi
    elif direction == 'below':
        return previous_rsi >= level > current_rsi
    
    return False


def check_candle_close(current_close: float, ema: float, direction: str) -> bool:
    """
    التحقق من إغلاق الشمعة فوق/تحت EMA
    
    Args:
        current_close: سعر الإغلاق الحالي
        ema: قيمة EMA
        direction: 'above' للإغلاق فوق، 'below' للإغلاق تحت
    
    Returns:
        True إذا تحقق الشرط
    """
    if direction == 'above':
        return current_close > ema
    elif direction == 'below':
        return current_close < ema
    
    return False
