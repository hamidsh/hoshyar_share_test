import logging
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import Tweet, TwitterUser, SearchQuery
from lib.twitter_api.middleware import OptimizedTwitterAPIClient

logger = logging.getLogger(__name__)

class TwitterCollectorService:
    def __init__(self, api_key=None, daily_budget_usd=0.5):
        self.api_key = api_key or settings.TWITTER_API_KEY
        self.daily_budget_usd = daily_budget_usd
        cache_dir = getattr(settings, 'TWITTER_API_CACHE_DIR', '.twitter_cache')
        self.client = OptimizedTwitterAPIClient(
            api_key=self.api_key,
            daily_budget_usd=daily_budget_usd,
            enable_cache=False,  # برای تست
            cache_dir=cache_dir,
            default_max_pages=20,
            default_max_results=100
        )
        logger.info(f"سرویس با API واقعی راه‌اندازی شد. بودجه روزانه: ${daily_budget_usd:.2f}, کش: غیرفعال")

    def collect_from_query(self, query):
        result = {
            'query': query.query,
            'collected': 0,
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        try:
            return self._collect_from_query_real(query, result)
        except Exception as e:
            logger.error(f"خطا در جمع‌آوری برای {query.query}: {str(e)}")
            result['errors'] += 1
            return result

    def _collect_from_query_real(self, query, result):
        budget_status = self.client.get_budget_status()
        if budget_status['percentage_used'] > 90:
            logger.warning(
                f"بیش از 90% بودجه مصرف شده ({budget_status['percentage_used']:.1f}%). "
                f"جمع‌آوری برای {query.query} متوقف شد."
            )
            result['errors'] += 1
            return result

        # اصلاح query_type برای پشتیبانی از API
        query_type = "Latest" if query.result_type == "recent" else "Top" if query.result_type == "popular" else "Latest"  # Mixed به Latest مپ می‌شه
        max_results = query.count_per_run
        max_pages = 20
        cursor = query.last_cursor or None

        logger.info(f"جستجو: query={query.query}, max_results={max_results}, max_pages={max_pages}, cursor={cursor or 'None'}")
        try:
            tweets = self.client.search_tweets(
                query=query.query,
                query_type=query_type,
                cursor=cursor,
                max_results=max_results,
                max_pages=max_pages,
                convert_to_models=True
            )
            logger.info(f"API برگشت داد {len(tweets)} توییت برای {query.query}")
            # چک کردن next_cursor در پاسخ
            # چون API ساختار پاسخ رو ممکنه تغییر بده، مستقیماً tweets رو می‌گیریم
        except Exception as e:
            logger.error(f"خطا در جستجوی API برای {query.query}: {str(e)}")
            result['errors'] += 1
            return result

        if len(tweets) < max_results:
            logger.warning(f"کمتر از انتظار: {len(tweets)} توییت به جای {max_results}. بودجه باقی‌مانده: ${budget_status['remaining_usd']:.2f}")
        if len(tweets) < 19:
            logger.warning(f"تعداد توییت‌ها کمتر از حداقل مورد انتظار (19): {len(tweets)} برای {query.query}")

        # فیلتر کردن توییت‌های تکراری
        existing_tweet_ids = set(Tweet.objects.filter(tweet_id__in=[t.id for t in tweets]).values_list('tweet_id', flat=True))
        new_tweets = [t for t in tweets if t.id not in existing_tweet_ids]

        logger.info(f"فیلتر تکراری: {len(tweets)} توییت دریافتی, {len(new_tweets)} توییت جدید")

        for tweet in new_tweets:
            with transaction.atomic():
                db_tweet, created = self._process_tweet_from_model(tweet)
                logger.debug(f"توییت {db_tweet.tweet_id} پردازش شد - جدید: {created}")
                result['collected'] += 1
                if created:
                    result['created'] += 1
                else:
                    result['updated'] += 1

        with transaction.atomic():
            query.refresh_from_db()
            query.total_collected += result['collected']
            query.last_run = timezone.now()
            query.last_cursor = None  # تا وقتی next_cursor رو درست دریافت کنیم
            query.save(update_fields=['total_collected', 'last_run', 'last_cursor'])

        logger.info(
            f"جمع‌آوری {result['collected']} توییت برای {query.query}: "
            f"{result['created']} جدید, {result['updated']} به‌روزرسانی"
        )
        return result

    def _process_tweet_from_model(self, tweet_model):
        user_model = tweet_model.author
        user, _ = self._get_or_create_user_from_model(user_model)
        tweet, created = Tweet.objects.get_or_create(
            tweet_id=tweet_model.id,
            defaults={
                'text': tweet_model.text,
                'user': user,
                'created_at': tweet_model.created_at,
                'language': tweet_model.lang or 'fa',
                'reply_count': tweet_model.reply_count,
                'retweet_count': tweet_model.retweet_count,
                'like_count': tweet_model.like_count,
                'quote_count': tweet_model.quote_count,
                'replied_to_tweet_id': tweet_model.in_reply_to_id,
                'conversation_id': tweet_model.conversation_id,
                'retweeted_tweet_id': None,
                'quoted_tweet_id': None,
                'is_valid': True,
                'hashtags': [h.text for h in tweet_model.hashtags],
                'mentions': [m.screen_name for m in tweet_model.user_mentions]
            }
        )
        if not created:
            fields_to_update = {}
            if tweet.text != tweet_model.text:
                fields_to_update['text'] = tweet_model.text
            if tweet.reply_count != tweet_model.reply_count:
                fields_to_update['reply_count'] = tweet_model.reply_count
            if tweet.retweet_count != tweet_model.retweet_count:
                fields_to_update['retweet_count'] = tweet_model.retweet_count
            if tweet.like_count != tweet_model.like_count:
                fields_to_update['like_count'] = tweet_model.like_count
            if tweet.quote_count != tweet_model.quote_count:
                fields_to_update['quote_count'] = tweet_model.quote_count
            if fields_to_update:
                for field, value in fields_to_update.items():
                    setattr(tweet, field, value)
                tweet.save(update_fields=fields_to_update.keys())
        tweet.calculate_engagement_score()
        return tweet, created

    def _get_or_create_user_from_model(self, user_model):
        user, created = TwitterUser.objects.get_or_create(
            user_id=user_model.id,
            defaults={
                'username': user_model.username,
                'display_name': user_model.name,
                'description': user_model.description or '',
                'followers_count': user_model.followers_count,
                'following_count': user_model.following_count,
                'tweet_count': user_model.tweet_count,
                'profile_image_url': user_model.profile_picture or '',
                'verified': user_model.is_blue_verified,
                'created_at': user_model.created_at
            }
        )
        if created or user.influence_score == 0:
            user.calculate_influence_score()
        return user, created

    def get_api_status(self):
        try:
            budget_status = self.client.get_budget_status()
            cache_stats = self.client.get_cache_stats()
            return {
                "mode": "real",
                "status": "active",
                "api_key": f"***{self.api_key[-4:]}",
                "budget": {
                    "daily_usd": budget_status['daily_budget_usd'],
                    "spent_usd": budget_status['spent_today_usd'],
                    "remaining_usd": budget_status['remaining_usd'],
                    "used_percent": budget_status['percentage_used']
                },
                "cache": {
                    "enabled": self.client.enable_cache,
                    "hit_rate": cache_stats.get('hit_rate_percent', 0),
                    "size_mb": cache_stats.get('size_mb', 0)
                }
            }
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت API: {str(e)}")
            return {"mode": "real", "status": "error", "error": str(e)}