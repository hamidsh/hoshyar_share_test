import logging
from django.utils import timezone
from collector.models import Tweet
from .models import SentimentAnalysis

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def analyze_tweet(self, tweet):
        """Simple sentiment analysis (positive, negative, neutral)"""
        text = tweet.text.lower()
        positive_words = ['خوب', 'عالی', 'بهبود', 'موفق', 'پیشرفت']
        negative_words = ['بد', 'فیلتر', 'مشکل', 'نابود', 'فساد']

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = negative_count / (positive_count + negative_count + 1)
        else:
            sentiment = 'neutral'
            confidence = 0.5

        analysis, _ = SentimentAnalysis.objects.update_or_create(
            tweet=tweet,
            defaults={
                'sentiment': sentiment,
                'confidence': confidence,
                'analyzed_at': timezone.now()
            }
        )
        logger.info(f"Tweet {tweet.tweet_id} analyzed: {sentiment} ({confidence:.2f})")
        return analysis

    def analyze_recent_tweets(self, hours=24):
        """Analyze tweets from the last X hours"""
        result = {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        tweets = Tweet.objects.filter(collected_at__gte=cutoff, is_valid=True)
        result['total'] = tweets.count()

        for tweet in tweets:
            analysis = self.analyze_tweet(tweet)
            if analysis.sentiment == 'positive':
                result['positive'] += 1
            elif analysis.sentiment == 'negative':
                result['negative'] += 1
            else:
                result['neutral'] += 1

        logger.info(
            f"Analyzed {result['total']} tweets: {result['positive']} positive, {result['negative']} negative, {result['neutral']} neutral")
        return result