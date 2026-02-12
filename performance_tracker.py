"""
نظام تتبع الأداء والأرباح اليومية
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


class PerformanceTracker:
    """
    تتبع أداء الصفقات والأرباح اليومية
    """
    
    def __init__(self, initial_balance: float = 1000.0, data_file: str = "trades_history.json"):
        """
        تهيئة نظام التتبع
        
        Args:
            initial_balance: الرصيد الابتدائي ($)
            data_file: ملف حفظ البيانات
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.data_file = data_file
        self.trades: List[Dict] = []
        self.daily_stats: Dict = {}
        
        # تحميل البيانات المحفوظة
        self._load_data()
    
    def _load_data(self):
        """تحميل البيانات من الملف"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trades = data.get('trades', [])
                    self.current_balance = data.get('current_balance', self.initial_balance)
                    self.daily_stats = data.get('daily_stats', {})
            except Exception as e:
                print(f"⚠️  خطأ في تحميل البيانات: {e}")
    
    def _save_data(self):
        """حفظ البيانات إلى الملف"""
        try:
            data = {
                'trades': self.trades,
                'current_balance': self.current_balance,
                'daily_stats': self.daily_stats,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  خطأ في حفظ البيانات: {e}")
    
    def calculate_profit(self, entry_price: float, exit_price: float, 
                        direction: str, lot_size: float = 0.01) -> float:
        """
        حساب الربح/الخسارة للصفقة
        
        Args:
            entry_price: سعر الدخول
            exit_price: سعر الخروج
            direction: اتجاه الصفقة (BUY/SELL)
            lot_size: حجم العقد (0.01 = $1 لكل نقطة)
        
        Returns:
            الربح/الخسارة بالدولار
        """
        pip_value = 1.0  # $1 لكل نقطة (لحجم 0.01)
        
        if direction == "BUY":
            pips = (exit_price - entry_price) * 10000  # تحويل لنقاط
        else:  # SELL
            pips = (entry_price - exit_price) * 10000
        
        profit = pips * pip_value * lot_size * 100
        return round(profit, 2)
    
    def add_trade(self, symbol: str, direction: str, entry_price: float,
                  stop_loss: float, take_profit: float, timestamp: Optional[datetime] = None):
        """
        إضافة صفقة جديدة
        
        Args:
            symbol: رمز الزوج
            direction: اتجاه الصفقة (BUY/SELL)
            entry_price: سعر الدخول
            stop_loss: وقف الخسارة
            take_profit: هدف الربح
            timestamp: وقت الصفقة
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # حساب الربح/الخسارة المتوقعة
        profit_if_tp = self.calculate_profit(entry_price, take_profit, direction)
        loss_if_sl = self.calculate_profit(entry_price, stop_loss, direction)
        
        trade = {
            'id': len(self.trades) + 1,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': timestamp.isoformat(),
            'status': 'open',
            'profit_if_tp': profit_if_tp,
            'loss_if_sl': loss_if_sl,
            'actual_profit': None,
            'exit_price': None,
            'exit_time': None
        }
        
        self.trades.append(trade)
        self._save_data()
        
        return trade
    
    def close_trade(self, trade_id: int, exit_price: float, 
                    timestamp: Optional[datetime] = None) -> Optional[Dict]:
        """
        إغلاق صفقة
        
        Args:
            trade_id: رقم الصفقة
            exit_price: سعر الخروج
            timestamp: وقت الإغلاق
        
        Returns:
            معلومات الصفقة المغلقة
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # البحث عن الصفقة
        trade = None
        for t in self.trades:
            if t['id'] == trade_id and t['status'] == 'open':
                trade = t
                break
        
        if trade is None:
            return None
        
        # حساب الربح الفعلي
        actual_profit = self.calculate_profit(
            trade['entry_price'],
            exit_price,
            trade['direction']
        )
        
        # تحديث الصفقة
        trade['status'] = 'closed'
        trade['exit_price'] = exit_price
        trade['exit_time'] = timestamp.isoformat()
        trade['actual_profit'] = actual_profit
        
        # تحديث الرصيد
        self.current_balance += actual_profit
        
        # تحديث الإحصائيات اليومية
        date_key = timestamp.strftime('%Y-%m-%d')
        if date_key not in self.daily_stats:
            self.daily_stats[date_key] = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }
        
        stats = self.daily_stats[date_key]
        stats['total_trades'] += 1
        stats['total_profit'] += actual_profit
        
        if actual_profit > 0:
            stats['winning_trades'] += 1
        else:
            stats['losing_trades'] += 1
        
        stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
        
        self._save_data()
        
        return trade
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        الحصول على ملخص اليوم
        
        Args:
            date: التاريخ (افتراضي: اليوم)
        
        Returns:
            ملخص الأداء اليومي
        """
        if date is None:
            date = datetime.now()
        
        date_key = date.strftime('%Y-%m-%d')
        
        if date_key in self.daily_stats:
            stats = self.daily_stats[date_key].copy()
        else:
            stats = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }
        
        stats['date'] = date_key
        stats['current_balance'] = self.current_balance
        stats['initial_balance'] = self.initial_balance
        stats['total_profit_loss'] = self.current_balance - self.initial_balance
        stats['roi'] = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        return stats
    
    def get_open_trades(self) -> List[Dict]:
        """الحصول على الصفقات المفتوحة"""
        return [t for t in self.trades if t['status'] == 'open']
    
    def get_closed_trades_today(self) -> List[Dict]:
        """الحصول على الصفقات المغلقة اليوم"""
        today = datetime.now().strftime('%Y-%m-%d')
        closed_today = []
        
        for trade in self.trades:
            if trade['status'] == 'closed' and trade['exit_time']:
                exit_date = datetime.fromisoformat(trade['exit_time']).strftime('%Y-%m-%d')
                if exit_date == today:
                    closed_today.append(trade)
        
        return closed_today
    
    def format_daily_report(self) -> str:
        """
        تنسيق تقرير يومي
        
        Returns:
            نص التقرير
        """
        summary = self.get_daily_summary()
        
        report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **تقرير الأداء اليومي**
📅 التاريخ: {summary['date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **الرصيد:**
• الرصيد الحالي: ${summary['current_balance']:.2f}
• الرصيد الابتدائي: ${summary['initial_balance']:.2f}
• الربح/الخسارة الإجمالي: ${summary['total_profit_loss']:.2f}
• العائد على الاستثمار: {summary['roi']:.2f}%

📈 **الصفقات اليوم:**
• إجمالي الصفقات: {summary['total_trades']}
• صفقات رابحة: {summary['winning_trades']} ✅
• صفقات خاسرة: {summary['losing_trades']} ❌
• نسبة النجاح: {summary['win_rate']:.1f}%
• الربح اليومي: ${summary['total_profit']:.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report.strip()
