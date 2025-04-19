# راهنمای مدیریت هزینه TwitterAPI.io

این راهنما توضیح می‌دهد که چگونه از سیستم مدیریت هزینه TwitterAPI.io در پروژه **هُشیار** استفاده کنید.

## مقدمه

مدل هزینه‌گذاری TwitterAPI.io بر اساس تعداد درخواست و نوع داده دریافتی است. برای جلوگیری از هزینه‌های غیرمنتظره و کنترل بهتر مصرف API، یک لایه میان‌افزار (`middleware`) ایجاد شده که امکانات زیر را فراهم می‌کند:

1. **مدیریت بودجه**: تنظیم و کنترل بودجه روزانه
2. **کش کردن**: ذخیره نتایج برای کاهش درخواست‌های تکراری
3. **کنترل نرخ**: تنظیم تأخیر بین درخواست‌ها
4. **محدودیت پارامترها**: کنترل تعداد صفحات و نتایج
5. **گزارش‌دهی**: دریافت گزارش دقیق از مصرف API

## نرخ هزینه TwitterAPI.io

- **توییت‌ها**: 15 اعتبار برای هر 1000 توییت ($0.15/1K)
- **پروفایل‌ها**: 18 اعتبار برای هر 1000 کاربر ($0.18/1K)
- **دنبال‌کنندگان**: 15 اعتبار برای هر 1000 دنبال‌کننده ($0.15/1K)
- **حداقل هزینه هر درخواست**: 15 اعتبار ($0.00015)

## تنظیمات میان‌افزار

تنظیمات اصلی در فایل `core/settings.py` قرار دارند:

```python
# Twitter API Settings
TWITTER_API_KEY = ""  # کلید از settings_local.py خوانده می‌شود
TWITTER_API_DAILY_BUDGET_USD = 0.5  # بودجه روزانه به دلار
TWITTER_API_CACHE_ENABLED = True  # فعال‌سازی کش
TWITTER_API_CACHE_DIR = '.twitter_cache'  # دایرکتوری کش
TWITTER_API_MAX_REQUESTS_PER_MINUTE = 30  # حداکثر تعداد درخواست در دقیقه
TWITTER_API_BASE_DELAY = 1.0  # تأخیر پایه بین درخواست‌ها (ثانیه)
TWITTER_API_DEFAULT_MAX_PAGES = 1  # محدودیت پیش‌فرض تعداد صفحات
TWITTER_API_DEFAULT_MAX_RESULTS = 50  # محدودیت پیش‌فرض تعداد نتایج
```

### تنظیم بودجه روزانه

مقدار پیش‌فرض بودجه روزانه 0.5 دلار است. این مقدار را می‌توانید در فایل `settings.py` یا `settings_local.py` تغییر دهید:

```python
TWITTER_API_DAILY_BUDGET_USD = 1.0  # افزایش بودجه به 1 دلار در روز
```

### فعال‌سازی یا غیرفعال‌سازی کش

کش کردن نتایج API می‌تواند به میزان قابل توجهی هزینه‌ها را کاهش دهد. برای فعال یا غیرفعال کردن آن:

```python
TWITTER_API_CACHE_ENABLED = True  # فعال
# یا
TWITTER_API_CACHE_ENABLED = False  # غیرفعال
```

### تنظیم حداکثر تعداد صفحات و نتایج

برای جلوگیری از دریافت داده‌های زیاد، محدودیت پیش‌فرض تعداد صفحات و نتایج تنظیم شده است:

```python
TWITTER_API_DEFAULT_MAX_PAGES = 2  # حداکثر 2 صفحه
TWITTER_API_DEFAULT_MAX_RESULTS = 100  # حداکثر 100 نتیجه
```

## استفاده از کلاینت بهینه‌شده

### استفاده مستقیم

برای استفاده مستقیم از کلاینت بهینه‌شده:

```python
from lib.twitter_api.middleware import OptimizedTwitterAPIClient

client = OptimizedTwitterAPIClient(
    api_key="your_api_key",
    daily_budget_usd=0.5,
    enable_cache=True
)

# جستجوی امن توییت‌ها با کنترل هزینه
tweets = client.search_tweets_safe(
    query="برنامه‌نویسی lang:fa",
    query_type="Latest",
    max_results=20
)

# دریافت وضعیت بودجه
budget_status = client.get_budget_status()
print(f"بودجه امروز: ${budget_status['daily_budget_usd']:.2f}")
print(f"مصرف تا کنون: ${budget_status['spent_today_usd']:.4f}")
print(f"باقیمانده: ${budget_status['remaining_usd']:.4f}")
```

### استفاده در سرویس‌ها

سرویس `TwitterCollectorService` برای استفاده از کلاینت بهینه‌شده به‌روزرسانی شده است:

```python
from collector.services import TwitterCollectorService

service = TwitterCollectorService(
    api_key="your_api_key",
    use_real_api=True,  # استفاده از API واقعی (به جای داده‌های تستی)
    daily_budget_usd=0.5
)

# دریافت وضعیت API
api_status = service.get_api_status()
print(f"وضعیت API: {api_status}")
```

## اولویت‌بندی کوئری‌های جستجو

برای مدیریت بهتر هزینه، می‌توانید به کوئری‌های جستجو اولویت اختصاص دهید:

- **اولویت بالا (high)**: در شرایط محدودیت بودجه هم اجرا می‌شوند
- **اولویت متوسط (medium)**: در شرایط عادی اجرا می‌شوند
- **اولویت پایین (low)**: فقط در شرایط مناسب اجرا می‌شوند

این اولویت‌ها در پنل ادمین Django قابل تنظیم هستند.

## گزارش‌گیری از مصرف API

برای دریافت گزارش مصرف API:

```python
from lib.twitter_api.middleware import OptimizedTwitterAPIClient

client = OptimizedTwitterAPIClient(api_key="your_api_key")

# گزارش مصرف 7 روز اخیر
report = client.generate_usage_report(days=7)
print(f"تعداد کل درخواست‌ها: {report['total_requests']}")
print(f"هزینه کل: ${report['total_usd']:.2f}")

# مصرف به تفکیک endpoint
for endpoint, usage in report['endpoint_usage'].items():
    print(f"{endpoint}: {usage['requests']} درخواست، ${usage['usd']:.4f}")
```

## نکات مهم

1. **کش کردن**: کش کردن نتایج یکی از مؤثرترین روش‌ها برای کاهش هزینه است. زمان‌های اعتبار کش بر اساس نوع endpoint تنظیم شده‌اند.

2. **پارامترهای pagination**: در صورت امکان، تعداد صفحات و نتایج را محدود کنید تا هزینه‌ها کنترل شوند.

3. **درخواست‌های گروهی**: برای دریافت اطلاعات چندین کاربر، از متد `get_users_by_ids_efficient` استفاده کنید که از درخواست‌های گروهی با هزینه کمتر بهره می‌برد.

4. **تأخیر بین درخواست‌ها**: برای جلوگیری از ارسال درخواست‌های متوالی سریع، تأخیر مناسب بین درخواست‌ها تنظیم شده است.

5. **کنترل خودکار بودجه**: زمانی که بیش از 80% بودجه روزانه مصرف شود، فقط کوئری‌های با اولویت بالا اجرا می‌شوند.