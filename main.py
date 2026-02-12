"""
الملف الرئيسي لأداة التداول EMA + RSI (Forex)
مع نظام تتبع الأداء والأرباح
"""

import time
from datetime import datetime
import config
from forex_data_fetcher import ForexDataFetcher
from strategy import TradingStrategy
from telegram_notifier import TelegramNotifier
from time_filter import is_trading_time
from performance_tracker import PerformanceTracker


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
        config.TELEGRAM_BOT_TOKEN,
        config.TELEGRAM_CHAT_ID
    )
    
    # تهيئة نظام تتبع الأداء
    tracker = None
    if config.ENABLE_PERFORMANCE_TRACKING:
        tracker = PerformanceTracker(
            initial_balance=config.INITIAL_BALANCE
        )
        print(f"💰 نظام تتبع الأداء: مفعّل (رصيد: ${config.INITIAL_BALANCE})")
    
    # إرسال رسالة البدء
    startup_message = f"""
🚀 **البوت بدأ العمل** 🚀

⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 الأزواج المراقبة: {len(config.TRADING_PAIRS)}
🔄 التحديث كل: {config.UPDATE_INTERVAL} ثانية
{'💰 تتبع الأداء: مفعّل' if config.ENABLE_PERFORMANCE_TRACKING else ''}

✅ **جاهز لمراقبة السوق** ✅
"""
    notifier.send_message(startup_message)
    
    print(f"📊 أزواج الفوركس المراقبة: {len(config.TRADING_PAIRS)}")
    print(f"🔄 التحديث كل: {config.UPDATE_INTERVAL} ثانية")
    print("✅ جاهز لمراقبة السوق...\n")
    
    # متغيرات التتبع
    last_signals = {}  # لتتبع آخر إشارة لكل زوج
    last_daily_report = None  # آخر تقرير يومي
    
    # الحلقة الرئيسية
    while True:
        try:
            current_time = datetime.now()
            
            # التحقق من وقت التداول
            if config.ENABLE_TIME_FILTER and not is_trading_time(current_time):
                if config.DEBUG_MODE:
                    print(f"⏸️  خارج أوقات التداول: {current_time.strftime('%H:%M')}")
                time.sleep(config.UPDATE_INTERVAL)
                continue
            
            print(f"\n{'='*60}")
            print(f"🔍 فحص السوق: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # مراقبة كل زوج
            for symbol in config.TRADING_PAIRS:
                try:
                    # جلب بيانات الاتجاه (5 دقائق)
                    df_trend = data_fetcher.get_data_with_indicators(
                        symbol,
                        config.TREND_TIMEFRAME
                    )
                    
                    if df_trend is None or df_trend.empty:
                        print(f"⚠️  {symbol}: لا توجد بيانات")
                        continue
                    
                    # جلب بيانات الدخول (1 دقيقة)
                    df_entry = data_fetcher.get_data_with_indicators(
                        symbol,
                        config.ENTRY_TIMEFRAME
                    )
                    
                    if df_entry is None or df_entry.empty:
                        continue
                    
                    # تحليل الاستراتيجية
                    signal = strategy.analyze(df_trend, df_entry, symbol)
                    
                    if signal:
                        signal_key = f"{symbol}_{signal['type']}"
                        
                        # التحقق من عدم تكرار الإشارة
                        if signal_key in last_signals:
                            time_diff = (current_time - last_signals[signal_key]).total_seconds() / 60
                            if time_diff < config.SIGNAL_COOLDOWN_CANDLES:
                                continue
                        
                        # تحديث آخر إشارة
                        last_signals[signal_key] = current_time
                        
                        # إرسال التنبيه
                        if signal['type'] == 'ready':
                            if config.ENABLE_READY_ALERT:
                                notifier.send_ready_alert(signal)
                                print(f"🔔 {symbol}: تنبيه استعداد {signal['direction']}")
                        else:  # entry
                            notifier.send_entry_alert(signal)
                            print(f"🚀 {symbol}: إشارة دخول {signal['direction']}")
                            
                            # إضافة الصفقة لنظام التتبع
                            if tracker and config.ENABLE_PERFORMANCE_TRACKING:
                                trade = tracker.add_trade(
                                    symbol=symbol,
                                    direction=signal['direction'],
                                    entry_price=signal['price'],
                                    stop_loss=signal['stop_loss'],
                                    take_profit=signal['take_profit'],
                                    timestamp=current_time
                                )
                                print(f"💰 تم إضافة الصفقة #{trade['id']} للتتبع")
                    
                    time.sleep(0.5)  # تأخير صغير بين الأزواج
                    
                except Exception as e:
                    print(f"❌ خطأ في معالجة {symbol}: {e}")
                    continue
            
            # إرسال التقرير اليومي
            if (tracker and config.ENABLE_PERFORMANCE_TRACKING and 
                config.SEND_DAILY_REPORT):
                
                current_date = current_time.strftime('%Y-%m-%d')
                report_time = config.DAILY_REPORT_TIME
                current_hour_min = current_time.strftime('%H:%M')
                
                # إرسال التقرير مرة واحدة يومياً
                if (current_hour_min == report_time and 
                    last_daily_report != current_date):
                    
                    report = tracker.format_daily_report()
                    notifier.send_message(report)
                    last_daily_report = current_date
                    print(f"📊 تم إرسال التقرير اليومي")
            
            print(f"\n⏳ انتظار {config.UPDATE_INTERVAL} ثانية...")
            time.sleep(config.UPDATE_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 إيقاف البوت...")
            
            # إرسال رسالة الإيقاف
            if tracker and config.ENABLE_PERFORMANCE_TRACKING:
                final_report = tracker.format_daily_report()
                notifier.send_message(f"🛑 **تم إيقاف البوت**\n\n{final_report}")
            else:
                notifier.send_message("🛑 تم إيقاف البوت")
            
            break
            
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            time.sleep(config.UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
