"""
فایل عیب‌یابی برای بررسی پاسخ‌های خام TwitterAPI.io
"""

import requests

# API کلید برای اتصال به سرویس
API_KEY = "cf5800d7a52a4df89b5df7ffe1c7303d"

# تنظیمات درخواست
BASE_URL = "https://api.twitterapi.io"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def print_separator(title):
    """نمایش جداکننده با عنوان برای خوانایی بهتر خروجی"""
    sep_line = "=" * 80
    print(f"\n{sep_line}")
    print(f"  {title}")
    print(f"{sep_line}\n")

def make_request(endpoint, params=None):
    """ارسال درخواست به API و بازگرداندن پاسخ خام"""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)

    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")

    try:
        return response.json()
    except ValueError:
        return {"error": "Invalid JSON response", "text": response.text}

def debug_search_tweets():
    """دیباگ جستجوی توییت‌ها"""
    print_separator("DEBUG SEARCH TWEETS")

    params = {
        "query": "برنامه‌نویسی OR هوش‌مصنوعی lang:fa",
        "queryType": "Latest",
        "cursor": ""
    }

    response = make_request("twitter/tweet/advanced_search", params)

    # بررسی ساختار پاسخ
    print("Response Structure Keys:", list(response.keys()))

    # نمایش تعداد توییت‌ها
    tweets = response.get("tweets", [])
    print(f"Number of tweets: {len(tweets)}")

    # نمایش اطلاعات پاگینیشن
    print(f"has_next_page: {response.get('has_next_page')}")
    print(f"next_cursor: {response.get('next_cursor', '')}")

    # نمایش نمونه اولین توییت (اگر وجود داشته باشد)
    if tweets:
        print("\nSample Tweet Structure Keys:", list(tweets[0].keys()))
        print("\nSample Tweet Author Structure Keys:", list(tweets[0].get("author", {}).keys()))

def debug_user_tweets():
    """دیباگ دریافت توییت‌های کاربر"""
    print_separator("DEBUG USER TWEETS")

    # امتحان با چند کاربر مختلف
    usernames = ["cmartin380", "elonmusk", "BarackObama"]

    for username in usernames:
        print(f"\nChecking tweets for user: {username}")

        params = {
            "userName": username,
            "cursor": ""
        }

        response = make_request("twitter/user/last_tweets", params)

        # بررسی ساختار پاسخ
        print("Response Structure Keys:", list(response.keys()))

        # نمایش تعداد توییت‌ها - نکته: data می‌تواند دیکشنری یا لیست باشد
        data = response.get("data", [])
        tweets = []

        if isinstance(data, dict):
            # اگر یک دیکشنری باشد و خالی نباشد، آن را در یک لیست قرار می‌دهیم
            if data:
                tweets = [data]
                print("NOTE: Data is a dictionary, not a list!")
        elif isinstance(data, list):
            tweets = data

        print(f"Number of tweets: {len(tweets)}")
        print(f"Data type: {type(data).__name__}")

        # نمایش کد وضعیت و پیام
        print(f"Status: {response.get('status')}")
        print(f"Message: {response.get('msg', '')}")

        # پاگینیشن
        print(f"has_next_page: {response.get('has_next_page')}")
        print(f"next_cursor: {response.get('next_cursor', '')}")

        # فقط یک کاربر را بررسی کن اگر نتیجه داشت
        if tweets:
            print("\nSample Tweet Structure Keys:", list(tweets[0].keys()))
            break

def debug_tweet_replies():
    """دیباگ دریافت پاسخ‌های توییت"""
    print_separator("DEBUG TWEET REPLIES")

    # امتحان با چند توییت مختلف - توجه: باید توییت‌های اصلی (نه پاسخ) باشند
    tweet_ids = ["1909313772080255415", "1895364161032556732", "1894154866559164582"]

    for tweet_id in tweet_ids:
        print(f"\nChecking replies for tweet: {tweet_id}")

        params = {
            "tweetId": tweet_id,
            "cursor": ""
        }

        response = make_request("twitter/tweet/replies", params)

        # بررسی ساختار پاسخ
        print("Response Structure Keys:", list(response.keys()))

        # نمایش تعداد پاسخ‌ها - نکته: پاسخ‌ها در فیلد "tweets" قرار دارند، نه "replies"
        replies = response.get("tweets", [])
        print(f"Number of replies: {len(replies)}")

        # نمایش کد وضعیت و پیام
        print(f"Status: {response.get('status')}")
        print(f"Message: {response.get('message', '')}")

        # فقط یک توییت را بررسی کن اگر نتیجه داشت
        if replies:
            print("\nSample Reply Structure Keys:", list(replies[0].keys()))
            break

def debug_user_followers():
    """دیباگ دریافت دنبال‌کنندگان کاربر"""
    print_separator("DEBUG USER FOLLOWERS")

    # امتحان با یک کاربر معروف که دنبال‌کنندگان زیادی دارد
    params = {
        "userName": "elonmusk",
        "cursor": ""
    }

    response = make_request("twitter/user/followers", params)

    # بررسی ساختار پاسخ
    print("Response Structure Keys:", list(response.keys()))

    # نمایش تعداد دنبال‌کنندگان
    followers = response.get("followers", [])
    print(f"Number of followers: {len(followers)}")

    # نمایش کد وضعیت و پیام
    print(f"Status: {response.get('status')}")
    print(f"Message: {response.get('message', '')}")

    # نمایش نمونه اولین دنبال‌کننده (اگر وجود داشته باشد)
    if followers:
        print("\nSample Follower Structure Keys:", list(followers[0].keys()))

        # بررسی مقادیر null یا خالی در فیلدهای مهم
        sample_follower = followers[0]
        print("\nSample Follower Values:")
        for key in ["screen_name", "name", "id", "created_at"]:
            print(f"  {key}: {sample_follower.get(key)}")

def debug_get_user_info():
    """دیباگ دریافت اطلاعات کاربر - برای مقایسه با دنبال‌کنندگان"""
    print_separator("DEBUG USER INFO")

    params = {
        "userName": "elonmusk"
    }

    response = make_request("twitter/user/info", params)

    # نمایش ساختار پاسخ
    print("Response Structure Keys:", list(response.keys()))

    # نمایش ساختار اطلاعات کاربر - نکته: اطلاعات کاربر در فیلد "data" قرار دارد، نه "user"
    user = response.get("data", {})
    if user:
        print("\nUser Structure Keys:", list(user.keys()))

        # نمایش مقادیر فیلدهای مهم
        print("\nUser Values:")
        for key in ["screen_name", "name", "id", "created_at"]:
            print(f"  {key}: {user.get(key)}")

def main():
    """اجرای تمام توابع دیباگ"""
    debug_search_tweets()
    debug_user_tweets()
    debug_tweet_replies()
    debug_user_followers()
    debug_get_user_info()

if __name__ == "__main__":
    main()