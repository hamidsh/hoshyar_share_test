"""
کلاینت بهینه‌شده TwitterAPI.io با مدیریت هزینه و کنترل نرخ درخواست

این ماژول یک لایه میان‌افزار برای کلاینت TwitterAPI.io فراهم می‌کند که
امکان مدیریت هزینه، کنترل نرخ درخواست و کش کردن نتایج را فراهم می‌سازد.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from lib.twitter_api import TwitterAPIClient, Tweet
from lib.twitter_api.middleware.budget import TwitterAPIBudget
from lib.twitter_api.middleware.cache import TwitterAPICache
from lib.twitter_api.middleware.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class OptimizedTwitterAPIClient:
    """
    نسخه بهینه شده کلاینت TwitterAPI با مدیریت هزینه، کش و کنترل نرخ درخواست

    این کلاس یک لایه میان‌افزار روی کلاینت اصلی TwitterAPIClient ایجاد می‌کند
    که امکانات زیر را فراهم می‌سازد:

    1. مدیریت بودجه و محدودیت هزینه روزانه
    2. کش کردن نتایج برای کاهش درخواست‌های تکراری
    3. کنترل نرخ درخواست برای جلوگیری از ارسال درخواست‌های متوالی سریع
    4. محدودسازی هوشمند پارامترهای pagination برای کنترل هزینه
    5. گزارش‌دهی دقیق از مصرف API
    """

    def __init__(
        self,
        api_key: str,
        daily_budget_usd: float = 0.5,
        enable_cache: bool = True,
        cache_dir: str = '.twitter_cache',
        base_delay: float = 0.5,
        max_requests_per_minute: int = 60,
        default_max_pages: int = 10,  # افزایش به 10 برای انعطاف‌پذیری
        default_max_results: int = 100
    ):
        self.budget = TwitterAPIBudget(daily_budget_usd)
        self.cache = TwitterAPICache(cache_dir) if enable_cache else None
        self.rate_limiter = RateLimiter(self.budget, max_requests_per_minute, base_delay)
        self.enable_cache = enable_cache
        self.default_max_pages = default_max_pages
        self.default_max_results = default_max_results
        self.client = TwitterAPIClient(api_key)
        self._wrap_base_make_request()
        self._wrap_client_methods()
        logger.info(f"Optimized client initialized. Budget: ${daily_budget_usd:.2f}, cache: {'enabled' if enable_cache else 'disabled'}")

    def _wrap_base_make_request(self):
        original_make_request = self.client.base.make_request

        def optimized_make_request(method, endpoint, params=None, data=None, headers=None, timeout=None, **kwargs):
            skip_cache = kwargs.get('skip_cache', False)
            resource_type, resource_count = self._estimate_resource_info(endpoint, params)
            start_time = time.time()
            short_endpoint = endpoint.split('/')[-1] if '/' in endpoint else endpoint
            logger.debug(f"Request to {short_endpoint} ({resource_type}, count: {resource_count})")

            estimated_cost = self.budget.calculate_cost(resource_type, resource_count)
            if not self.budget.check_budget(resource_type, resource_count):
                status = self.budget.get_status()
                error_msg = (
                    f"Insufficient budget for request to {short_endpoint}. "
                    f"Spent today: ${status['spent_today_usd']:.4f} of ${status['daily_budget_usd']:.2f}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

            if self.enable_cache and method.upper() == 'GET' and not skip_cache:
                max_results = kwargs.get('max_results') or params.get('max_results') if params else None
                cache_data = self.cache.get(endpoint, params, max_results)
                if cache_data:
                    logger.info(f"Retrieved cache for {short_endpoint}")
                    return cache_data

            wait_time = self.rate_limiter.wait_if_needed(endpoint, estimated_cost)
            if wait_time > 0:
                logger.debug(f"Waiting {wait_time:.2f} seconds for {short_endpoint}")

            try:
                self.budget.record_usage(endpoint, resource_type, resource_count)
                response = original_make_request(method, endpoint, params, data, headers, timeout)
                response_time = time.time() - start_time
                logger.info(f"Response from {short_endpoint}. Time: {response_time:.2f}s, cost: {estimated_cost} credits")

                if self.enable_cache and method.upper() == 'GET':
                    max_results = kwargs.get('max_results') or params.get('max_results') if params else None
                    self.cache.set(endpoint, params, response, max_results)

                return response
            except Exception as e:
                logger.error(f"Error in request to {short_endpoint}: {str(e)}")
                time.sleep(1.0)
                raise

        self.client.base.make_request = optimized_make_request

    def _wrap_client_methods(self):
        original_search_tweets = self.client.search_tweets

        def limited_search_tweets(query, query_type="Latest", cursor=None, max_pages=None, max_results=None, convert_to_models=True):
            # محاسبه تعداد صفحات بر اساس max_results
            if max_results is not None:
                estimated_pages = max(1, (max_results + 19) // 20)  # فرض 20 توییت در صفحه
                max_pages = max_pages or estimated_pages
                if max_pages < estimated_pages:
                    logger.warning(f"max_pages ({max_pages}) may be insufficient for max_results ({max_results})")
            else:
                max_pages = max_pages or self.default_max_pages

            max_results = max_results or self.default_max_results
            logger.debug(f"Settings: max_pages={max_pages}, max_results={max_results}")

            return original_search_tweets(
                query=query,
                query_type=query_type,
                cursor=cursor,
                max_pages=max_pages,
                max_results=max_results,
                convert_to_models=convert_to_models
            )

        self.client.search_tweets = limited_search_tweets

        def limited_search_tweets(query, query_type="Latest", cursor=None,
                                  max_pages=None, max_results=None, convert_to_models=True):
            """نسخه محدود شده search_tweets"""
            # اعمال محدودیت‌های پیش‌فرض
            if max_pages is None or max_pages > self.default_max_pages:
                max_pages = self.default_max_pages
                logger.debug(f"محدودیت max_pages به {max_pages} تنظیم شد (کنترل هزینه)")

            if max_results is None or max_results > self.default_max_results:
                max_results = self.default_max_results
                logger.debug(f"محدودیت max_results به {max_results} تنظیم شد (کنترل هزینه)")

            # اجرای متد اصلی با محدودیت‌های اعمال شده
            return original_search_tweets(
                query=query,
                query_type=query_type,
                cursor=cursor,
                max_pages=max_pages,
                max_results=max_results,
                convert_to_models=convert_to_models
            )

        # 2. محدودسازی دریافت توییت‌های کاربر
        original_get_user_tweets = self.client.get_user_tweets

        def limited_get_user_tweets(username=None, user_id=None, cursor=None,
                                    max_pages=None, max_results=None, convert_to_models=True):
            """نسخه محدود شده get_user_tweets"""
            # اعمال محدودیت‌های پیش‌فرض
            if max_pages is None or max_pages > self.default_max_pages:
                max_pages = self.default_max_pages
                logger.debug(f"محدودیت max_pages به {max_pages} تنظیم شد (کنترل هزینه)")

            if max_results is None or max_results > self.default_max_results:
                max_results = self.default_max_results
                logger.debug(f"محدودیت max_results به {max_results} تنظیم شد (کنترل هزینه)")

            # اجرای متد اصلی با محدودیت‌های اعمال شده
            return original_get_user_tweets(
                username=username,
                user_id=user_id,
                cursor=cursor,
                max_pages=max_pages,
                max_results=max_results,
                convert_to_models=convert_to_models
            )

        # 3. محدودسازی دریافت دنبال‌کنندگان کاربر
        original_get_user_followers = self.client.get_user_followers

        def limited_get_user_followers(username, cursor=None, max_pages=None,
                                       max_results=None, convert_to_models=True):
            """نسخه محدود شده get_user_followers"""
            # اعمال محدودیت‌های پیش‌فرض
            if max_pages is None or max_pages > self.default_max_pages:
                max_pages = self.default_max_pages
                logger.debug(f"محدودیت max_pages به {max_pages} تنظیم شد (کنترل هزینه)")

            if max_results is None or max_results > self.default_max_results:
                max_results = self.default_max_results
                logger.debug(f"محدودیت max_results به {max_results} تنظیم شد (کنترل هزینه)")

            # اجرای متد اصلی با محدودیت‌های اعمال شده
            return original_get_user_followers(
                username=username,
                cursor=cursor,
                max_pages=max_pages,
                max_results=max_results,
                convert_to_models=convert_to_models
            )

        # 4. محدودسازی دریافت پاسخ‌های توییت
        original_get_tweet_replies = self.client.get_tweet_replies

        def limited_get_tweet_replies(tweet_id, since_time=None, until_time=None,
                                      cursor=None, max_pages=None, max_results=None,
                                      convert_to_models=True):
            """نسخه محدود شده get_tweet_replies"""
            # اعمال محدودیت‌های پیش‌فرض
            if max_pages is None or max_pages > self.default_max_pages:
                max_pages = self.default_max_pages
                logger.debug(f"محدودیت max_pages به {max_pages} تنظیم شد (کنترل هزینه)")

            if max_results is None or max_results > self.default_max_results:
                max_results = self.default_max_results
                logger.debug(f"محدودیت max_results به {max_results} تنظیم شد (کنترل هزینه)")

            # اجرای متد اصلی با محدودیت‌های اعمال شده
            return original_get_tweet_replies(
                tweet_id=tweet_id,
                since_time=since_time,
                until_time=until_time,
                cursor=cursor,
                max_pages=max_pages,
                max_results=max_results,
                convert_to_models=convert_to_models
            )

        # جایگزینی متدهای اصلی با نسخه‌های محدود شده
        self.client.search_tweets = limited_search_tweets
        self.client.get_user_tweets = limited_get_user_tweets
        self.client.get_user_followers = limited_get_user_followers
        self.client.get_tweet_replies = limited_get_tweet_replies

        # همین الگو برای سایر متدها نیز تکرار می‌شود...

    def _estimate_resource_info(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> tuple[str, int]:
        if 'tweet/advanced_search' in endpoint:
            return 'tweet', 20
        elif 'user/info' in endpoint:
            return 'user', 1
        elif 'user/batch_info_by_ids' in endpoint:
            user_count = 1
            if params and 'userIds' in params:
                ids = params['userIds']
                if isinstance(ids, str):
                    user_count = len(ids.split(','))
                elif isinstance(ids, list):
                    user_count = len(ids)
            return 'user', user_count
        elif 'user/followers' in endpoint or 'user/followings' in endpoint:
            return 'follower', 200
        elif 'user/last_tweets' in endpoint:
            return 'tweet', 20
        elif 'tweet/replies' in endpoint:
            return 'tweet', 20
        elif 'tweet/quotes' in endpoint:
            return 'tweet', 20
        elif 'list/tweets' in endpoint:
            return 'tweet', 20
        else:
            return 'request', 1

    def get_budget_status(self) -> Dict[str, Any]:
        return self.budget.get_status()

    def get_cache_stats(self) -> Dict[str, Any]:
        if self.cache:
            return self.cache.get_stats()
        return {"error": "Cache is not enabled"}

    def clear_cache(self, endpoint: Optional[str] = None) -> int:
        if self.cache:
            return self.cache.clear(endpoint)
        return 0

    def generate_usage_report(self, days: int = 7) -> Dict[str, Any]:
        return self.budget.generate_usage_report(days)

    def set_default_limits(self, max_pages: int = None, max_results: int = None) -> None:
        if max_pages is not None:
            self.default_max_pages = max_pages
        if max_results is not None:
            self.default_max_results = max_results
        logger.info(f"Default limits set: max_pages={self.default_max_pages}, max_results={self.default_max_results}")

    def check_can_afford(self, endpoint: str, estimated_count: int = 1) -> bool:
        resource_type, _ = self._estimate_resource_info(endpoint, None)
        return self.budget.check_budget(resource_type, estimated_count)

    def search_tweets_safe(self, query: str, query_type: str = "Latest", max_results: int = 20) -> List[Tweet]:
        max_results = min(max_results, self.default_max_results)
        if not self.check_can_afford('twitter/tweet/advanced_search', max_results):
            logger.warning(f"Insufficient budget for searching {max_results} tweets")
            raise Exception("Insufficient budget")
        return self.client.search_tweets(
            query=query,
            query_type=query_type,
            max_pages=1,
            max_results=max_results
        )

    def get_user_info_safe(self, username: str) -> Any:
        if not self.check_can_afford('twitter/user/info', 1):
            logger.warning(f"Insufficient budget for user info: {username}")
            raise Exception("Insufficient budget")
        return self.client.get_user_info(username)

    def get_users_by_ids_efficient(self, user_ids: List[str]) -> List[Any]:
        batch_size = 100
        results = []
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            if not self.check_can_afford('twitter/user/batch_info_by_ids', len(batch)):
                logger.warning(f"Insufficient budget for {len(batch)} users")
                break
            batch_users = self.client.get_users_by_ids(batch)
            results.extend(batch_users)
            if i + batch_size < len(user_ids):
                self.rate_limiter.add_delay(1.0)
        return results

    def __getattr__(self, name):
        return getattr(self.client, name)