import logging
from celery import shared_task
from .services import TweetFilterService
from collector.models import Tweet

logger = logging.getLogger(__name__)

@shared_task
def filter_new_tweets(hours=24):
    """Filter new tweets from the last X hours"""
    try:
        service = TweetFilterService()
        result = service.filter_new_tweets(hours)
        logger.info(f"Filtered {result['total']} tweets: {result['valid']} valid, {result['invalid']} invalid")
        return {'status': 'success', 'total': result['total'], 'valid': result['valid'], 'invalid': result['invalid']}
    except Exception as e:
        logger.error(f"Error in filter_new_tweets: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@shared_task
def process_tweet(tweet_id):
    """Process a single tweet"""
    try:
        tweet = Tweet.objects.get(id=tweet_id)
        service = TweetFilterService()
        is_valid, reason = service.filter_tweet(tweet)
        if not is_valid:
            tweet.is_valid = False
            tweet.invalid_reason = reason
            tweet.save(update_fields=['is_valid', 'invalid_reason'])
            logger.info(f"Tweet {tweet_id} marked as invalid: {reason}")
            return {'status': 'success', 'tweet_id': tweet_id, 'is_valid': False, 'reason': reason}
        entities = service.extract_entities(tweet)
        logger.info(f"Tweet {tweet_id} processed: valid with {len(entities['hashtags'])} hashtags")
        return {
            'status': 'success',
            'tweet_id': tweet_id,
            'is_valid': True,
            'entities': {
                'hashtags_count': len(entities['hashtags']),
                'mentions_count': len(entities['mentions']),
                'keywords_count': len(entities['keywords'])
            }
        }
    except Tweet.DoesNotExist:
        logger.error(f"Tweet {tweet_id} does not exist")
        return {'status': 'error', 'tweet_id': tweet_id, 'error': 'Tweet does not exist'}
    except Exception as e:
        logger.error(f"Error in process_tweet for {tweet_id}: {str(e)}")
        return {'status': 'error', 'tweet_id': tweet_id, 'error': str(e)}