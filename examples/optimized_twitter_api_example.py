"""
مثال استفاده از کلاینت بهینه‌شده TwitterAPI.io با مدیریت هزینه

این اسکریپت نمونه‌ای از نحوه استفاده از کلاینت بهینه‌شده TwitterAPI.io با مدیریت هزینه
و کنترل نرخ درخواست را نشان می‌دهد.
"""

import os
import logging
import json
from typing import Dict, Any

from lib.twitter_api.middleware import OptimizedTwitterAPIClient

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("twitter_example")

# کلید API از متغیر محیطی یا فایل تنظیمات
API_KEY = os.environ.get("TWITTER_API_KEY", "cf5800d7a52a4df89b5df7ffe1c7303d")


def print_separator(title: str) -> None:
    """نمایش جداکننده با عنوان برای خوانایی بهتر خروجی"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_dict(data: Dict[str, Any], indent: int = 2) -> None:
    """نمایش زیبای دیکشنری"""
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def init_optimized_client() -> OptimizedTwitterAPIClient:
    """راه‌اندازی کلاینت بهینه‌شده با تنظیمات مناسب"""
    client = OptimizedTwitterAPIClient(
        api_key=API_KEY,
        daily_budget_usd=0.5,  # 50 سنت در روز
        enable_cache=True,
        cache_dir='.twitter_cache',
        base_delay=1.0,  # 1 ثانیه تأخیر بین درخواست‌ها
        max_requests_per_minute=30,  # محدودیت تعداد درخواست در دقیقه
        default_max_pages=2,
        default_max_results=50
    )

    # نمایش وضعیت بودجه
    status = client.get_budget_status()
    print("وضعیت بودجه:")
    print(f"- بودجه روزانه: ${status['daily_budget_usd']:.2f}")
    print(f"- مصرف امروز: ${status['spent_today_usd']:.4f}")
    print(f"- باقیمانده: ${status['remaining_usd']:.4f} ({status['percentage_used']:.1f}%)")

    # نمایش وضعیت کش
    cache_stats = client.get_cache_stats()
    print("\nوضعیت کش:")
    print(f"- تعداد فایل‌ها: {cache_stats.get('files', 0)}")
    print(f"- اندازه: {cache_stats.get('size_mb', 0):.2f} MB")
    print(f"- نرخ موفقیت: {cache_stats.get('hit_rate_percent', 0):.1f}%")

    return client


def example_search_tweets(client: OptimizedTwitterAPIClient) -> None:
    """مثال جستجوی توییت‌ها با کلاینت بهینه‌شده"""
    print_separator("جستجوی توییت‌ها")

    try:
        # درخواست اول - احتمالاً از کش نخواهد بود
        print("درخواست اول برای جستجوی توییت‌ها:")
        tweets = client.search_tweets(
            query="برنامه‌نویسی OR هوش‌مصنوعی lang:fa",
            query_type="Latest",
            max_results=10
        )
        print(f"تعداد توییت‌ها: {len(tweets)}")

        if tweets:
            print(f"\nنمونه توییت:")
            print(f"- متن: {tweets[0].text}")
            print(f"- نویسنده: @{tweets[0].author.username if tweets[0].author else 'ناشناس'}")
            print(f"- تاریخ: {tweets[0].created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # نمایش وضعیت بودجه بعد از درخواست اول
        status = client.get_budget_status()
        print(f"\nمصرف بودجه بعد از درخواست اول: ${status['spent_today_usd']:.4f}")

        # درخواست دوم - همان جستجو (باید از کش استفاده کند)
        print("\nدرخواست دوم (همان جستجو - باید از کش استفاده کند):")
        tweets2 = client.search_tweets(
            query="برنامه‌نویسی OR هوش‌مصنوعی lang:fa",
            query_type="Latest",
            max_results=10
        )
        print(f"تعداد توییت‌ها: {len(tweets2)}")

        # نمایش وضعیت بودجه بعد از درخواست دوم
        status = client.get_budget_status()
        print(f"\nمصرف بودجه بعد از درخواست دوم: ${status['spent_today_usd']:.4f}")

        # نمایش وضعیت کش
        cache_stats = client.get_cache_stats()
        print(f"\nوضعیت کش بعد از درخواست‌ها:")
        print(f"- موفق: {cache_stats['hits']}, ناموفق: {cache_stats['misses']}")
        print(f"- نرخ موفقیت: {cache_stats['hit_rate_percent']:.1f}%")

    except Exception as e:
        logger.error(f"خطا در جستجوی توییت‌ها: {str(e)}")


def example_user_info(client: OptimizedTwitterAPIClient) -> None:
    """مثال دریافت اطلاعات کاربر با کلاینت بهینه‌شده"""
    print_separator("اطلاعات کاربر")

    try:
        username = "elonmusk"

        # درخواست اول - احتمالاً از کش نخواهد بود
        print(f"درخواست اول برای اطلاعات کاربر {username}:")
        user = client.get_user_info(username)

        print(f"- نام کاربری: @{user.username}")
        print(f"- نام: {user.name}")
        print(f"- دنبال‌کنندگان: {user.followers_count:,}")
        print(f"- تاریخ ایجاد: {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'نامشخص'}")

        # نمایش وضعیت بودجه بعد از درخواست
        status = client.get_budget_status()
        print(f"\nمصرف بودجه بعد از درخواست: ${status['spent_today_usd']:.4f}")

        # درخواست دوم - همان کاربر (باید از کش استفاده کند)
        print(f"\nدرخواست دوم (همان کاربر - باید از کش استفاده کند):")
        user2 = client.get_user_info(username)
        print(f"- نام کاربری: @{user2.username}")

        # نمایش وضعیت بودجه بعد از درخواست دوم
        status = client.get_budget_status()
        print(f"\nمصرف بودجه بعد از درخواست دوم: ${status['spent_today_usd']:.4f}")

    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات کاربر: {str(e)}")


def example_batch_user_info(client: OptimizedTwitterAPIClient) -> None:
    """مثال دریافت اطلاعات گروهی کاربران با کلاینت بهینه‌شده"""
    print_separator("دریافت گروهی اطلاعات کاربران")

    try:
        # شناسه‌های کاربران (نمونه)
        user_ids = [
            "44196397",  # elonmusk
            "783214",  # twitter
            "1514888570417291264"  # wef
        ]

        print(f"درخواست اطلاعات گروهی برای {len(user_ids)} کاربر:")
        users = client.get_users_by_ids_efficient(user_ids)

        print(f"تعداد کاربران دریافت شده: {len(users)}")

        for user in users:
            print(f"- @{user.username}: {user.name} ({user.followers_count:,} دنبال‌کننده)")

        # نمایش وضعیت بودجه بعد از درخواست
        status = client.get_budget_status()
        print(f"\nمصرف بودجه بعد از درخواست: ${status['spent_today_usd']:.4f}")

    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات گروهی کاربران: {str(e)}")


def example_generate_report(client: OptimizedTwitterAPIClient) -> None:
    """مثال تولید گزارش مصرف با کلاینت بهینه‌شده"""
    print_separator("گزارش مصرف API")

    try:
        # تولید گزارش برای 7 روز اخیر
        report = client.generate_usage_report(days=7)

        print(f"گزارش مصرف برای {report['period_days']} روز اخیر:")
        print(f"- تعداد کل درخواست‌ها: {report['total_requests']:,}")
        print(f"- مصرف کل: {report['total_credits']:,} اعتبار (${report['total_usd']:.4f})")

        # نمایش مصرف به تفکیک منبع
        if 'resource_usage' in report and report['resource_usage']:
            print("\nمصرف به تفکیک نوع منبع:")
            for resource, usage in report['resource_usage'].items():
                print(f"- {resource}: {usage['count']:,} عدد, {usage['credits']:,} اعتبار (${usage['usd']:.4f})")

        # نمایش مصرف به تفکیک endpoint
        if 'endpoint_usage' in report and report['endpoint_usage']:
            print("\nمصرف به تفکیک endpoint:")
            for endpoint, usage in report['endpoint_usage'].items():
                print(f"- {endpoint}: {usage['requests']:,} درخواست, {usage['credits']:,} اعتبار (${usage['usd']:.4f})")

    except Exception as e:
        logger.error(f"خطا در تولید گزارش مصرف: {str(e)}")


def main() -> None:
    """اجرای تمام مثال‌ها"""
    try:
        # راه‌اندازی کلاینت بهینه‌شده
        client = init_optimized_client()

        # اجرای مثال‌ها
        example_search_tweets(client)
        example_user_info(client)
        example_batch_user_info(client)
        example_generate_report(client)

        # نمایش وضعیت نهایی بودجه
        print_separator("وضعیت نهایی")
        status = client.get_budget_status()
        print(f"مصرف کل: ${status['spent_today_usd']:.4f} از ${status['daily_budget_usd']:.2f}")
        print(f"باقیمانده: ${status['remaining_usd']:.4f} ({status['percentage_used']:.1f}%)")

    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {str(e)}")


if __name__ == "__main__":
    main()