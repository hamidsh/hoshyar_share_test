"""
نمونه کاربردی کتابخانه TwitterAPI.io که نشان می‌دهد چگونه از آن استفاده کنیم.
"""

from lib.twitter_api import TwitterAPIClient

# کلید API را از متغیرهای محیطی بخوانید یا به صورت مستقیم وارد کنید
API_KEY = "your_api_key_here"

def print_separator(title):
    """نمایش جداکننده با عنوان برای خوانایی بهتر خروجی"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def search_tweets_example():
    """نمونه‌ای از جستجوی توییت‌ها"""
    print_separator("جستجوی توییت‌ها")

    client = TwitterAPIClient(API_KEY)

    try:
        # جستجوی توییت‌ها با کلمات کلیدی به زبان فارسی
        tweets = client.search_tweets(
            query="برنامه‌نویسی OR هوش‌مصنوعی lang:fa",
            query_type="Latest",
            max_results=3
        )

        print(f"تعداد {len(tweets)} توییت یافت شد:")

        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- توییت {i} ---")
            print(f"شناسه: {tweet.id}")
            print(f"نویسنده: @{tweet.author.username if tweet.author else 'ناشناس'}")
            print(f"متن: {tweet.text}")
            print(f"تاریخ: {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"بازتوییت: {tweet.retweet_count}, لایک: {tweet.like_count}, پاسخ: {tweet.reply_count}")

    except Exception as e:
        print(f"خطا: {str(e)}")

def get_user_info_example():
    """نمونه‌ای از دریافت اطلاعات کاربر"""
    print_separator("اطلاعات کاربر")

    client = TwitterAPIClient(API_KEY)

    try:
        # دریافت اطلاعات یک کاربر مشهور
        user = client.get_user_info("elonmusk")

        print(f"شناسه: {user.id}")
        print(f"نام کاربری: @{user.username}")
        print(f"نام: {user.name}")
        print(f"توضیحات: {user.description}")
        print(f"موقعیت: {user.location}")
        print(f"تأیید شده: {user.is_blue_verified}")
        print(f"دنبال‌کنندگان: {user.followers_count}, دنبال‌شده‌ها: {user.following_count}")
        print(f"تاریخ ایجاد: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'نامشخص'}")

    except Exception as e:
        print(f"خطا: {str(e)}")

def get_user_followers_example():
    """نمونه‌ای از دریافت دنبال‌کنندگان کاربر"""
    print_separator("دنبال‌کنندگان کاربر")

    client = TwitterAPIClient(API_KEY)

    try:
        # دریافت دنبال‌کنندگان یک کاربر مشهور
        followers = client.get_user_followers(
            username="elonmusk",
            max_results=3
        )

        print(f"تعداد {len(followers)} دنبال‌کننده یافت شد:")

        for i, user in enumerate(followers, 1):
            print(f"\n--- دنبال‌کننده {i} ---")
            print(f"شناسه: {user.id}")
            print(f"نام کاربری: @{user.username or 'بدون نام کاربری'}")
            print(f"نام: {user.name}")
            print(f"دنبال‌کنندگان: {user.followers_count}, دنبال‌شده‌ها: {user.following_count}")

    except Exception as e:
        print(f"خطا: {str(e)}")

def get_user_tweets_example():
    """نمونه‌ای از دریافت توییت‌های کاربر"""
    print_separator("توییت‌های کاربر")

    client = TwitterAPIClient(API_KEY)

    try:
        # دریافت توییت‌های یک کاربر
        tweets = client.get_user_tweets(
            username="elonmusk",
            max_results=3
        )

        print(f"تعداد {len(tweets)} توییت یافت شد:")

        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- توییت {i} ---")
            print(f"شناسه: {tweet.id}")
            print(f"متن: {tweet.text}")
            print(f"تاریخ: {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"بازتوییت: {tweet.retweet_count}, لایک: {tweet.like_count}")

        # توضیح در مورد نتایج خالی
        if not tweets:
            print("\nتوجه: این API توییت‌های پاسخ را برنمی‌گرداند. اگر کاربر اخیراً فقط پاسخ داده باشد، نتیجه خالی خواهد بود.")
            print("برای دریافت پاسخ‌ها، از جستجوی پیشرفته با کوئری «from:username is:reply» استفاده کنید.")

    except Exception as e:
        print(f"خطا: {str(e)}")

        # استفاده از گزینه جایگزین
        try:
            print("\nتلاش با استفاده از جستجوی پیشرفته برای توییت‌های اخیر:")

            # استفاده از جستجو به جای API user/last_tweets
            search_tweets = client.search_tweets(
                query=f"from:{(username or user_id)} -filter:replies -filter:retweets",
                query_type="Latest",
                max_results=3
            )

            print(f"تعداد {len(search_tweets)} توییت یافت شد:")

            for i, tweet in enumerate(search_tweets, 1):
                print(f"\n--- توییت {i} ---")
                print(f"شناسه: {tweet.id}")
                print(f"متن: {tweet.text}")
                print(f"تاریخ: {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"بازتوییت: {tweet.retweet_count}, لایک: {tweet.like_count}")

        except Exception as search_error:
            print(f"خطا در جستجوی پیشرفته: {str(search_error)}")

def get_tweet_replies_example():
    """نمونه‌ای از دریافت پاسخ‌های یک توییت"""
    print_separator("پاسخ‌های توییت")

    client = TwitterAPIClient(API_KEY)

    try:
        # دریافت پاسخ‌های یک توییت
        # توجه: باید شناسه یک توییت اصلی (نه پاسخ) را وارد کنید
        tweet_id = "1593606720771178496"  # شناسه نمونه - با یک شناسه واقعی جایگزین کنید

        replies = client.get_tweet_replies(
            tweet_id=tweet_id,
            max_results=3
        )

        print(f"تعداد {len(replies)} پاسخ یافت شد:")

        for i, tweet in enumerate(replies, 1):
            print(f"\n--- پاسخ {i} ---")
            print(f"شناسه: {tweet.id}")
            print(f"نویسنده: @{tweet.author.username if tweet.author else 'ناشناس'}")
            print(f"متن: {tweet.text}")
            print(f"تاریخ: {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # توضیح در مورد نتایج خالی
        if not replies:
            print("\nتوجه: ممکن است این توییت پاسخی نداشته باشد یا API در بازیابی پاسخ‌ها با مشکل مواجه شده باشد.")
            print("فقط توییت‌های اصلی (نه پاسخ‌ها) و اولین توییت در یک رشته پشتیبانی می‌شوند.")

    except Exception as e:
        print(f"خطا: {str(e)}")

def advanced_search_example():
    """نمونه‌ای از جستجوی پیشرفته"""
    print_separator("جستجوی پیشرفته")

    client = TwitterAPIClient(API_KEY)

    try:
        # جستجوی پیشرفته با ترکیبی از عملگرها
        query = 'from:elonmusk -filter:replies -filter:retweets'

        tweets = client.search_tweets(
            query=query,
            query_type="Latest",
            max_results=3
        )

        print(f"جستجوی: {query}")
        print(f"تعداد {len(tweets)} توییت یافت شد:")

        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- نتیجه {i} ---")
            print(f"شناسه: {tweet.id}")
            print(f"متن: {tweet.text}")
            print(f"لایک: {tweet.like_count}, بازتوییت: {tweet.retweet_count}")

            # نمایش لینک‌ها
            if tweet.urls:
                print("لینک‌ها:")
                for url in tweet.urls:
                    print(f"  {url.expanded_url}")

    except Exception as e:
        print(f"خطا: {str(e)}")

def using_iterator_example():
    """نمونه‌ای از استفاده از ایتریتور برای صرفه‌جویی در حافظه"""
    print_separator("استفاده از ایتریتور")

    client = TwitterAPIClient(API_KEY)

    try:
        # استفاده از ایتریتور برای دریافت نتایج به صورت تدریجی
        tweets_iter = client.search_tweets_iter(
            query="اخبار lang:fa",
            query_type="Latest"
        )

        print("پیمایش نتایج با استفاده از ایتریتور:")

        for i, tweet in enumerate(tweets_iter, 1):
            print(f"\n--- توییت {i} ---")
            print(f"شناسه: {tweet.id}")
            print(f"نویسنده: @{tweet.author.username if tweet.author else 'ناشناس'}")

            # نمایش خلاصه متن
            if len(tweet.text) > 100:
                print(f"متن: {tweet.text[:100]}...")
            else:
                print(f"متن: {tweet.text}")

            # فقط 3 توییت اول را نمایش می‌دهیم
            if i >= 3:
                break

    except Exception as e:
        print(f"خطا: {str(e)}")

def main():
    """اجرای تمام نمونه‌ها"""
    try:
        search_tweets_example()
        get_user_info_example()
        get_user_followers_example()
        get_user_tweets_example()
        get_tweet_replies_example()
        advanced_search_example()
        using_iterator_example()

    except Exception as e:
        print(f"خطای غیرمنتظره: {str(e)}")

if __name__ == "__main__":
    main()