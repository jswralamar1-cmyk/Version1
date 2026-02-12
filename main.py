"""
البرنامج الرئيسي لأداة التداول
EMA + RSI Strategy Bot (Forex)
"""

import time
from datetime import datetime
import config
from forex_data_fetcher import ForexDataFetcher
from strategy import TradingStrategy
from telegram_notifier import TelegramNotifier
from time_filter import is_trading_time, get_current_session


def main():
    """
    الدالة الرئيسية
    """
    print("=" * 60)
    print("🚀 بدء تشغيل أداة التداول EMA + RSI (Forex)")
    print("=" * 60)
    
    # تهيئة المكونات
    data_fetcher = ForexDataFetcher()
    strategy = TradingStrategy()
    notifier = TelegramNotifier()
    
    # إرسال رسالة البدء
    notifier.send_startup_message()
    
    print(f"\n📊 أزواج الفوركس المراقبة: {', '.join(config.TRADING_PAIRS)}")
    print(f"⏰ التحديث كل: {config.UPDATE_INTERVAL} ثانية")
    print(f"🕐 فلتر الوقت: {'مفعّل' if config.ENABLE_TIME_FILTER else 'معطّل'}")
    print(f"🌍 المنطقة الزمنية: {config.TIMEZONE}")
    print("\n" + "=" * 60)
    print("✅ البوت يعمل الآن... (اضغط Ctrl+C للإيقاف)")
    print("=" * 60 + "\n")
    
    # الحلقة الرئيسية
    iteration = 0
    
    try:
        while True:
            iteration += 1
            current_time = datetime.now()
            
            # عرض معلومات الدورة
            print(f"\n{'─' * 60}")
            print(f"🔄 الدورة #{iteration} | {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📍 الجلسة الحالية: {get_current_session()}")
            print(f"{'─' * 60}")
            
            # التحقق من وقت التداول
            if not is_trading_time():
                print("⏸️  خارج أوقات التداول المحددة")
                time.sleep(config.UPDATE_INTERVAL)
                continue
            
            # تحليل كل زوج
            for symbol in config.TRADING_PAIRS:
                try:
                    print(f"\n🔍 تحليل {symbol}...")
                    
                    # جلب بيانات فريم 5 دقائق
                    df_5m = data_fetcher.get_data_with_indicators(
                        symbol,
                        config.TREND_TIMEFRAME
                    )
                    
                    if df_5m is None or df_5m.empty:
                        print(f"   ⚠️  فشل جلب بيانات 5 دقائق")
                        continue
                    
                    # جلب بيانات فريم 1 دقيقة
                    df_1m = data_fetcher.get_data_with_indicators(
                        symbol,
                        config.ENTRY_TIMEFRAME
                    )
                    
                    if df_1m is None or df_1m.empty:
                        print(f"   ⚠️  فشل جلب بيانات 1 دقيقة")
                        continue
                    
                    # تحليل الاستراتيجية
                    signal = strategy.analyze(df_5m, df_1m, symbol)
                    
                    if signal:
                        print(f"   🎯 إشارة جديدة: {signal['type']}")
                        print(f"   💰 السعر: {signal['price']:.5f}")
                        
                        # إرسال التنبيه
                        success = notifier.send_signal(signal)
                        
                        if success:
                            print(f"   ✅ تم إرسال التنبيه عبر Telegram")
                        else:
                            print(f"   ❌ فشل إرسال التنبيه")
                        
                        # عرض السبب في الكونسول
                        if config.DEBUG_MODE:
                            print(f"\n   السبب:\n{signal['reason']}\n")
                    else:
                        # عرض معلومات موجزة
                        last_5m = df_5m.iloc[-1]
                        last_1m = df_1m.iloc[-1]
                        
                        print(f"   📊 السعر: {last_1m['close']:.5f}")
                        print(f"   📈 EMA20: {last_1m['ema_fast']:.5f} | EMA50: {last_1m['ema_slow']:.5f}")
                        print(f"   📉 RSI: {last_1m['rsi']:.1f}")
                        print(f"   📏 ATR: {last_1m['atr']:.6f}")
                        print(f"   ➡️  لا توجد إشارة")
                
                except Exception as e:
                    error_msg = f"خطأ في تحليل {symbol}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    
                    if config.DEBUG_MODE:
                        import traceback
                        traceback.print_exc()
                    
                    # إرسال تنبيه بالخطأ
                    notifier.send_error_message(error_msg)
            
            # الانتظار قبل الدورة التالية
            print(f"\n⏳ الانتظار {config.UPDATE_INTERVAL} ثانية...")
            time.sleep(config.UPDATE_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 تم إيقاف البوت بواسطة المستخدم")
        print("=" * 60)
        
        # إرسال رسالة الإيقاف
        notifier.send_message(
            "🛑 <b>تم إيقاف البوت</b>\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    except Exception as e:
        error_msg = f"خطأ فادح: {str(e)}"
        print(f"\n❌ {error_msg}")
        
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        
        # إرسال تنبيه بالخطأ
        notifier.send_error_message(error_msg)


if __name__ == "__main__":
    main()
