from django.contrib import admin
from django.contrib import messages
from .models import TwitterUser, Tweet, SearchQuery, TaskLog
from .tasks import collect_new_tweets

@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'followers_count', 'influence_score')
    search_fields = ('username', 'display_name')

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('tweet_id', 'user', 'text', 'created_at', 'is_valid')
    search_fields = ('text', 'user__username')
    list_filter = ('is_valid', 'created_at')

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'priority', 'is_active', 'total_collected', 'last_run', 'schedule_interval')
    search_fields = ('query', 'description')
    list_filter = ('is_active', 'priority', 'result_type', 'language')
    fieldsets = (
        (None, {
            'fields': ('query', 'description', 'is_active', 'priority')
        }),
        ('تنظیمات جستجو', {
            'fields': ('result_type', 'language', 'count_per_run')
        }),
        ('زمان‌بندی و صفحه‌بندی', {
            'fields': ('schedule_interval', 'last_run', 'last_cursor', 'archive_until_timestamp')
        }),
        ('آمار', {
            'fields': ('total_collected', 'total_valid')
        }),
    )
    actions = ['run_query_now', 'run_query_archive', 'reset_last_run']

    def run_query_now(self, request, queryset):
        """
        اجرای فوری کوئری‌های انتخاب‌شده برای توییت‌های جدید.
        """
        try:
            for query in queryset:
                collect_new_tweets.delay(query_id=query.id, archive_mode=False)
                self.message_user(request, f"تسک برای کوئری '{query.query}' (جدید) به صف ارسال شد.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"خطا در ارسال تسک: {str(e)}", messages.ERROR)
    run_query_now.short_description = "اجرای فوری کوئری (جدید)"

    def run_query_archive(self, request, queryset):
        """
        اجرای فوری کوئری‌های انتخاب‌شده برای توییت‌های قدیمی (آرشیو).
        """
        try:
            for query in queryset:
                collect_new_tweets.delay(query_id=query.id, archive_mode=True)
                self.message_user(request, f"تسک برای کوئری '{query.query}' (آرشیو) به صف ارسال شد.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"خطا در ارسال تسک: {str(e)}", messages.ERROR)
    run_query_archive.short_description = "اجرای فوری کوئری (آرشیو)"

    def reset_last_run(self, request, queryset):
        """
        ریست زمان آخرین اجرا و cursor برای اجرای دوباره.
        """
        try:
            queryset.update(last_run=None, last_cursor=None, archive_until_timestamp=None)
            self.message_user(request, f"زمان‌ها و cursor برای {queryset.count()} کوئری ریست شد.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"خطا در ریست: {str(e)}", messages.ERROR)
    reset_last_run.short_description = "ریست زمان و cursor"

@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'task_id', 'query', 'status', 'collected', 'created', 'updated', 'errors', 'executed_at')
    search_fields = ('task_name', 'task_id', 'message')
    list_filter = ('status', 'task_name', 'executed_at')
    readonly_fields = ('task_name', 'task_id', 'query', 'status', 'message', 'collected', 'created', 'updated', 'errors', 'executed_at')

    def has_add_permission(self, request):
        return False