from django.db import models
from django.utils import timezone

class Topic(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    keywords = models.JSONField(default=list, blank=True)  # جایگزین ArrayField
    excluded_keywords = models.JSONField(default=list, blank=True)  # جایگزین ArrayField
    related_topics = models.ManyToManyField('self', blank=True, symmetrical=True)
    tweets = models.ManyToManyField('collector.Tweet', blank=True, related_name='topics')
    news_articles = models.ManyToManyField('news.NewsArticle', blank=True, related_name='topics')

    class Meta:
        indexes = [models.Index(fields=['name'])]
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return self.name

class UserRelationship(models.Model):
    RELATIONSHIP_TYPES = [
        ('mention', 'Mention'),
        ('reply', 'Reply'),
        ('retweet', 'Retweet'),
        ('quote', 'Quote'),
        ('inferred', 'Inferred'),
    ]
    from_user = models.ForeignKey('collector.TwitterUser', on_delete=models.CASCADE, related_name='relationships_from')
    to_user = models.ForeignKey('collector.TwitterUser', on_delete=models.CASCADE, related_name='relationships_to')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    strength = models.FloatField(default=0.0)
    count = models.IntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    topics = models.ManyToManyField(Topic, blank=True, related_name='user_relationships')

    class Meta:
        unique_together = ('from_user', 'to_user', 'relationship_type')
        indexes = [
            models.Index(fields=['relationship_type']),
            models.Index(fields=['strength']),
            models.Index(fields=['last_seen']),
        ]
        verbose_name = 'User Relationship'
        verbose_name_plural = 'User Relationships'

    def __str__(self):
        return f"{self.from_user.username} {self.get_relationship_type_display()} {self.to_user.username}"

class MemoryRecord(models.Model):
    MEMORY_TYPES = [
        ('short_term', 'Short Term'),
        ('medium_term', 'Medium Term'),
        ('long_term', 'Long Term'),
    ]
    CONTENT_TYPES = [
        ('tweets', 'Tweets'),
        ('news', 'News'),
        ('patterns', 'Patterns'),
        ('combined', 'Combined'),
    ]
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='memory_records')
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    raw_content = models.TextField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    tweet_count = models.IntegerField(default=0)
    news_count = models.IntegerField(default=0)
    pattern_count = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['memory_type']),
            models.Index(fields=['content_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        verbose_name = 'Memory Record'
        verbose_name_plural = 'Memory Records'

    def __str__(self):
        return f"{self.topic.name} - {self.get_memory_type_display()} - {self.get_content_type_display()}"