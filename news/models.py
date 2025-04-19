from django.db import models
from django.utils import timezone

class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    rss_url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_fetch = models.DateTimeField(null=True, blank=True)
    fetch_interval = models.IntegerField(default=60)
    total_articles = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'News Source'
        verbose_name_plural = 'News Sources'

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    title = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='articles')
    guid = models.CharField(max_length=500, blank=True)
    author = models.CharField(max_length=200, blank=True, null=True)
    published_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    is_valid = models.BooleanField(default=True)
    importance_score = models.FloatField(default=0.0)
    keywords = models.JSONField(default=list, blank=True)  # جایگزین ArrayField

    class Meta:
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['importance_score']),
        ]
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'

    def __str__(self):
        return self.title