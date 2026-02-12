"""
منطق استراتيجية التداول
EMA + RSI Strategy
"""

import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime
import config
from indicators import (
    get_trend_direction,
    is_price_near_ema,
    check_rsi_cross,
    check_candle_close
)


class TradingStrategy:
    """
    استراتيجية التداول الرئيسية
    """
    
    def __init__(self):
        self.last_signals = {}  # تتبع آخر إشارة لكل زوج
        self.signal_cooldown = {}  # منع تكرار الإشارات
    
    def analyze_trend(self, df_5m: pd.DataFrame, symbol: str) -> Dict:
        """
        تحليل الاتجاه على فريم 5 دقائق
        
        Args:
            df_5m: بيانات فريم 5 دقائق مع المؤشرات
            symbol: رمز الزوج
        
        Returns:
            قاموس يحتوي على معلومات الاتجاه
        """
        if df_5m.empty or len(df_5m) < 2:
            return {'direction': 'neutral', 'valid': False}
        
        trend = get_trend_direction(df_5m)
        last_row = df_5m.iloc[-1]
        
        return {
            'direction': trend,
            'valid': trend != 'neutral',
            'ema_fast': last_row['ema_fast'],
            'ema_slow': last_row['ema_slow'],
            'close': last_row['close']
        }
    
    def check_buy_conditions(self, df_1m: pd.DataFrame, trend_info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        فحص شروط إشارة الشراء على فريم 1 دقيقة
        
        Args:
            df_1m: بيانات فريم 1 دقيقة مع المؤشرات
            trend_info: معلومات الاتجاه من فريم 5 دقائق
        
        Returns:
            (نوع الإشارة, السبب) أو (None, None)
        """
        if df_1m.empty or len(df_1m) < 2:
            return None, None
        
        # التحقق من الاتجاه الصاعد
        if trend_info['direction'] != 'bullish':
            return None, None
        
        current = df_1m.iloc[-1]
        previous = df_1m.iloc[-2]
        
        # الشرط 1: السعر قريب من EMA20
        price_near_ema = is_price_near_ema(
            current['close'],
            current['ema_fast'],
            config.EMA_PROXIMITY_POINTS
        )
        
        # الشرط 2: RSI في المنطقة الصحيحة (40-50)
        rsi_in_zone = config.RSI_BUY_ZONE[0] <= current['rsi'] <= config.RSI_BUY_ZONE[1]
        
        # الشرط 3: RSI يعبر فوق 50
        rsi_crossed = check_rsi_cross(
            current['rsi'],
            previous['rsi'],
            config.RSI_LEVEL,
            'above'
        )
        
        # الشرط 4: الشمعة تغلق فوق EMA20
        candle_closed_above = check_candle_close(
            current['close'],
            current['ema_fast'],
            'above'
        )
        
        # فحص ATR
        atr_valid = current['atr'] >= config.ATR_MIN_VALUE
        
        if not atr_valid:
            return None, None
        
        # تنبيه الاستعداد
        if price_near_ema and rsi_in_zone and rsi_crossed and config.ENABLE_READY_ALERT:
            reason = (
                f"🟡 استعداد للشراء\n"
                f"• الاتجاه: صاعد ✅\n"
                f"• السعر قرب EMA20: {current['close']:.5f} ≈ {current['ema_fast']:.5f} ✅\n"
                f"• RSI عبر فوق 50: {previous['rsi']:.1f} → {current['rsi']:.1f} ✅\n"
                f"• انتظر إغلاق الشمعة فوق EMA20"
            )
            return 'ready_buy', reason
        
        # تنبيه الدخول
        if price_near_ema and rsi_crossed and candle_closed_above:
            reason = (
                f"🟢 دخول شراء\n"
                f"• الاتجاه: صاعد ✅\n"
                f"• السعر: {current['close']:.5f}\n"
                f"• EMA20: {current['ema_fast']:.5f}\n"
                f"• RSI: {current['rsi']:.1f}\n"
                f"• الشمعة أغلقت فوق EMA20 ✅\n"
                f"• وقف الخسارة: {current['close'] - config.STOP_LOSS_POINTS * 0.0001:.5f}\n"
                f"• هدف الربح: {current['close'] + config.TAKE_PROFIT_POINTS * 0.0001:.5f}"
            )
            return 'entry_buy', reason
        
        return None, None
    
    def check_sell_conditions(self, df_1m: pd.DataFrame, trend_info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        فحص شروط إشارة البيع على فريم 1 دقيقة
        
        Args:
            df_1m: بيانات فريم 1 دقيقة مع المؤشرات
            trend_info: معلومات الاتجاه من فريم 5 دقائق
        
        Returns:
            (نوع الإشارة, السبب) أو (None, None)
        """
        if df_1m.empty or len(df_1m) < 2:
            return None, None
        
        # التحقق من الاتجاه الهابط
        if trend_info['direction'] != 'bearish':
            return None, None
        
        current = df_1m.iloc[-1]
        previous = df_1m.iloc[-2]
        
        # الشرط 1: السعر قريب من EMA20
        price_near_ema = is_price_near_ema(
            current['close'],
            current['ema_fast'],
            config.EMA_PROXIMITY_POINTS
        )
        
        # الشرط 2: RSI في المنطقة الصحيحة (50-60)
        rsi_in_zone = config.RSI_SELL_ZONE[0] <= current['rsi'] <= config.RSI_SELL_ZONE[1]
        
        # الشرط 3: RSI يعبر تحت 50
        rsi_crossed = check_rsi_cross(
            current['rsi'],
            previous['rsi'],
            config.RSI_LEVEL,
            'below'
        )
        
        # الشرط 4: الشمعة تغلق تحت EMA20
        candle_closed_below = check_candle_close(
            current['close'],
            current['ema_fast'],
            'below'
        )
        
        # فحص ATR
        atr_valid = current['atr'] >= config.ATR_MIN_VALUE
        
        if not atr_valid:
            return None, None
        
        # تنبيه الاستعداد
        if price_near_ema and rsi_in_zone and rsi_crossed and config.ENABLE_READY_ALERT:
            reason = (
                f"🟡 استعداد للبيع\n"
                f"• الاتجاه: هابط ✅\n"
                f"• السعر قرب EMA20: {current['close']:.5f} ≈ {current['ema_fast']:.5f} ✅\n"
                f"• RSI عبر تحت 50: {previous['rsi']:.1f} → {current['rsi']:.1f} ✅\n"
                f"• انتظر إغلاق الشمعة تحت EMA20"
            )
            return 'ready_sell', reason
        
        # تنبيه الدخول
        if price_near_ema and rsi_crossed and candle_closed_below:
            reason = (
                f"🔴 دخول بيع\n"
                f"• الاتجاه: هابط ✅\n"
                f"• السعر: {current['close']:.5f}\n"
                f"• EMA20: {current['ema_fast']:.5f}\n"
                f"• RSI: {current['rsi']:.1f}\n"
                f"• الشمعة أغلقت تحت EMA20 ✅\n"
                f"• وقف الخسارة: {current['close'] + config.STOP_LOSS_POINTS * 0.0001:.5f}\n"
                f"• هدف الربح: {current['close'] - config.TAKE_PROFIT_POINTS * 0.0001:.5f}"
            )
            return 'entry_sell', reason
        
        return None, None
    
    def is_in_cooldown(self, symbol: str, current_time: datetime) -> bool:
        """
        التحقق من فترة التهدئة لمنع تكرار الإشارات
        
        Args:
            symbol: رمز الزوج
            current_time: الوقت الحالي
        
        Returns:
            True إذا كان في فترة التهدئة
        """
        if symbol not in self.signal_cooldown:
            return False
        
        last_signal_time = self.signal_cooldown[symbol]
        cooldown_minutes = config.SIGNAL_COOLDOWN_CANDLES  # عدد الشموع = عدد الدقائق
        
        time_diff = (current_time - last_signal_time).total_seconds() / 60
        
        return time_diff < cooldown_minutes
    
    def update_cooldown(self, symbol: str, current_time: datetime):
        """
        تحديث وقت آخر إشارة
        
        Args:
            symbol: رمز الزوج
            current_time: الوقت الحالي
        """
        self.signal_cooldown[symbol] = current_time
    
    def analyze(self, df_5m: pd.DataFrame, df_1m: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """
        التحليل الكامل للزوج
        
        Args:
            df_5m: بيانات فريم 5 دقائق
            df_1m: بيانات فريم 1 دقيقة
            symbol: رمز الزوج
        
        Returns:
            قاموس يحتوي على الإشارة أو None
        """
        current_time = datetime.now()
        
        # فحص فترة التهدئة
        if self.is_in_cooldown(symbol, current_time):
            return None
        
        # تحليل الاتجاه
        trend_info = self.analyze_trend(df_5m, symbol)
        
        if not trend_info['valid']:
            return None
        
        # فحص شروط الشراء
        signal_type, reason = self.check_buy_conditions(df_1m, trend_info)
        
        # إذا لم توجد إشارة شراء، فحص شروط البيع
        if signal_type is None:
            signal_type, reason = self.check_sell_conditions(df_1m, trend_info)
        
        # إذا وجدت إشارة
        if signal_type and reason:
            # تحديث فترة التهدئة فقط لإشارات الدخول
            if 'entry' in signal_type:
                self.update_cooldown(symbol, current_time)
            
            return {
                'symbol': symbol,
                'type': signal_type,
                'reason': reason,
                'timestamp': current_time,
                'price': df_1m.iloc[-1]['close']
            }
        
        return None
