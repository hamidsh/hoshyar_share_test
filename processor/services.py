import logging
from django.utils import timezone
from django.conf import settings
from collector.models import Tweet

logger = logging.getLogger(__name__)


class TweetFilterService:
    def filter_tweet(self, tweet, min_length=None):
        """Filter a tweet based on rules"""
        min_length = min_length or settings.MIN_TWEET_LENGTH
        text = tweet.text
        logger.info(f"Filtering tweet {tweet.tweet_id}: text='{text}', length={len(text)}")

        if len(text) < min_length:
            logger.info(f"Tweet {tweet.tweet_id} invalid: too_short")
            return False, 'too_short'
        if settings.FILTER_INAPPROPRIATE_CONTENT and self._contains_inappropriate_content(text):
            logger.info(f"Tweet {tweet.tweet_id} invalid: inappropriate")
            return False, 'inappropriate'
        if settings.FILTER_DUPLICATES and self._is_duplicate(tweet):
            logger.info(f"Tweet {tweet.tweet_id} invalid: duplicate")
            return False, 'duplicate'
        if self._is_spam(tweet):
            logger.info(f"Tweet {tweet.tweet_id} invalid: spam")
            return False, 'spam'
        logger.info(f"Tweet {tweet.tweet_id} valid")
        return True, None

    def filter_new_tweets(self, hours=24):
        """Filter tweets from the last X hours"""
        result = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'invalid_reasons': {}
        }
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        tweets = Tweet.objects.filter(collected_at__gte=cutoff, is_valid=True, invalid_reason__isnull=True)
        result['total'] = tweets.count()

        for tweet in tweets:
            is_valid, reason = self.filter_tweet(tweet)
            if not is_valid:
                tweet.is_valid = False
                tweet.invalid_reason = reason
                tweet.save(update_fields=['is_valid', 'invalid_reason'])
                result['invalid'] += 1
                result['invalid_reasons'][reason] = result['invalid_reasons'].get(reason, 0) + 1
            else:
                result['valid'] += 1
        logger.info(f"Filtered {result['total']} tweets: {result['valid']} valid, {result['invalid']} invalid")
        return result

    def extract_entities(self, tweet):
        """Extract hashtags, mentions, and keywords from a tweet"""
        import re
        text = tweet.text
        entities = {
            'hashtags': re.findall(r'#(\w+)', text),
            'mentions': re.findall(r'@(\w+)', text),
            'keywords': []
        }
        words = re.findall(r'\b(\w{4,})\b', text.lower())
        stop_words = self._get_persian_stop_words()
        entities['keywords'] = [w for w in words if w not in stop_words][:10]

        tweet.hashtags = entities['hashtags']
        tweet.mentions = entities['mentions']
        tweet.keywords = entities['keywords']
        tweet.save(update_fields=['hashtags', 'mentions', 'keywords'])
        return entities

    def _contains_inappropriate_content(self, text):
        inappropriate_words = self._get_inappropriate_words()
        text_lower = text.lower()
        return any(word in text_lower for word in inappropriate_words)

    def _is_duplicate(self, tweet):
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        duplicates = Tweet.objects.filter(
            text=tweet.text,
            created_at__gte=cutoff
        ).exclude(id=tweet.id).exists()
        return duplicates

    def _is_spam(self, tweet):
        text = tweet.text
        if text.count('http') > 2:
            return True
        cutoff = timezone.now() - timezone.timedelta(hours=1)
        recent_tweets = Tweet.objects.filter(
            user=tweet.user,
            created_at__gte=cutoff
        ).exclude(id=tweet.id)
        return recent_tweets.count() > 15

    def _get_inappropriate_words(self):
        return ['badword1', 'badword2', 'badword3']

    def _get_persian_stop_words(self):
        return ['و', 'در', 'به', 'از', 'که', 'این', 'را', 'با', 'است', 'برای']