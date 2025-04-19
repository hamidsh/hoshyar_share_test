from django.contrib import admin
from .models import SentimentAnalysis, Pattern

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('get_content', 'sentiment', 'confidence', 'analyzed_at')
    search_fields = ('tweet__text', 'news_article__title')
    list_filter = ('sentiment', 'analyzed_at')

    def get_content(self, obj):
        if obj.tweet:
            return f"Tweet: {obj.tweet.text[:50]}..."
        elif obj.news_article:
            return f"News: {obj.news_article.title[:50]}..."
        return '-'
    get_content.short_description = 'Content'

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'pattern_type', 'confidence', 'detected_at')
    search_fields = ('name', 'description')
    list_filter = ('pattern_type', 'detected_at')