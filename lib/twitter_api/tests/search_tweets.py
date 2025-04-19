import logging
import sys
from typing import List
from lib.twitter_api.client import TwitterAPIClient
from lib.twitter_api.middleware.client import OptimizedTwitterAPIClient
from lib.twitter_api.models import Tweet

# تنظیم لاگینگ با جزئیات بالا
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_search_tweets(api_key: str, query: str = "from:elonmusk", max_results: int = 100, use_cache: bool = True) -> List[Tweet]:
    """
    Test tweet search with detailed logging to verify result count and pagination.

    Args:
        api_key: TwitterAPI.io API key
        query: Search query
        max_results: Desired number of tweets
        use_cache: Enable or disable cache

    Returns:
        List of retrieved tweets
    """
    logger.info(f"Starting tweet search test: query='{query}', max_results={max_results}, use_cache={use_cache}")

    # مقداردهی اولیه کلاینت
    try:
        client = OptimizedTwitterAPIClient(
            api_key=api_key,
            daily_budget_usd=1.0,
            enable_cache=use_cache,
            cache_dir='.twitter_test_cache',
            default_max_pages=10,
            default_max_results=max_results
        )
        logger.debug("Client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing client: {str(e)}")
        raise

    # تنظیم محدودیت‌ها
    client.set_default_limits(max_pages=10, max_results=max_results)
    logger.debug(f"Limits set: max_pages=10, max_results={max_results}")

    # اجرای جست‌وجو
    try:
        tweets = client.search_tweets(
            query=query,
            query_type="Latest",
            max_results=max_results,
            convert_to_models=True
        )
        logger.info(f"Search completed. Retrieved {len(tweets)} tweets")
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise

    # بررسی نتایج
    if not tweets:
        logger.warning("No tweets retrieved!")
    else:
        for i, tweet in enumerate(tweets[:5], 1):
            logger.debug(f"Tweet {i}: ID={tweet.id}, Text={tweet.text[:50]}...")

    # اعتبارسنجی تعداد
    if len(tweets) < max_results:
        logger.warning(
            f"Retrieved {len(tweets)} tweets, less than requested {max_results}. "
            "Check pagination, cache, or API response."
        )
    elif len(tweets) > max_results:
        logger.warning(
            f"Retrieved {len(tweets)} tweets, more than requested {max_results}. "
            "Check truncation logic."
        )
    else:
        logger.info("Retrieved exact number of requested tweets")

    # بررسی وضعیت کش
    if use_cache:
        cache_stats = client.get_cache_stats()
        logger.info(
            f"Cache stats: hits={cache_stats.get('hits', 0)}, misses={cache_stats.get('misses', 0)}, "
            f"size={cache_stats.get('size_mb', 0):.2f} MB"
        )

    # بررسی وضعیت بودجه
    budget_status = client.get_budget_status()
    logger.info(
        f"Budget stats: spent_today=${budget_status['spent_today_usd']:.4f}, "
        f"remaining=${budget_status['remaining_usd']:.4f}"
    )

    return tweets

def main():
    # کلید API خود را وارد کنید
    API_KEY = "54600ae426bd46f8a5f6c7d16df4e00b"
    QUERY = "from:elonmusk"
    MAX_RESULTS = 100
    USE_CACHE = False

    if API_KEY == "YOUR_API_KEY_HERE":
        logger.error("Please provide a valid API key")
        sys.exit(1)

    logger.info("Running tweet search test...")
    try:
        tweets = test_search_tweets(API_KEY, QUERY, MAX_RESULTS, USE_CACHE)
        logger.info(f"Test completed successfully. Total tweets: {len(tweets)}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()