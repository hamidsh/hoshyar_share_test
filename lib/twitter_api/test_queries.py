"""
Test script for TwitterAPI.io query operators with detailed validation.
"""

import logging
from lib.twitter_api import TwitterAPIClient

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("query_test")

# کلید API
API_KEY = "cf5800d7a52a4df89b5df7ffe1c7303d"

# لیست کوئری‌ها
QUERIES = [
    "lang:fa since:2023-01-01",
    "lang:fa until:2023-12-31",
    "lang:fa since:2023-01-01 until:2023-01-02",
    "lang:fa since:2023-01-01_12:00:00_UTC until:2023-01-01_14:00:00_UTC",
    "lang:fa since_time:1672531200",
    "lang:fa until_time:1704067200",
    "lang:fa since_time:1672531200 until_time:1672617600",
    "lang:fa within_time:7d",
    "from:elonmusk lang:en",
    "from:elonmusk to:tesla lang:en",
    "@elonmusk lang:en",
    "هوش مصنوعی lang:fa -filter:nativeretweets",
    "هوش مصنوعی lang:fa filter:nativeretweets",
    "هوش مصنوعی lang:fa -filter:replies",
    "هوش مصنوعی lang:fa filter:replies",
    "هوش مصنوعی lang:fa -filter:media",
    "هوش مصنوعی lang:fa filter:media",
    "تحلیل lang:fa min_faves:10",
    "تحلیل lang:fa -min_retweets:50",
    "from:elonmusk since:2023-01-01 -filter:replies lang:en",
    "هوش مصنوعی lang:fa filter:media since_time:1672531200",
]

def test_query(client, query):
    """تست کوئری با اعتبارسنجی فیلترها."""
    try:
        logger.info(f"Testing query: {query}")
        tweets = client.search_tweets(query, max_results=5)
        logger.info(f"Found {len(tweets)} tweets for query: {query}")

        if tweets:
            # لاگ کردن جزئیات اولین توییت برای اعتبارسنجی
            tweet = tweets[0]
            logger.info(f"Sample tweet details:")
            logger.info(f"  Text: {tweet.text}")
            logger.info(f"  Created_at: {tweet.created_at}")
            logger.info(f"  Is_reply: {tweet.is_reply}")
            logger.info(f"  Retweet_count: {tweet.retweet_count}")
            logger.info(f"  Has_media: {'extendedEntities' in tweet.raw_data if tweet.raw_data else False}")
            logger.info(f"  Like_count: {tweet.like_count}")
            logger.info(f"  Raw_data: {tweet.raw_data}")
    except Exception as e:
        logger.error(f"Failed for query: {query} - Error: {str(e)}")

def main():
    """اجرای تست‌ها."""
    client = TwitterAPIClient(API_KEY)
    for query in QUERIES:
        test_query(client, query)
        logger.info("-" * 50)

if __name__ == "__main__":
    main()