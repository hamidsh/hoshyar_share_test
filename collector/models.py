from django.db import models
from django.utils import timezone

class TwitterUser(models.Model):
    user_id = models.CharField(max_length=100, unique=True, db_index=True)
    username = models.CharField(max_length=100, db_index=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    influence_score = models.FloatField(default=0.0)

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['influence_score']),
        ]
        verbose_name = 'Twitter User'
        verbose_name_plural = 'Twitter Users'

    def __str__(self):
        return f"{self.username} ({self.display_name})"

    def calculate_influence_score(self):
        follower_factor = min(self.followers_count * 0.7, 70)
        tweet_factor = min(self.tweet_count * 0.3, 30)
        self.influence_score = (follower_factor + tweet_factor) / 100
        self.save(update_fields=['influence_score'])
        return self.influence_score

class Tweet(models.Model):
    tweet_id = models.CharField(max_length=100, unique=True, db_index=True)
    text = models.TextField()
    user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE, related_name='tweets')
    created_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, default='fa')
    reply_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)
    replied_to_tweet_id = models.CharField(max_length=100, null=True, blank=True)
    conversation_id = models.CharField(max_length=100, null=True, blank=True)
    retweeted_tweet_id = models.CharField(max_length=100, null=True, blank=True)
    quoted_tweet_id = models.CharField(max_length=100, null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    invalid_reason = models.CharField(max_length=50, null=True, blank=True)
    engagement_score = models.FloatField(default=0.0)
    importance_score = models.FloatField(default=0.0)
    hashtags = models.JSONField(default=list, blank=True)
    mentions = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['importance_score']),
            models.Index(fields=['engagement_score']),
        ]
        verbose_name = 'Tweet'
        verbose_name_plural = 'Tweets'

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}..."

    def calculate_engagement_score(self):
        engagement = (
            2 * self.reply_count +
            3 * self.retweet_count +
            1 * self.like_count +
            2 * self.quote_count
        ) / 100
        self.engagement_score = min(max(engagement, 0), 1)
        self.save(update_fields=['engagement_score'])
        return self.engagement_score

class SearchQuery(models.Model):
    RESULT_TYPE_CHOICES = [
        ('recent', 'Recent'),
        ('popular', 'Popular'),
        ('mixed', 'Mixed')
    ]
    PRIORITY_CHOICES = [
        ('high', 'اولویت بالا'),
        ('medium', 'اولویت متوسط'),
        ('low', 'اولویت پایین'),
    ]
    query = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_cursor = models.CharField(max_length=255, null=True, blank=True)  # برای cursor
    archive_until_timestamp = models.BigIntegerField(null=True, blank=True)  # برای آرشیو
    result_type = models.CharField(
        max_length=20,
        choices=RESULT_TYPE_CHOICES,
        default='mixed'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    language = models.CharField(max_length=10, default='fa')
    count_per_run = models.IntegerField(default=100)
    schedule_interval = models.IntegerField(default=1)  # برای تست
    total_collected = models.IntegerField(default=0)
    total_valid = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'

    def __str__(self):
        return self.query

class TaskLog(models.Model):
    task_name = models.CharField(max_length=200)
    task_id = models.CharField(max_length=150)
    query = models.ForeignKey(SearchQuery, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('success', 'موفق'), ('error', 'خطا'), ('skipped', 'رد شده')])
    message = models.TextField(blank=True)
    collected = models.IntegerField(default=0)
    created = models.IntegerField(default=0)
    updated = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Task Log'
        verbose_name_plural = 'Task Logs'

    def __str__(self):
        return f"{self.task_name} ({self.task_id}) - {self.status}"