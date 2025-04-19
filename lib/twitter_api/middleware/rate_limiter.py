"""
سیستم کنترل نرخ درخواست برای TwitterAPI.io

این ماژول امکان کنترل نرخ ارسال درخواست به API را فراهم می‌کند تا از
ارسال درخواست‌های متوالی با سرعت بالا جلوگیری شود.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """مدیریت نرخ درخواست‌ها برای جلوگیری از ارسال بیش از حد به TwitterAPI.io"""

    def __init__(self,
                 budget=None,
                 max_per_minute: int = 60,
                 min_delay: float = 0.5,
                 adaptive_delay: bool = True):
        """
        مقداردهی اولیه کنترل‌کننده نرخ

        Args:
            budget: نمونه کلاس TwitterAPIBudget برای انطباق تأخیر با بودجه (اختیاری)
            max_per_minute: حداکثر تعداد درخواست مجاز در هر دقیقه
            min_delay: حداقل تأخیر بین درخواست‌ها (ثانیه)
            adaptive_delay: فعال‌سازی سیستم تأخیر تطبیقی بر اساس بودجه
        """
        self.budget = budget
        self.max_per_minute = max_per_minute
        self.min_delay = min_delay
        self.adaptive_delay = adaptive_delay
        self.requests = []  # زمان درخواست‌های اخیر
        self.last_request_time = None  # زمان آخرین درخواست
        self.lock = threading.Lock()

        logger.info(
            f"کنترل‌کننده نرخ راه‌اندازی شد. "
            f"محدودیت: {max_per_minute} درخواست در دقیقه، "
            f"تأخیر پایه: {min_delay} ثانیه، "
            f"تأخیر تطبیقی: {'فعال' if adaptive_delay else 'غیرفعال'}"
        )

    def wait_if_needed(self,
                       endpoint: Optional[str] = None,
                       estimated_cost: Optional[float] = None) -> float:
        """
        در صورت نیاز، منتظر ماندن قبل از ارسال درخواست جدید

        Args:
            endpoint: آدرس endpoint مورد استفاده (برای لاگ)
            estimated_cost: هزینه تخمینی درخواست (برای تأخیر تطبیقی)

        Returns:
            زمان واقعی انتظار (ثانیه)
        """
        with self.lock:
            now = datetime.now()
            wait_time = 0

            # حذف درخواست‌های قدیمی تر از 1 دقیقه
            self.requests = [t for t in self.requests if now - t < timedelta(minutes=1)]

            # بررسی محدودیت تعداد درخواست در دقیقه
            if len(self.requests) >= self.max_per_minute:
                oldest = self.requests[0]
                wait_time_rate_limit = (oldest + timedelta(minutes=1) - now).total_seconds()

                if wait_time_rate_limit > 0:
                    wait_time = max(wait_time, wait_time_rate_limit)
                    logger.info(
                        f"محدودیت نرخ درخواست ({self.max_per_minute}/دقیقه): "
                        f"انتظار {wait_time:.2f} ثانیه قبل از درخواست بعدی"
                    )

            # بررسی تأخیر حداقل بین درخواست‌ها
            if self.last_request_time:
                time_since_last = (now - self.last_request_time).total_seconds()

                # محاسبه تأخیر مورد نیاز
                required_delay = self._calculate_delay(estimated_cost)

                if time_since_last < required_delay:
                    delay_time = required_delay - time_since_last
                    wait_time = max(wait_time, delay_time)

            # اعمال تأخیر اگر لازم است
            if wait_time > 0:
                if endpoint:
                    logger.debug(f"انتظار {wait_time:.2f} ثانیه قبل از درخواست به {endpoint}")
                time.sleep(wait_time)

            # ثبت درخواست جدید
            self.requests.append(datetime.now())
            self.last_request_time = datetime.now()

            return wait_time

    def _calculate_delay(self, estimated_cost: Optional[float] = None) -> float:
        """
        محاسبه تأخیر مناسب بین درخواست‌ها

        Args:
            estimated_cost: هزینه تخمینی درخواست

        Returns:
            تأخیر مناسب (ثانیه)
        """
        # تأخیر پایه
        delay = self.min_delay

        # اگر حالت تطبیقی فعال باشد و بودجه تنظیم شده باشد
        if self.adaptive_delay and self.budget:
            status = self.budget.get_status()
            percent_used = status['percentage_used']

            # افزایش تأخیر با مصرف بودجه
            if percent_used < 50:
                # تأخیر پایه
                pass
            elif percent_used < 75:
                # افزایش خطی تا دو برابر
                delay *= (1 + (percent_used - 50) / 25)
            elif percent_used < 90:
                # افزایش خطی تا پنج برابر
                delay *= (3 + (percent_used - 75) / 5)
            else:
                # افزایش شدید نزدیک محدودیت
                delay *= (6 + (percent_used - 90) * 4)

        # افزایش تأخیر برای درخواست‌های پرهزینه
        if estimated_cost is not None and self.budget is not None:
            base_cost = self.budget.CREDITS['request']
            if estimated_cost > base_cost:
                cost_factor = min(5.0, estimated_cost / base_cost)
                delay *= max(1.0, cost_factor / 2)

        return delay

    def add_delay(self, seconds: float = None) -> None:
        """
        اضافه کردن تأخیر دستی بین درخواست‌ها

        Args:
            seconds: مدت تأخیر (ثانیه)، اگر None باشد از مقدار پیش‌فرض استفاده می‌شود
        """
        if seconds is None:
            seconds = self.min_delay

        if seconds > 0:
            time.sleep(seconds)

    def get_stats(self) -> dict:
        """
        دریافت آمار کنترل‌کننده نرخ

        Returns:
            دیکشنری حاوی آمار
        """
        with self.lock:
            now = datetime.now()
            self.requests = [t for t in self.requests if now - t < timedelta(minutes=1)]

            # محاسبه سرعت میانگین درخواست‌ها
            avg_rate = 0
            if len(self.requests) >= 2:
                time_span = (self.requests[-1] - self.requests[0]).total_seconds()
                if time_span > 0:
                    avg_rate = (len(self.requests) - 1) / time_span

            return {
                'current_minute_requests': len(self.requests),
                'max_per_minute': self.max_per_minute,
                'usage_percent': (len(self.requests) / self.max_per_minute) * 100,
                'min_delay': self.min_delay,
                'adaptive_delay': self.adaptive_delay,
                'avg_requests_per_second': avg_rate,
                'last_request': self.last_request_time.isoformat() if self.last_request_time else None
            }