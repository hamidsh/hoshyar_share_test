from django.db import models

class SentimentAnalysis(models.Model):
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('mixed', 'Mixed'),
    ]
    tweet = models.OneToOneField('collector.Tweet', on_delete=models.CASCADE, null=True, blank=True, related_name='sentiment')
    news_article = models.OneToOneField('news.NewsArticle', on_delete=models.CASCADE, null=True, blank=True, related_name='sentiment')
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    confidence = models.FloatField()
    details = models.JSONField(null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    model_used = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=['sentiment']),
            models.Index(fields=['confidence']),
            models.Index(fields=['analyzed_at']),
        ]
        verbose_name = 'Sentiment Analysis'
        verbose_name_plural = 'Sentiment Analyses'

    def __str__(self):
        if self.tweet:
            return f"{self.sentiment} ({self.confidence:.2f}) - Tweet: {self.tweet.text[:50]}"
        elif self.news_article:
            return f"{self.sentiment} ({self.confidence:.2f}) - News: {self.news_article.title}"
        return f"{self.sentiment} ({self.confidence:.2f})"

class Pattern(models.Model):
    PATTERN_TYPES = [
        ('sentiment_trend', 'Sentiment Trend'),
        ('topic_trend', 'Topic Trend'),
        ('user_activity', 'User Activity'),
        ('user_relationship', 'User Relationship'),
        ('emerging_topic', 'Emerging Topic'),
        ('news_correlation', 'News Correlation'),
        ('unusual_activity', 'Unusual Activity'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField()
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPES)
    topics = models.ManyToManyField('memory.Topic', related_name='patterns')
    users = models.ManyToManyField('collector.TwitterUser', blank=True, related_name='patterns')
    tweets = models.ManyToManyField('collector.Tweet', blank=True, related_name='patterns')
    news_articles = models.ManyToManyField('news.NewsArticle', blank=True, related_name='patterns')
    confidence = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    data = models.JSONField(null=True, blank=True)
    model_used = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=['pattern_type']),
            models.Index(fields=['confidence']),
            models.Index(fields=['detected_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        verbose_name = 'Pattern'
        verbose_name_plural = 'Patterns'

    def __str__(self):
        return f"{self.name} ({self.get_pattern_type_display()})"