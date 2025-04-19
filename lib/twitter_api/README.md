
---

# مستندات کتابخانه `twitter_api` (نسخه ناپایدار - در حال توسعه)

## مقدمه
این کتابخانه برای اتصال به **TwitterAPI.io** (نه API رسمی توییتر) طراحی شده و هدفش مدیریت چالش‌های این API و ارائه رابطی ساده برای پروژه **هوشیار** است که روی تحلیل احساسات توییت‌های فارسی تمرکز داره.

> **اخطار**: این نسخه **ناپایدار** و در **حالت توسعه و تست** است. باگ‌ها، تغییرات ساختاری، یا اضافه شدن امکانات ممکنه اتفاق بیفته. این یه ابزار عمومی نیست و برای نیازهای خاص هوشیار ساخته شده.

## ساختار پروژه
- `lib/twitter_api/`
  - `base.py`: درخواست‌های HTTP و مدیریت خطا.
  - `client.py`: متدهای سطح بالا.
  - `exceptions.py`: استثناهای سفارشی.
  - `models/`: مدل‌ها (`Tweet`, `User`, `WebhookRule`).
  - `utils/`: ابزارهای کمکی.

## امکانات
### متدهای اصلی (`TwitterAPIClient`)
1. **جستجوی توییت‌ها**:
   - `search_tweets(query, query_type="Latest")`
   - `search_tweets_iter(...)`
2. **پاسخ‌ها**:
   - `get_tweet_replies(tweet_id)`
   - `get_tweet_replies_iter(...)`
3. **کاربر**:
   - `get_user_info(username)`
   - `get_user_info_by_id(user_id)`
   - `get_user_tweets(username=None, user_id=None)`
   - `get_user_followers(username)`
   - `get_user_following(username)`
   - `get_users_by_ids(user_ids)`
4. **لیست و وب‌هوک**:
   - `get_list_tweets(list_id)`
   - `get_webhook_rules()`, `add_webhook_rule()`, ...

### فیلدها
#### `Tweet`:
- **اصلی**: `id`, `text`, `created_at`, `retweet_count`.
- **اختیاری**: `view_count`, `url`, `is_reply`.
- **روابط**: `author`, `quoted_tweet`.

#### `User`:
- **اصلی**: `id`, `username`, `name`.
- **پروفایل**: `profile_picture`, `description`.
- **آمار**: `followers_count`, `tweet_count`.

#### `WebhookRule`:
- **اصلی**: `tag`, `value`, `interval_seconds`.

## نحوه استفاده
### نصب
- پایتون 3.11 و `requests` نیازه:
  ```bash
  pip install requests
  ```

### مثال‌ها
#### جستجو
```python
from lib.twitter_api import TwitterAPIClient
client = TwitterAPIClient("your_api_key")
tweets = client.search_tweets("برنامه‌نویسی lang:fa", max_results=5)
for tweet in tweets:
    print(tweet.text)
```

#### اطلاعات کاربر
```python
user = client.get_user_info("elonmusk")
print(user.name)
```

## بخش کوئری‌ها
### توضیحات
متد `search_tweets` از `twitter/tweet/advanced_search` استفاده می‌کنه و پارامتر `query` رو می‌پذیره. TwitterAPI.io ادعا می‌کنه از جستجوی پیشرفته پشتیبانی می‌کنه، ولی تست‌ها نشون دادن که همه عملگرها به طور کامل یا درست کار نمی‌کنن.

### عملگرهای تست‌شده (تا ۹ آوریل ۲۰۲۵)
تست‌ها با اسکریپت `test_queries.py` انجام شدن:

#### فیلترهای تاریخ
- **`since:YYYY-MM-DD`**: ✅ توییت‌ها از تاریخ مشخص به بعد.
- **`until:YYYY-MM-DD`**: ✅ توییت‌ها قبل از تاریخ مشخص (غیرشامل).
- **`since:YYYY-MM-DD until:YYYY-MM-DD`**: ✅ بازه تاریخ.
- **`since:YYYY-MM-DD_HH:MM:SS_UTC until:YYYY-MM-DD_HH:MM:SS_UTC`**: ✅ با دقت ساعت و ثانیه.
- **`since_time:timestamp`**: ✅ از Unix Timestamp شروع.
- **`until_time:timestamp`**: ✅ تا Unix Timestamp مشخص.
- **`since_time:timestamp until_time:timestamp`**: ✅ بازه Unix Timestamp.
- **`within_time:Xd`**: ✅ توییت‌های X روز اخیر.

#### فیلترهای کاربران
- **`from:user`**: ✅ توییت‌ها از کاربر خاص.
- **`from:user to:user`**: ✅ توییت‌ها از یه کاربر به کاربر دیگه.
- **`@user`**: ✅ توییت‌هایی که کاربر رو منشن کردن.

#### فیلترهای نوع توییت
- **`-filter:nativeretweets`**: ✅ ریتوییت‌ها رو حذف می‌کنه.
- **`filter:nativeretweets`**: ✅ فقط ریتوییت‌ها.
- **`-filter:replies`**: ✅ پاسخ‌ها رو حذف می‌کنه.
- **`filter:replies`**: ✅ فقط پاسخ‌ها.
- **`-filter:media`**: ❌ کار نمی‌کنه (توییت با مدیا برگردوند).
- **`filter:media`**: ✅ فقط توییت‌های با مدیا.

#### فیلترهای تعامل
- **`min_faves:N`**: ✅ حداقل N لایک.
- **`-min_retweets:N`**: ✅ کمتر از N ریتوییت.

#### ترکیبات
- **`from:elonmusk since:2023-01-01 -filter:replies lang:en`**: ✅ درست کار کرد.
- **`هوش مصنوعی lang:fa filter:media since_time:1672531200`**: ✅ درست کار کرد.

### عملگرهای تست‌نشده
- **`filter:images`, `filter:videos`, `filter:links`**: احتمالاً کار می‌کنن.
- **`min_replies:N`, `-min_faves:N`**: ممکنه مثل `min_faves` باشن.
- **`near:city`, `geocode:lat,long,radius`**: بعید به نظر میاد پشتیبانی بشن.
- **`conversation_id:tweet_id`**: برای مکالمات.

### چالش‌ها
- **پشتیبانی ناقص**: `-filter:media` مشکل داره.
- **مستندات مبهم**: لیست دقیق عملگرها مشخص نیست.
- **نتایج تکراری**: توییت‌ها توی چند کوئری تکرار شدن.

### نتایج تست فعلی (۹ آوریل ۲۰۲۵)
- **موفقیت**: ۲۰ از ۲۱ کوئری درست کار کردن.
- **شکست**: `-filter:media` توییت با مدیا برگردوند.
- **مشکوک**: `Has_media: True` با `extendedEntities` خالی (نیاز به بررسی مدل `Tweet`).

## مدیریت هزینه
TwitterAPI.io از مدل **Pay-As-You-Go** استفاده می‌کنه. هزینه‌ها بر اساس تعداد درخواست‌ها و نوع داده محاسبه می‌شن:

### نرخ پایه
- **توییت‌ها**: `$0.15 / 1000 توییت`.
- **پروفایل کاربران**: `$0.18 / 1000 پروفایل`.
- **دنبال‌کننده‌ها**: `$0.15 / 1000 دنبال‌کننده`.

### حداقل هزینه
- **هر درخواست**: `$0.00015` (حتی اگه داده‌ای برنگرده).

### اعتبار اولیه
- **ثبت‌نام**: `$1 اعتبار رایگان` برای تست.

### بدون اشتراک
- هزینه ماهانه یا تعهد اولیه وجود نداره.

### تخفیف
- **دانشجویان و تحقیقات**: نرخ‌های تخفیفی (جزئیات با تماس).

### مثال محاسبه هزینه
- ۵۰۰۰ توییت: `5000 / 1000 * $0.15 = $0.75`.
- ۲۰۰۰ پروفایل: `2000 / 1000 * $0.18 = $0.36`.
- ۱۰ درخواست خالی: `10 * $0.00015 = $0.0015`.
- **مجموع**: `$1.1115`.

### نکات مهم
- **عملکرد**: ~800ms پاسخ، ۱۰۰۰+ QPS.
- **پایداری**: ۹۹.۹۹٪ آپ‌تایم، ۲M+ درخواست ماهانه.
- **پشتیبانی**: ۲۴/۷.
- **Webhook/WebSocket**: برای داده real-time.

## چالش‌های API
- **ساختار متغیر**: تابع `_normalize_response` مدیریت می‌کنه.
- **پاسخ ناقص**: با `stop_on_empty` هندل شده.

## نکات توسعه
- **ناپایداری**: نسخه در حال توسعه‌ست.
- **تحلیل جدا**: مدل‌های تحلیل توی `features/` بسازید.

## محدودیت‌ها
- `-filter:media` قابل اعتماد نیست.
- خطاهای غیرمنتظره ممکنه پیش بیاد.

---
