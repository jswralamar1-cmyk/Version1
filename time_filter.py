"""
فلتر وقت التداول
التحقق من جلسات لندن ونيويورك
"""

from datetime import datetime, time
import config


def is_trading_time() -> bool:
    """
    التحقق من أن الوقت الحالي ضمن جلسات التداول المسموحة
    
    Returns:
        True إذا كان الوقت ضمن جلسة لندن أو نيويورك
    """
    if not config.ENABLE_TIME_FILTER:
        return True
    
    # الوقت الحالي بتوقيت UTC
    now = datetime.utcnow().time()
    
    # جلسة لندن
    london_start = time.fromisoformat(config.LONDON_SESSION['start'])
    london_end = time.fromisoformat(config.LONDON_SESSION['end'])
    
    # جلسة نيويورك
    ny_start = time.fromisoformat(config.NY_SESSION['start'])
    ny_end = time.fromisoformat(config.NY_SESSION['end'])
    
    # التحقق من الجلسات
    in_london = london_start <= now <= london_end
    in_ny = ny_start <= now <= ny_end
    
    return in_london or in_ny


def get_current_session() -> str:
    """
    الحصول على اسم الجلسة الحالية
    
    Returns:
        اسم الجلسة أو "خارج أوقات التداول"
    """
    if not config.ENABLE_TIME_FILTER:
        return "جميع الأوقات"
    
    now = datetime.utcnow().time()
    
    london_start = time.fromisoformat(config.LONDON_SESSION['start'])
    london_end = time.fromisoformat(config.LONDON_SESSION['end'])
    
    ny_start = time.fromisoformat(config.NY_SESSION['start'])
    ny_end = time.fromisoformat(config.NY_SESSION['end'])
    
    if london_start <= now <= london_end:
        return "جلسة لندن"
    elif ny_start <= now <= ny_end:
        return "جلسة نيويورك"
    else:
        return "خارج أوقات التداول"


def get_next_session_time() -> str:
    """
    الحصول على وقت بداية الجلسة القادمة
    
    Returns:
        وقت الجلسة القادمة
    """
    if not config.ENABLE_TIME_FILTER:
        return "N/A"
    
    now = datetime.utcnow().time()
    
    london_start = time.fromisoformat(config.LONDON_SESSION['start'])
    ny_start = time.fromisoformat(config.NY_SESSION['start'])
    
    if now < london_start:
        return f"جلسة لندن تبدأ في {london_start.strftime('%H:%M')} UTC"
    elif now < ny_start:
        return f"جلسة نيويورك تبدأ في {ny_start.strftime('%H:%M')} UTC"
    else:
        return f"جلسة لندن تبدأ غداً في {london_start.strftime('%H:%M')} UTC"
