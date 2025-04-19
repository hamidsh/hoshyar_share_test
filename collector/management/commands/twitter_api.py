import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from lib.twitter_api.middleware import OptimizedTwitterAPIClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'مدیریت TwitterAPI.io و نمایش آمار مصرف'

    def add_arguments(self, parser):
        # زیر دستورات اصلی
        subparsers = parser.add_subparsers(dest='command', help='زیر دستور')

        # دستور status
        status_parser = subparsers.add_parser('status', help='نمایش وضعیت API')

        # دستور report
        report_parser = subparsers.add_parser('report', help='تولید گزارش مصرف')
        report_parser.add_argument(
            '--days', type=int, default=7,
            help='تعداد روزهای گذشته برای گزارش (پیش‌فرض: 7)'
        )
        report_parser.add_argument(
            '--format', choices=['text', 'json'], default='text',
            help='قالب خروجی گزارش (پیش‌فرض: text)'
        )

        # دستور cache
        cache_parser = subparsers.add_parser('cache', help='مدیریت کش')
        cache_parser.add_argument(
            'cache_action', choices=['status', 'clear'],
            help='عملیات کش (status: نمایش وضعیت، clear: پاکسازی)'
        )
        cache_parser.add_argument(
            '--endpoint', type=str,
            help='پاکسازی کش فقط برای یک endpoint خاص'
        )

        # دستور test
        test_parser = subparsers.add_parser('test', help='تست اتصال به API')
        test_parser.add_argument(
            '--query', type=str, default='برنامه‌نویسی lang:fa',
            help='کوئری برای تست جستجو (پیش‌فرض: "برنامه‌نویسی lang:fa")'
        )
        test_parser.add_argument(
            '--count', type=int, default=5,
            help='تعداد نتایج (پیش‌فرض: 5)'
        )

    def handle(self, *args, **options):
        command = options['command']

        if not command:
            self.print_help('manage.py', 'twitter_api')
            return

        try:
            # ایجاد کلاینت بهینه‌شده
            client = self._create_client()

            if command == 'status':
                self._handle_status(client)
            elif command == 'report':
                self._handle_report(client, options)
            elif command == 'cache':
                self._handle_cache(client, options)
            elif command == 'test':
                self._handle_test(client, options)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"خطا: {str(e)}"))
            logger.error(f"خطا در اجرای دستور twitter_api {command}: {str(e)}")
            raise CommandError(str(e))

    def _create_client(self):
        """ایجاد کلاینت بهینه‌شده با تنظیمات از فایل settings"""
        api_key = getattr(settings, 'TWITTER_API_KEY', None)
        if not api_key:
            raise CommandError("TWITTER_API_KEY در تنظیمات تعریف نشده است")

        daily_budget = getattr(settings, 'TWITTER_API_DAILY_BUDGET_USD', 0.5)
        enable_cache = getattr(settings, 'TWITTER_API_CACHE_ENABLED', True)
        cache_dir = getattr(settings, 'TWITTER_API_CACHE_DIR', '.twitter_cache')
        max_rpm = getattr(settings, 'TWITTER_API_MAX_REQUESTS_PER_MINUTE', 30)
        base_delay = getattr(settings, 'TWITTER_API_BASE_DELAY', 1.0)

        return OptimizedTwitterAPIClient(
            api_key=api_key,
            daily_budget_usd=daily_budget,
            enable_cache=enable_cache,
            cache_dir=cache_dir,
            max_requests_per_minute=max_rpm,
            base_delay=base_delay
        )

    def _handle_status(self, client):
        """نمایش وضعیت API"""
        status = client.get_budget_status()

        self.stdout.write(self.style.SUCCESS("=== وضعیت TwitterAPI.io ==="))
        self.stdout.write(f"کلید API: ***{client.client.base.api_key[-4:]}")
        self.stdout.write(f"بودجه روزانه: ${status['daily_budget_usd']:.2f}")
        self.stdout.write(f"مصرف امروز: ${status['spent_today_usd']:.4f}")
        self.stdout.write(f"باقیمانده: ${status['remaining_usd']:.4f}")
        self.stdout.write(f"درصد مصرف: {status['percentage_used']:.1f}%")

        # وضعیت کش
        if client.enable_cache:
            cache_stats = client.get_cache_stats()
            self.stdout.write("\n=== وضعیت کش ===")
            self.stdout.write(f"فعال: بله")
            self.stdout.write(f"تعداد فایل‌ها: {cache_stats.get('files', 0)}")
            self.stdout.write(f"اندازه: {cache_stats.get('size_mb', 0):.2f} MB")

            hits = cache_stats.get('hits', 0)
            misses = cache_stats.get('misses', 0)
            total = hits + misses

            hit_rate = 0
            if total > 0:
                hit_rate = (hits / total) * 100

            self.stdout.write(f"نرخ موفقیت: {hit_rate:.1f}% ({hits} از {total})")
        else:
            self.stdout.write("\n=== وضعیت کش ===")
            self.stdout.write(f"فعال: خیر")

    def _handle_report(self, client, options):
        """تولید گزارش مصرف API"""
        days = options['days']
        output_format = options['format']

        report = client.generate_usage_report(days=days)

        if output_format == 'json':
            # خروجی JSON
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))
            return

        # خروجی متنی
        self.stdout.write(self.style.SUCCESS(f"=== گزارش مصرف {days} روز اخیر ==="))
        self.stdout.write(f"تعداد کل درخواست‌ها: {report['total_requests']}")
        self.stdout.write(f"مصرف کل: {report['total_credits']:,} اعتبار (${report['total_usd']:.4f})")

        # نمایش مصرف روزانه
        if 'daily_usage' in report and report['daily_usage']:
            self.stdout.write("\n--- مصرف روزانه ---")
            for day, usage in sorted(report['daily_usage'].items()):
                self.stdout.write(
                    f"{day}: {usage['requests']} درخواست, "
                    f"{usage['credits']:,} اعتبار (${usage['usd']:.4f})"
                )

        # نمایش مصرف منابع
        if 'resource_usage' in report and report['resource_usage']:
            self.stdout.write("\n--- مصرف به تفکیک نوع منبع ---")
            for resource, usage in report['resource_usage'].items():
                self.stdout.write(
                    f"{resource}: {usage['count']:,} عدد, "
                    f"{usage['credits']:,} اعتبار (${usage['usd']:.4f})"
                )

        # نمایش مصرف endpoint
        if 'endpoint_usage' in report and report['endpoint_usage']:
            self.stdout.write("\n--- مصرف به تفکیک endpoint ---")
            for endpoint, usage in sorted(
                    report['endpoint_usage'].items(),
                    key=lambda x: x[1]['credits'],
                    reverse=True
            ):
                self.stdout.write(
                    f"{endpoint}: {usage['requests']} درخواست, "
                    f"{usage['credits']:,} اعتبار (${usage['usd']:.4f})"
                )

    def _handle_cache(self, client, options):
        """مدیریت کش API"""
        action = options['cache_action']
        endpoint = options.get('endpoint')

        if not client.enable_cache:
            self.stdout.write(self.style.WARNING("کش غیرفعال است"))
            return

        if action == 'status':
            # نمایش وضعیت کش
            cache_stats = client.get_cache_stats()
            self.stdout.write(self.style.SUCCESS("=== وضعیت کش ==="))
            self.stdout.write(f"تعداد فایل‌ها: {cache_stats.get('files', 0)}")
            self.stdout.write(
                f"اندازه: {cache_stats.get('size_mb', 0):.2f} MB / {cache_stats.get('max_size_mb', 0)} MB")
            self.stdout.write(f"تعداد موفق: {cache_stats.get('hits', 0)}")
            self.stdout.write(f"تعداد ناموفق: {cache_stats.get('misses', 0)}")
            self.stdout.write(f"نرخ موفقیت: {cache_stats.get('hit_rate_percent', 0):.1f}%")

        elif action == 'clear':
            # پاکسازی کش
            count = client.clear_cache(endpoint)
            if endpoint:
                self.stdout.write(self.style.SUCCESS(f"{count} فایل کش برای endpoint {endpoint} پاک شد"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{count} فایل کش پاک شد"))

    def _handle_test(self, client, options):
        """تست اتصال به API و جستجو"""
        query = options['query']
        count = options['count']

        self.stdout.write(self.style.SUCCESS(f"=== تست اتصال به TwitterAPI.io ==="))
        self.stdout.write(f"کوئری جستجو: {query}")
        self.stdout.write(f"تعداد نتایج: {count}")
        self.stdout.write("در حال ارسال درخواست...")

        # نمایش وضعیت قبلی
        status_before = client.get_budget_status()
        self.stdout.write(f"مصرف قبل از درخواست: ${status_before['spent_today_usd']:.4f}")

        # ارسال درخواست
        try:
            tweets = client.search_tweets_safe(query=query, max_results=count)
            self.stdout.write(self.style.SUCCESS(f"درخواست موفق: {len(tweets)} توییت دریافت شد"))

            # نمایش توییت‌ها
            for i, tweet in enumerate(tweets, 1):
                self.stdout.write(
                    f"\n[{i}] @{tweet.author.username if tweet.author else 'ناشناس'}: {tweet.text[:100]}...")

            # نمایش وضعیت بعدی
            status_after = client.get_budget_status()
            cost = status_after['spent_today_usd'] - status_before['spent_today_usd']
            self.stdout.write(f"\nهزینه این درخواست: ${cost:.6f}")
            self.stdout.write(f"مصرف بعد از درخواست: ${status_after['spent_today_usd']:.4f}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطا در درخواست: {str(e)}"))