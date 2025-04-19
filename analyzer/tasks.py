import logging
from celery import shared_task
from .services import SentimentAnalyzer

logger = logging.getLogger(__name__)

@shared_task
def analyze_recent_tweets(hours=24):
    """Analyze recent tweets"""
    try:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_recent_tweets(hours)
        return {'status': 'success', 'result': result}
    except Exception as e:
        logger.error(f"Error in analyze_recent_tweets: {str(e)}")
        return {'status': 'error', 'error': str(e)}