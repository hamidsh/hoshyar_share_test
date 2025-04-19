import logging
import feedparser
from django.utils import timezone
from django.db import transaction
from collector.models import Tweet, TwitterUser, SearchQuery  # اصلاح import
from .models import NewsSource, NewsArticle

logger = logging.getLogger(__name__)

class NewsCollectorService:
    def collect_from_source(self, source):
        """Collect news articles from an RSS source"""
        result = {
            'source': source.name,
            'total': 0,
            'added': 0,
            'updated': 0,
            'errors': 0
        }
        try:
            feed = feedparser.parse(source.rss_url)
            if feed.bozo:
                logger.error(f"Error parsing feed for {source.name}: {str(feed.bozo_exception)}")
                result['errors'] += 1
                return result
            for entry in feed.entries:
                with transaction.atomic():
                    article, created = self._process_entry(entry, source)
                    if created:
                        result['added'] += 1
                    else:
                        result['updated'] += 1
                    result['total'] += 1
            source.last_fetch = timezone.now()
            source.total_articles = NewsArticle.objects.filter(source=source).count()
            source.save(update_fields=['last_fetch', 'total_articles'])
            return result
        except Exception as e:
            logger.error(f"Error collecting from {source.name}: {str(e)}")
            result['errors'] += 1
            return result

    def _process_entry(self, entry, source):
        """Process a single RSS entry"""
        from datetime import datetime
        import pytz
        published = entry.get('published_parsed')
        if published:
            published_at = datetime.fromtimestamp(datetime(*published[:6]).timestamp(), pytz.UTC)
        else:
            published_at = timezone.now()
        article, created = NewsArticle.objects.update_or_create(
            url=entry.get('link', ''),
            defaults={
                'title': entry.get('title', 'Untitled'),
                'source': source,
                'guid': entry.get('id', entry.get('link', '')),
                'published_at': published_at,
                'summary': entry.get('summary', ''),
                'content': entry.get('content', [{}])[0].get('value', ''),
                'is_valid': True
            }
        )
        return article, created