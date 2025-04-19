import logging
from celery import shared_task
from .services import NewsCollectorService
from .models import NewsSource

logger = logging.getLogger(__name__)

@shared_task
def collect_news():
    """Collect news articles from active sources"""
    try:
        service = NewsCollectorService()
        sources = NewsSource.objects.filter(is_active=True)
        total_collected = 0
        for source in sources:
            result = service.collect_from_source(source)
            total_collected += result['total']
        logger.info(f"Collected {total_collected} news articles")
        return {'status': 'success', 'total_collected': total_collected}
    except Exception as e:
        logger.error(f"Error in collect_news: {str(e)}")
        return {'status': 'error', 'error': str(e)}