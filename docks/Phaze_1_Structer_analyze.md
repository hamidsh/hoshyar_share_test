# مستندات جامع پروژه هُشیار

## فهرست مطالب
1. [خلاصه پروژه](#1-خلاصه-پروژه)
2. [ساختار فعلی پروژه](#2-ساختار-فعلی-پروژه)
3. [معماری و ارتباط بین ماژول‌ها](#3-معماری-و-ارتباط-بین-ماژولها)
4. [جریان داده در سیستم](#4-جریان-داده-در-سیستم)
5. [API‌ها و نقاط پایانی](#5-apiها-و-نقاط-پایانی)
6. [مستندات تکنیکی ماژول‌ها](#6-مستندات-تکنیکی-ماژولها)
7. [وابستگی‌ها و نصب](#7-وابستگیها-و-نصب)
8. [راه‌اندازی و اجرا](#8-راهاندازی-و-اجرا)
9. [راهنمای توسعه‌دهندگان](#9-راهنمای-توسعهدهندگان)

## 1. خلاصه پروژه

هُشیار یک سیستم هوشمند مانیتورینگ و تحلیل توییت‌های فارسی است که با هدف شناسایی الگوها، روندها و روابط پیچیده در شبکه‌های اجتماعی توسعه یافته است. این سیستم علاوه بر جمع‌آوری و تحلیل توییت‌ها، داده‌های خبری را نیز از منابع RSS جمع‌آوری کرده و با ترکیب این دو منبع، تحلیل‌های عمیق‌تر و جامع‌تری ارائه می‌دهد.

هُشیار از یک معماری ماژولار با کامپوننت‌های مختلف برای جمع‌آوری، پردازش، تحلیل و ارائه داده‌ها استفاده می‌کند. سیستم از هوش مصنوعی (Claude و Grok) برای تحلیل محتوا و کشف الگوها استفاده کرده و دارای سیستم حافظه چندسطحی برای مدیریت بهینه داده‌ها است.

## 2. ساختار فعلی پروژه

### ساختار پوشه‌ها

```
hoshyar/
├── analyzer/               # ماژول تحلیل داده و احساسات
├── api/                    # ماژول API برای ارتباطات خارجی
├── collector/              # ماژول جمع‌آوری داده از توییتر
│   ├── management/         # دستورات مدیریتی Django
│   │   └── commands/
├── core/                   # تنظیمات اصلی و پیکربندی پروژه
├── examples/               # مثال‌های کاربردی
├── lib/                    # کتابخانه‌های سفارشی
│   └── twitter_api/        # کتابخانه ارتباط با TwitterAPI.io
│       ├── middleware/     # میان‌افزارهای بهینه‌سازی
│       ├── models/         # مدل‌های داده
│       └── utils/          # ابزارهای کمکی
├── memory/                 # ماژول مدیریت حافظه و تاریخچه
├── news/                   # ماژول جمع‌آوری اخبار از RSS
├── processor/              # ماژول پردازش و فیلترینگ داده‌ها
├── manage.py               # دستورات مدیریتی Django
└── ROADMAP.md              # نقشه راه پروژه
```

### مدل‌های داده اصلی

پروژه از چندین مدل داده کلیدی استفاده می‌کند:

1. **TwitterUser** - اطلاعات کاربران توییتر و امتیاز تأثیرگذاری
2. **Tweet** - توییت‌های جمع‌آوری شده با متادیتا و امتیازها
3. **SearchQuery** - کوئری‌های جستجو برای جمع‌آوری خودکار توییت‌ها
4. **NewsSource** - منابع خبری و آدرس‌های RSS
5. **NewsArticle** - مقالات خبری جمع‌آوری شده
6. **Topic** - موضوعات و دسته‌بندی‌های محتوا
7. **UserRelationship** - روابط بین کاربران با قدرت ارتباط
8. **MemoryRecord** - رکوردهای حافظه برای سطوح مختلف زمانی
9. **SentimentAnalysis** - نتایج تحلیل احساسات
10. **Pattern** - الگوهای شناسایی شده در داده‌ها

### سرویس‌های اصلی

سیستم از چندین سرویس کلیدی تشکیل شده است:

1. **TwitterCollectorService** - جمع‌آوری توییت‌ها از TwitterAPI.io
2. **NewsCollectorService** - جمع‌آوری اخبار از منابع RSS
3. **TweetFilterService** - فیلترینگ و پیش‌پردازش توییت‌ها
4. **SentimentAnalyzer** - تحلیل احساسات توییت‌ها و اخبار
5. **OptimizedTwitterAPIClient** - کلاینت بهینه‌شده توییتر با مدیریت هزینه
6. **TwitterAPIBudget** - مدیریت بودجه API توییتر
7. **TwitterAPICache** - کش‌کردن درخواست‌های API
8. **RateLimiter** - مدیریت نرخ درخواست به API

## 3. معماری و ارتباط بین ماژول‌ها

### نمودار معماری سیستم

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│ جمع‌آوری داده‌ها  │────▶│  پیش‌پردازش     │────▶│  تحلیل و پردازش │────▶│  ارائه و انتشار  │
│ (توییت و اخبار) │     │  و فیلترینگ     │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
        ▲  ▲                  ▲                     ▲  ▲                     ▲
        │  │                  │                     │  │                     │
        │  │                  │                     │  │                     │
        │  │                  │                     │  │                     │
┌───────┘  └──────────┐      └──────────┐  ┌───────┘  └───────┐      ┌──────┘
│                     │                  │  │                  │      │        
│  TwitterAPI.io      │                  │  │  claude 3.7 sonnet   │      │        
└─────────────────────┘                  │  └──────────────────┘      │        
                                         │                            │        
┌─────────────────────┐                  │  ┌──────────────────┐      │        
│                     │                  │  │                  │      │        
│  RSS Feeds          │                  │  │    claude 3.5 haiku API     │      │        
└─────────────────────┘                  │  └──────────────────┘      │        
        ▲                                │                            │        
        │                                │                            │        
        └────────────────────────────────┴────────────────────────────┘        
                                         ▲                                     
                                         │                                     
                          ┌──────────────┴───────────────┐                     
                          │                              │                     
                          │   مدیریت حافظه و تاریخچه      │                     
                          │  (توییت‌ها، اخبار، روندها)     │                     
                          └──────────────────────────────┘                     
                                         ▲                                     
                                         │                                     
                          ┌──────────────┴───────────────┐                     
                          │                              │                     
                          │         زیرساخت API          │                     
                          │                              │                     
                          └──────────────────────────────┘                     
                                    ▲           ▲                              
                                    │           │                              
                      ┌─────────────┘           └───────────────┐              
                      │                                         │              
             ┌────────┴─────────┐                     ┌─────────┴────────┐     
             │                  │                     │                  │     
             │    ربات تلگرام    │                     │ داشبورد (آینده)   │     
             │                  │                     │                  │     
             └──────────────────┘                     └──────────────────┘     
```

### ارتباط بین ماژول‌ها

#### جمع‌آوری داده‌ها
- **collector**: جمع‌آوری داده از TwitterAPI.io
- **news**: جمع‌آوری اخبار از منابع RSS
- **lib/twitter_api**: کتابخانه سفارشی برای ارتباط با TwitterAPI.io

#### پیش‌پردازش و فیلترینگ
- **processor**: فیلترینگ و پیش‌پردازش توییت‌ها و اخبار
- استخراج کلمات کلیدی، هشتگ‌ها و روابط بین کاربران

#### تحلیل و پردازش
- **analyzer**: تحلیل احساسات و شناسایی الگوها
- ارتباط با API‌های claude 3.7 sonnet  و claude 3.5 haiku API برای تحلیل هوشمند

#### مدیریت حافظه
- **memory**: مدیریت و سازماندهی داده‌ها در سطوح مختلف زمانی
- ایجاد ارتباط بین توییت‌ها، اخبار و موضوعات

#### ارائه و انتشار
- **api**: ارائه داده‌ها و نتایج از طریق API
- ربات تلگرام برای ارسال گزارش‌ها و هشدارها (در آینده)

## 4. جریان داده در سیستم

### جریان کلی داده

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│           │    │           │    │           │    │           │    │           │
│ جمع‌آوری   │───▶│ فیلترینگ  │───▶│  تحلیل    │───▶│  ذخیره    │───▶│  گزارش    │
│           │    │           │    │           │    │           │    │           │
└───────────┘    └───────────┘    └───────────┘    └───────────┘    └───────────┘
```

### جزئیات جریان داده

1. **جمع‌آوری داده‌ها**:
   - وظایف `collect_new_tweets` و `collect_news` به صورت دوره‌ای اجرا می‌شوند
   - `TwitterCollectorService` توییت‌ها را از TwitterAPI.io جمع‌آوری می‌کند
   - `NewsCollectorService` اخبار را از منابع RSS جمع‌آوری می‌کند
   - داده‌های جمع‌آوری شده در مدل‌های `Tweet` و `NewsArticle` ذخیره می‌شوند

2. **فیلترینگ و پیش‌پردازش**:
   - وظیفه `filter_new_tweets` به صورت دوره‌ای اجرا می‌شود
   - `TweetFilterService` توییت‌ها را فیلتر کرده و محتوای نامناسب را حذف می‌کند
   - کلمات کلیدی، هشتگ‌ها و منشن‌ها استخراج می‌شوند
   - امتیاز تعامل و اهمیت محاسبه می‌شود

3. **تحلیل**:
   - وظیفه `analyze_recent_tweets` احساسات توییت‌ها را تحلیل می‌کند
   - `SentimentAnalyzer` احساسات (مثبت، منفی، خنثی) را تشخیص می‌دهد
   - الگوها و روندها شناسایی و در مدل `Pattern` ذخیره می‌شوند
   - روابط بین کاربران مدل‌سازی و در مدل `UserRelationship` ذخیره می‌شوند

4. **ذخیره و مدیریت حافظه**:
   - داده‌ها در سطوح مختلف زمانی (کوتاه‌مدت، میان‌مدت، بلندمدت) در مدل `MemoryRecord` ذخیره می‌شوند
   - خلاصه‌سازی داده‌ها برای بهینه‌سازی حافظه انجام می‌شود
   - داده‌ها به موضوعات (`Topic`) دسته‌بندی می‌شوند

5. **گزارش و ارائه**:
   - API نقاط پایانی برای دسترسی به داده‌ها و نتایج تحلیل فراهم می‌کند
   - گزارش‌های دوره‌ای تولید می‌شوند
   - هشدارها برای رویدادهای مهم صادر می‌شوند

## 5. API‌ها و نقاط پایانی

> **نکته**: براساس بررسی کدها، API هنوز در مراحل اولیه توسعه است. `api/urls.py` خالی است که نشان می‌دهد نقاط پایانی هنوز پیاده‌سازی نشده‌اند.

### نقاط پایانی احتمالی مطابق با ساختار پروژه

#### Tweet APIs
- `GET /api/tweets/` - دریافت لیست توییت‌ها با فیلترینگ و صفحه‌بندی
- `GET /api/tweets/<tweet_id>/` - دریافت جزئیات یک توییت خاص
- `GET /api/tweets/search/` - جستجوی توییت‌ها براساس کلمات کلیدی، هشتگ‌ها و غیره

#### User APIs
- `GET /api/users/` - دریافت لیست کاربران
- `GET /api/users/<user_id>/` - دریافت جزئیات یک کاربر خاص
- `GET /api/users/<user_id>/tweets/` - دریافت توییت‌های یک کاربر
- `GET /api/users/<user_id>/relationships/` - دریافت روابط یک کاربر با دیگران

#### Topic APIs
- `GET /api/topics/` - دریافت لیست موضوعات
- `GET /api/topics/<topic_id>/` - دریافت جزئیات یک موضوع خاص
- `GET /api/topics/<topic_id>/tweets/` - دریافت توییت‌های مرتبط با یک موضوع
- `GET /api/topics/<topic_id>/news/` - دریافت اخبار مرتبط با یک موضوع

#### Memory APIs
- `GET /api/memory/` - دریافت رکوردهای حافظه
- `GET /api/memory/<memory_id>/` - دریافت جزئیات یک رکورد حافظه خاص
- `GET /api/memory/short_term/` - دریافت حافظه کوتاه‌مدت
- `GET /api/memory/long_term/` - دریافت حافظه بلندمدت

#### News APIs
- `GET /api/news/` - دریافت لیست اخبار
- `GET /api/news/<article_id>/` - دریافت جزئیات یک خبر خاص
- `GET /api/news/sources/` - دریافت لیست منابع خبری

#### Analysis APIs
- `GET /api/sentiment/` - دریافت نتایج تحلیل احساسات
- `GET /api/patterns/` - دریافت الگوهای شناسایی شده
- `GET /api/reports/` - دریافت گزارش‌های تولید شده

#### Management APIs
- `GET /api/status/` - دریافت وضعیت سیستم
- `POST /api/collect/tweets/` - شروع یک وظیفه جمع‌آوری توییت
- `POST /api/collect/news/` - شروع یک وظیفه جمع‌آوری اخبار

## 6. مستندات تکنیکی ماژول‌ها

### ماژول collector

مسئول جمع‌آوری داده‌های توییتر از طریق TwitterAPI.io است.

#### مدل‌های داده
- **TwitterUser**: کاربران توییتر با اطلاعات پروفایل و امتیاز تأثیرگذاری
- **Tweet**: توییت‌ها با متن، امتیازها و متادیتا
- **SearchQuery**: کوئری‌های جستجو برای جمع‌آوری خودکار توییت‌ها

#### سرویس‌ها
- **TwitterCollectorService**: جمع‌آوری توییت‌ها از TwitterAPI.io
  - `collect_from_query(query)`: جمع‌آوری توییت‌ها براساس یک کوئری جستجو
  - `_process_tweet_from_model(tweet_model)`: پردازش توییت دریافتی از API
  - `_get_or_create_user_from_model(user_model)`: دریافت یا ایجاد کاربر
  - `get_api_status()`: دریافت وضعیت API

#### وظایف Celery
- **collect_new_tweets**: جمع‌آوری توییت‌های جدید براساس کوئری‌های فعال
- **collect_user_tweets**: جمع‌آوری توییت‌های یک کاربر خاص
- **update_api_usage_statistics**: به‌روزرسانی آمار استفاده از API

#### دستورات مدیریتی
- **twitter_api**: مدیریت TwitterAPI.io و نمایش آمار مصرف
  - `status`: نمایش وضعیت API
  - `report`: تولید گزارش مصرف
  - `cache`: مدیریت کش
  - `test`: تست اتصال به API

### ماژول news

مسئول جمع‌آوری اخبار از منابع RSS است.

#### مدل‌های داده
- **NewsSource**: منابع خبری با آدرس‌های RSS
- **NewsArticle**: مقالات خبری با محتوا و متادیتا

#### سرویس‌ها
- **NewsCollectorService**: جمع‌آوری اخبار از منابع RSS
  - `collect_from_source(source)`: جمع‌آوری اخبار از یک منبع
  - `_process_entry(entry, source)`: پردازش یک ورودی RSS

#### وظایف Celery
- **collect_news**: جمع‌آوری اخبار از منابع فعال

### ماژول processor

مسئول پردازش و فیلترینگ داده‌های جمع‌آوری شده است.

#### سرویس‌ها
- **TweetFilterService**: فیلترینگ و پیش‌پردازش توییت‌ها
  - `filter_tweet(tweet)`: فیلتر یک توییت براساس قواعد
  - `filter_new_tweets(hours)`: فیلتر توییت‌های جدید
  - `extract_entities(tweet)`: استخراج هشتگ‌ها، منشن‌ها و کلمات کلیدی
  - `_contains_inappropriate_content(text)`: بررسی محتوای نامناسب
  - `_is_duplicate(tweet)`: بررسی تکراری بودن توییت
  - `_is_spam(tweet)`: بررسی اسپم بودن توییت

#### وظایف Celery
- **filter_new_tweets**: فیلتر توییت‌های جدید از ساعات اخیر
- **process_tweet**: پردازش یک توییت خاص

### ماژول analyzer

مسئول تحلیل محتوا و احساسات داده‌ها است.

#### مدل‌های داده
- **SentimentAnalysis**: نتایج تحلیل احساسات توییت‌ها و اخبار
- **Pattern**: الگوهای شناسایی شده در داده‌ها

#### سرویس‌ها
- **SentimentAnalyzer**: تحلیل احساسات توییت‌ها و اخبار
  - `analyze_tweet(tweet)`: تحلیل احساسات یک توییت
  - `analyze_recent_tweets(hours)`: تحلیل توییت‌های اخیر

#### وظایف Celery
- **analyze_recent_tweets**: تحلیل توییت‌های اخیر

### ماژول memory

مسئول مدیریت حافظه و تاریخچه سیستم است.

#### مدل‌های داده
- **Topic**: موضوعات و دسته‌بندی‌های محتوا
- **UserRelationship**: روابط بین کاربران
- **MemoryRecord**: رکوردهای حافظه در سطوح زمانی مختلف

### ماژول lib/twitter_api

کتابخانه سفارشی برای ارتباط با TwitterAPI.io است.

#### کلاس‌های اصلی
- **TwitterAPIClient**: کلاینت اصلی برای ارتباط با API
- **TwitterAPIBase**: کلاس پایه برای مدیریت درخواست‌ها و خطاها
- **OptimizedTwitterAPIClient**: کلاینت بهینه‌شده با مدیریت هزینه و کش
- **TwitterAPIBudget**: مدیریت بودجه API
- **TwitterAPICache**: کش‌کردن درخواست‌های API
- **RateLimiter**: کنترل نرخ درخواست‌ها

#### مدل‌های داده
- **Tweet**: مدل داده توییت
- **User**: مدل داده کاربر
- **WebhookRule**: مدل داده قوانین وبهوک

## 7. وابستگی‌ها و نصب

### وابستگی‌های اصلی

```
Django>=5.2
celery>=5.3.4
redis>=4.6.0
requests>=2.31.0
feedparser>=6.0.10
pytz>=2024.1
```

### وابستگی‌های اختیاری

```
django-cors-headers>=4.3.0
djangorestframework>=3.14.0
python-telegram-bot>=20.6
```

### نصب وابستگی‌ها

1. **نصب پایتون**: نیاز به پایتون 3.10 یا بالاتر دارد
   ```bash
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3.10-dev
   ```

2. **ایجاد محیط مجازی**:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

3. **نصب وابستگی‌ها**:
   ```bash
   pip install -r requirements.txt
   ```

4. **نصب Redis**:
   ```bash
   sudo apt install redis-server
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

### تنظیمات API‌های خارجی

برای استفاده از پروژه، نیاز به کلیدهای API زیر دارید:

1. **TwitterAPI.io API Key**: برای دسترسی به داده‌های توییتر
2. **Claude API Key**: برای تحلیل هوشمند محتوا
3. **Grok API Key**: برای تحلیل احساسات
4. **Telegram Bot Token**: برای ارسال گزارش‌ها و هشدارها

این کلیدها باید در فایل `core/settings_local.py` تنظیم شوند:

```python
# core/settings_local.py
TWITTER_API_KEY = 'your_twitter_api_key'
CLAUDE_API_KEY = 'your_claude_api_key'
GROK_API_KEY = 'your_grok_api_key'
TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token'

# تنظیمات بودجه TwitterAPI.io
TWITTER_API_DAILY_BUDGET_USD = 0.5
TWITTER_API_CACHE_ENABLED = True
TWITTER_API_CACHE_DIR = '.twitter_cache'
```

## 8. راه‌اندازی و اجرا

### آماده‌سازی دیتابیس

```bash
# اجرای مهاجرت‌های دیتابیس
python manage.py migrate

# ایجاد کاربر مدیر
python manage.py createsuperuser
```

### اجرای سرور توسعه

```bash
# اجرای سرور جنگو
python manage.py runserver
```

### راه‌اندازی Celery

```bash
# اجرای کارگر Celery
celery -A core worker -l info

# اجرای زمان‌بندی Celery
celery -A core beat -l info
```

### دستورات مدیریتی مفید

```bash
# بررسی وضعیت TwitterAPI.io
python manage.py twitter_api status

# تولید گزارش مصرف TwitterAPI.io
python manage.py twitter_api report --days 7

# مدیریت کش TwitterAPI.io
python manage.py twitter_api cache status
python manage.py twitter_api cache clear

# تست اتصال به TwitterAPI.io
python manage.py twitter_api test --query "هوش مصنوعی lang:fa" --count 5
```

### تنظیمات کوئری‌های جستجو

برای تنظیم کوئری‌های جستجو برای جمع‌آوری خودکار توییت‌ها، از پنل مدیریت استفاده کنید:

1. به آدرس `http://localhost:8000/admin/` وارد شوید
2. به بخش `Collector > Search Queries` بروید
3. دکمه "Add Search Query" را کلیک کنید
4. فرم را با مقادیر مناسب پر کنید:
   - Query: عبارت جستجو (مثل "هوش مصنوعی lang:fa")
   - Priority: اولویت (high, medium, low)
   - Result Type: نوع نتایج (recent, popular, mixed)
   - Schedule Interval: فاصله زمانی به دقیقه (مثلاً 60 برای هر ساعت)

## 9. راهنمای توسعه‌دهندگان

### افزودن ماژول جدید

1. **ایجاد ماژول جدید**:
   ```bash
   python manage.py startapp new_module
   ```

2. **ثبت ماژول در تنظیمات**:
   ```python
   # core/settings.py
   INSTALLED_APPS = [
       # ...
       'new_module',
   ]
   ```

3. **ساختار توصیه شده**:
   - `models.py`: تعریف مدل‌های داده
   - `services.py`: پیاده‌سازی منطق کسب‌وکار
   - `tasks.py`: تعریف وظایف Celery
   - `admin.py`: ثبت مدل‌ها در پنل مدیریت

### افزودن API جدید

1. **ایجاد نقاط پایانی در `api/urls.py`**:
   ```python
   from django.urls import path
   from api.views import MyNewAPIView

   urlpatterns = [
       path('my-endpoint/', MyNewAPIView.as_view(), name='my-endpoint'),
   ]
   ```

2. **ایجاد سریالایزر در `api/serializers.py`**:
   ```python
   from rest_framework import serializers
   from my_app.models import MyModel

   class MyModelSerializer(serializers.ModelSerializer):
       class Meta:
           model = MyModel
           fields = ['id', 'field1', 'field2']
   ```

3. **ایجاد ویو در `api/views.py`**:
   ```python
   from rest_framework import generics
   from my_app.models import MyModel
   from api.serializers import MyModelSerializer

   class MyNewAPIView(generics.ListCreateAPIView):
       queryset = MyModel.objects.all()
       serializer_class = MyModelSerializer
   ```

### افزودن وظیفه Celery جدید

1. **ایجاد وظیفه در `your_module/tasks.py`**:
   ```python
   from celery import shared_task
   import logging

   logger = logging.getLogger(__name__)

   @shared_task
   def my_new_task():
       try:
           # منطق وظیفه
           logger.info("وظیفه جدید با موفقیت اجرا شد")
           return {'status': 'success'}
       except Exception as e:
           logger.error(f"خطا در اجرای وظیفه جدید: {str(e)}")
           return {'status': 'error', 'error': str(e)}
   ```

2. **ثبت وظیفه در زمان‌بندی Celery (اختیاری)**:
   ```python
   # core/celery.py
   app.conf.beat_schedule = {
       # ...
       'my-new-task-hourly': {
           'task': 'your_module.tasks.my_new_task',
           'schedule': crontab(minute='0'),  # هر ساعت اجرا می‌شود
       },
   }
   ```

### اتصال به API‌های هوش مصنوعی

1. **ایجاد کلاس سرویس برای API**:
   ```python
   class AIService:
       def __init__(self, api_key=None):
           self.api_key = api_key or settings.AI_API_KEY
           
       def analyze_text(self, text):
           # ارسال درخواست به API
           # پردازش پاسخ
           return result
   ```

2. **استفاده از سرویس در وظایف Celery**:
   ```python
   @shared_task
   def analyze_with_ai(text_id):
       try:
           text_obj = Text.objects.get(id=text_id)
           service = AIService()
           result = service.analyze_text(text_obj.content)
           
           # ذخیره نتیجه تحلیل
           TextAnalysis.objects.create(
               text=text_obj,
               result=result
           )
           return {'status': 'success'}
       except Exception as e:
           return {'status': 'error', 'error': str(e)}
   ```

### بهینه‌سازی کارایی

1. **استفاده از query_set‌های بهینه**:
   ```python
   # به جای
   my_objects = MyModel.objects.all()
   for obj in my_objects:
       related = obj.related_set.all()  # N+1 query problem
       
   # استفاده از
   my_objects = MyModel.objects.prefetch_related('related_set').all()
   ```

2. **استفاده از عملیات دسته‌ای**:
   ```python
   # به جای
   for item in items:
       MyModel.objects.create(field=item)
       
   # استفاده از
   MyModel.objects.bulk_create([
       MyModel(field=item) for item in items
   ])
   ```

3. **استفاده از تراکنش‌ها برای عملیات پیچیده**:
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       # عملیات متعدد دیتابیس
       obj1.save()
       obj2.save()
       obj3.delete()
   ```

### گسترش کتابخانه TwitterAPI.io

1. **افزودن قابلیت جدید به کلاینت**:
   ```python
   # lib/twitter_api/client.py
   class TwitterAPIClient:
       # ...
       def my_new_method(self, param1, param2):
           """
           توضیحات متد جدید
           
           Args:
               param1: توضیح اولین پارامتر
               param2: توضیح دومین پارامتر
               
           Returns:
               توضیح خروجی متد
           """
           # پیاده‌سازی متد
           return self.base.make_request("GET", "path/to/endpoint", params={
               "param1": param1,
               "param2": param2
           })
   ```

2. **افزودن متد بهینه‌شده به کلاینت بهینه‌سازی شده**:
   ```python
   # lib/twitter_api/middleware/client.py
   class OptimizedTwitterAPIClient:
       # ...
       def my_new_optimized_method(self, param1, param2):
           """
           نسخه بهینه‌شده متد جدید
           """
           # بررسی بودجه
           if not self.check_can_afford('path/to/endpoint'):
               raise Exception("بودجه ناکافی")
               
           # فراخوانی متد اصلی با محدودیت‌ها
           return self.client.my_new_method(param1, param2)
   ```

### پیشنهادات برای توسعه آینده

1. **پیاده‌سازی API کامل**:
   - تعریف نقاط پایانی در `api/urls.py`
   - پیاده‌سازی سریالایزرها در `api/serializers.py`
   - پیاده‌سازی ویوها در `api/views.py`

2. **افزودن احراز هویت به API**:
   - پیاده‌سازی سیستم احراز هویت توکن
   - تعریف سطوح دسترسی مختلف کاربران

3. **توسعه ربات تلگرام**:
   - ایجاد ماژول `telegram_bot`
   - پیاده‌سازی ارسال گزارش‌ها و هشدارها
   - امکان درخواست اطلاعات از طریق ربات

4. **ایجاد داشبورد وب**:
   - توسعه رابط کاربری وب با فریم‌ورک فرانت‌اند
   - نمایش گراف‌ها و نمودارهای تحلیلی
   - امکان مدیریت سیستم از طریق داشبورد

5. **ارتقاء سیستم حافظه**:
   - پیاده‌سازی الگوریتم‌های پیشرفته خلاصه‌سازی
   - استفاده از تکنیک‌های vector embedding برای جستجوی معنایی
   - بهینه‌سازی استفاده از توکن در تعامل با Claude و Grok