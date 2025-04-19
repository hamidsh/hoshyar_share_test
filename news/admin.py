from django.contrib import admin
from .models import NewsSource, NewsArticle

@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'total_articles')
    search_fields = ('name', 'url')
    list_filter = ('is_active',)

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'is_valid')
    search_fields = ('title', 'content')
    list_filter = ('is_valid', 'published_at')