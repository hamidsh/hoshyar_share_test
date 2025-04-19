"""
سیستم مدیریت بودجه Twitter API برای کنترل هزینه‌ها و نظارت بر مصرف اعتبار

این ماژول امکان تعیین و پیگیری بودجه روزانه برای استفاده از TwitterAPI.io را
فراهم می‌کند. با استفاده از این سیستم، می‌توان از مصرف بیش از حد اعتبار جلوگیری کرد.
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TwitterAPIBudget:
    """مدیریت بودجه TwitterAPI برای جلوگیری از مصرف بیش از حد"""

    # نرخ‌های اعتبار (مطابق با قیمت‌گذاری TwitterAPI.io)
    CREDITS = {
        'tweet': 15,  # 15 اعتبار برای هر 1000 توییت ($0.15/1000)
        'user': 18,  # 18 اعتبار برای هر 1000 کاربر ($0.18/1000)
        'follower': 15,  # 15 اعتبار برای هر 1000 دنبال‌کننده ($0.15/1000)
        'request': 15  # حداقل اعتبار برای هر درخواست ($0.00015)
    }

    # نرخ تبدیل دلار به اعتبار
    USD_TO_CREDITS = 100000  # 1 دلار = 100,000 اعتبار

    def __init__(self,
                 daily_budget_usd: float = 0.5,
                 reset_hour: int = 0,
                 report_file: Optional[str] = None):
        """
        مقداردهی اولیه سیستم مدیریت بودجه

        Args:
            daily_budget_usd: بودجه روزانه به دلار
            reset_hour: ساعت بازنشانی بودجه (0-23)
            report_file: مسیر فایل گزارش مصرف (اختیاری)
        """
        self.daily_budget = daily_budget_usd * self.USD_TO_CREDITS
        self.reset_hour = reset_hour
        self.spent_today = 0
        self.total_spent = 0
        self.request_count = 0
        self.report_file = report_file

        # تنظیم زمان آخرین بازنشانی
        self.last_reset = datetime.now().replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        if datetime.now().hour < reset_hour:
            self.last_reset -= timedelta(days=1)

        self.lock = threading.Lock()
        self.usage_history = []

        logger.info(f"سیستم مدیریت بودجه راه‌اندازی شد. بودجه روزانه: ${daily_budget_usd:.2f}")

    def calculate_cost(self, resource_type: str = 'request', count: int = 1) -> float:
        """
        محاسبه هزینه یک درخواست بر اساس نوع و تعداد منبع

        Args:
            resource_type: نوع منبع ('tweet', 'user', 'follower', 'request')
            count: تعداد منابع

        Returns:
            هزینه به اعتبار
        """
        cost_per_1000 = self.CREDITS.get(resource_type, self.CREDITS['request'])
        resource_cost = (count * cost_per_1000) / 1000
        # هر درخواست حداقل 15 اعتبار هزینه دارد
        return max(resource_cost, self.CREDITS['request'])

    def check_budget(self, resource_type: str = 'request', count: int = 1) -> bool:
        """
        بررسی آیا بودجه کافی برای این درخواست وجود دارد یا خیر

        Args:
            resource_type: نوع منبع
            count: تعداد منابع

        Returns:
            True اگر بودجه کافی وجود دارد، False در غیر این صورت
        """
        with self.lock:
            self._reset_if_needed()
            cost = self.calculate_cost(resource_type, count)
            has_budget = self.spent_today + cost <= self.daily_budget

            if not has_budget:
                logger.warning(
                    f"بودجه ناکافی برای درخواست {resource_type} (تعداد: {count}). "
                    f"هزینه: {cost} اعتبار. مانده: {self.daily_budget - self.spent_today} اعتبار."
                )

            return has_budget

    def record_usage(self, endpoint: str, resource_type: str = 'request', count: int = 1) -> float:
        """
        ثبت استفاده از API و بروزرسانی هزینه

        Args:
            endpoint: آدرس endpoint مورد استفاده
            resource_type: نوع منبع
            count: تعداد منابع

        Returns:
            هزینه به اعتبار
        """
        with self.lock:
            self._reset_if_needed()
            cost = self.calculate_cost(resource_type, count)
            self.spent_today += cost
            self.total_spent += cost
            self.request_count += 1

            # ثبت در تاریخچه
            usage_info = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'type': resource_type,
                'count': count,
                'credits': cost,
                'usd': cost / self.USD_TO_CREDITS
            }
            self.usage_history.append(usage_info)

            # ثبت در فایل گزارش
            if self.report_file:
                try:
                    with open(self.report_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(usage_info) + "\n")
                except Exception as e:
                    logger.error(f"خطا در ثبت گزارش مصرف: {str(e)}")

            logger.debug(
                f"هزینه درخواست {endpoint} ({resource_type}, تعداد: {count}): "
                f"{cost} اعتبار (${cost / self.USD_TO_CREDITS:.6f})"
            )

            return cost

    def get_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت فعلی بودجه

        Returns:
            دیکشنری حاوی اطلاعات وضعیت بودجه
        """
        with self.lock:
            self._reset_if_needed()
            return {
                'daily_budget_credits': self.daily_budget,
                'daily_budget_usd': self.daily_budget / self.USD_TO_CREDITS,
                'spent_today_credits': self.spent_today,
                'spent_today_usd': self.spent_today / self.USD_TO_CREDITS,
                'remaining_credits': self.daily_budget - self.spent_today,
                'remaining_usd': (self.daily_budget - self.spent_today) / self.USD_TO_CREDITS,
                'percentage_used': (self.spent_today / self.daily_budget) * 100 if self.daily_budget > 0 else 0,
                'request_count': self.request_count,
                'last_reset': self.last_reset.isoformat(),
                'next_reset': (self.last_reset + timedelta(days=1)).isoformat()
            }

    def _reset_if_needed(self) -> bool:
        """
        در صورت نیاز، بودجه روزانه را بازنشانی می‌کند

        Returns:
            True اگر بازنشانی انجام شد، False در غیر این صورت
        """
        now = datetime.now()
        next_reset = self.last_reset + timedelta(days=1)
        if now >= next_reset:
            old_spent = self.spent_today
            self.spent_today = 0
            self.last_reset = now.replace(hour=self.reset_hour, minute=0, second=0, microsecond=0)

            logger.info(
                f"بودجه بازنشانی شد. مصرف دیروز: {old_spent} اعتبار "
                f"(${old_spent / self.USD_TO_CREDITS:.2f})"
            )
            return True
        return False

    def generate_usage_report(self, days: int = 7) -> Dict[str, Any]:
        """
        تولید گزارش مصرف API

        Args:
            days: تعداد روزهای گذشته برای گزارش

        Returns:
            دیکشنری حاوی گزارش مصرف
        """
        # فیلتر تاریخچه بر اساس تعداد روز
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_history = [
            entry for entry in self.usage_history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
        ]

        # گروه‌بندی بر اساس روز
        daily_usage = {}
        for entry in filtered_history:
            day = entry['timestamp'].split('T')[0]  # YYYY-MM-DD
            if day not in daily_usage:
                daily_usage[day] = {'credits': 0, 'usd': 0, 'requests': 0}

            daily_usage[day]['credits'] += entry['credits']
            daily_usage[day]['usd'] += entry['usd']
            daily_usage[day]['requests'] += 1

        # گروه‌بندی بر اساس نوع منبع
        resource_usage = {}
        for entry in filtered_history:
            res_type = entry['type']
            if res_type not in resource_usage:
                resource_usage[res_type] = {'credits': 0, 'usd': 0, 'count': 0}

            resource_usage[res_type]['credits'] += entry['credits']
            resource_usage[res_type]['usd'] += entry['usd']
            resource_usage[res_type]['count'] += entry['count']

        # گروه‌بندی بر اساس endpoint
        endpoint_usage = {}
        for entry in filtered_history:
            endpoint = entry['endpoint']
            if endpoint not in endpoint_usage:
                endpoint_usage[endpoint] = {'credits': 0, 'usd': 0, 'requests': 0}

            endpoint_usage[endpoint]['credits'] += entry['credits']
            endpoint_usage[endpoint]['usd'] += entry['usd']
            endpoint_usage[endpoint]['requests'] += 1

        # محاسبه مجموع
        total_credits = sum(entry['credits'] for entry in filtered_history)
        total_usd = sum(entry['usd'] for entry in filtered_history)

        return {
            'period_days': days,
            'total_requests': len(filtered_history),
            'total_credits': total_credits,
            'total_usd': total_usd,
            'daily_usage': daily_usage,
            'resource_usage': resource_usage,
            'endpoint_usage': endpoint_usage
        }