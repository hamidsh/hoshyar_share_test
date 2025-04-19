import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .services import TwitterCollectorService
from .models import SearchQuery, TaskLog

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def collect_new_tweets(self, force=False, query_id=None, archive_mode=False):
    """
    جمع‌آوری توییت‌های جدید یا قدیمی از کوئری‌های فعال یا یک کوئری خاص.

    Args:
        force: اجبار به جمع‌آوری حتی با وجود محدودیت بودجه.
        query_id: شناسه کوئری خاص برای اجرای فوری (اختیاری).
        archive_mode: اگه True باشه، توییت‌های قدیمی‌تر جمع می‌شن.

    Returns:
        دیکشنری حاوی نتیجه جمع‌آوری.
    """
    task_id = self.request.id
    try:
        daily_budget = getattr(settings, 'TWITTER_API_DAILY_BUDGET_USD', 0.5)
        service = TwitterCollectorService(
            api_key=settings.TWITTER_API_KEY,
            daily_budget_usd=daily_budget
        )
        api_status = service.get_api_status()

        # انتخاب کوئری‌ها
        if query_id:
            queries = SearchQuery.objects.filter(id=query_id, is_active=True)
            force = True
        else:
            if not force and api_status.get('mode') == 'real' and api_status.get('budget', {}).get('used_percent', 0) > 80:
                logger.warning(
                    f"بیش از 80% بودجه مصرف شده ({api_status['budget']['used_percent']:.1f}%). "
                    f"فقط کوئری‌های با اولویت بالا اجرا می‌شوند."
                )
                queries = SearchQuery.objects.filter(is_active=True, priority='high')
            else:
                queries = SearchQuery.objects.filter(is_active=True)

        scheduled_queries = list(queries)  # برای تست، همه کوئری‌ها
        logger.debug(f"کوئری‌های انتخاب‌شده: {[q.query for q in scheduled_queries]}")

        results = {
            'collected': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'queries_count': len(scheduled_queries),
            'skipped_queries_count': len(queries) - len(scheduled_queries)
        }

        for query in scheduled_queries:
            result = service.collect_from_query(query)
            results['collected'] += result.get('collected', 0)
            results['created'] += result.get('created', 0)
            results['updated'] += result.get('updated', 0)
            results['errors'] += result.get('errors', 0)

            # ذخیره لاگ برای هر کوئری
            with transaction.atomic():
                TaskLog.objects.create(
                    task_name='collect_new_tweets',
                    task_id=f"{task_id}-{query.id}",
                    query=query,
                    status='success' if result['errors'] == 0 else 'error',
                    message=f"جمع‌آوری {result['collected']} توییت: {result['created']} جدید, {result['updated']} به‌روزرسانی",
                    collected=result['collected'],
                    created=result['created'],
                    updated=result['updated'],
                    errors=result['errors']
                )

        logger.info(
            f"جمع‌آوری {results['collected']} توییت از {len(scheduled_queries)} کوئری: "
            f"{results['created']} جدید, {results['updated']} بروزرسانی, {results['errors']} خطا"
        )
        results['api_status'] = api_status
        return {'status': 'success', 'results': results}

    except Exception as e:
        logger.error(f"خطا در جمع‌آوری توییت‌های جدید: {str(e)}")
        with transaction.atomic():
            TaskLog.objects.create(
                task_name='collect_new_tweets',
                task_id=task_id,
                query=None,
                status='error',
                message=str(e),
                errors=1
            )
        return {'status': 'error', 'error': str(e)}

@shared_task(bind=True)
def collect_user_tweets(self, username=None, user_id=None, max_tweets=50):
    task_id = self.request.id
    if not username and not user_id:
        TaskLog.objects.create(
            task_name='collect_user_tweets',
            task_id=task_id,
            status='error',
            message='حداقل یکی از username یا user_id لازم است',
            errors=1
        )
        return {'status': 'error', 'error': 'حداقل یکی از username یا user_id لازم است'}
    try:
        daily_budget = getattr(settings, 'TWITTER_API_DAILY_BUDGET_USD', 0.5)
        service = TwitterCollectorService(
            api_key=settings.TWITTER_API_KEY,
            daily_budget_usd=daily_budget
        )
        api_status = service.get_api_status()
        if api_status.get('mode') == 'real' and api_status.get('budget', {}).get('used_percent', 0) > 90:
            error_msg = f"بیش از 90% بودجه مصرف شده ({api_status['budget']['used_percent']:.1f}%). جمع‌آوری متوقف شد."
            logger.warning(error_msg)
            TaskLog.objects.create(
                task_name='collect_user_tweets',
                task_id=task_id,
                status='error',
                message=error_msg,
                errors=1
            )
            return {'status': 'error', 'error': error_msg, 'api_status': api_status}
        if username:
            results = service.client.get_user_tweets(
                username=username,
                max_results=max_tweets
            )
        else:
            results = service.client.get_user_tweets(
                user_id=user_id,
                max_results=max_tweets
            )
        collected = 0
        created = 0
        updated = 0
        for tweet in results:
            db_tweet, is_created = service._process_tweet_from_model(tweet)
            collected += 1
            if is_created:
                created += 1
            else:
                updated += 1
        logger.info(
            f"جمع‌آوری {collected} توییت از {'@' + username if username else 'کاربر ' + user_id}: "
            f"{created} جدید, {updated} بروزرسانی"
        )
        TaskLog.objects.create(
            task_name='collect_user_tweets',
            task_id=task_id,
            status='success',
            message=f"جمع‌آوری {collected} توییت از {'@' + username if username else 'کاربر ' + user_id}",
            collected=collected,
            created=created,
            updated=updated
        )
        return {
            'status': 'success',
            'collected': collected,
            'created': created,
            'updated': updated,
            'api_status': api_status
        }
    except Exception as e:
        logger.error(f"خطا در جمع‌آوری توییت‌های کاربر: {str(e)}")
        TaskLog.objects.create(
            task_name='collect_user_tweets',
            task_id=task_id,
            status='error',
            message=str(e),
            errors=1
        )
        return {'status': 'error', 'error': str(e)}

@shared_task(bind=True)
def update_api_usage_statistics(self):
    task_id = self.request.id
    try:
        daily_budget = getattr(settings, 'TWITTER_API_DAILY_BUDGET_USD', 0.5)
        service = TwitterCollectorService(
            api_key=settings.TWITTER_API_KEY,
            daily_budget_usd=daily_budget
        )
        api_status = service.get_api_status()
        usage_report = service.client.generate_usage_report(days=7)
        logger.info(
            f"گزارش مصرف API: "
            f"مصرف امروز: ${api_status['budget']['spent_usd']:.4f} از ${api_status['budget']['daily_usd']:.2f}"
        )
        TaskLog.objects.create(
            task_name='update_api_usage_statistics',
            task_id=task_id,
            status='success',
            message=f"گزارش مصرف API تولید شد: مصرف امروز ${api_status['budget']['spent_usd']:.4f}"
        )
        return {
            'status': 'success',
            'api_status': api_status,
            'usage_report': usage_report
        }
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی آمار API: {str(e)}")
        TaskLog.objects.create(
            task_name='update_api_usage_statistics',
            task_id=task_id,
            status='error',
            message=str(e),
            errors=1
        )
        return {'status': 'error', 'error': str(e)}