from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('hoshyar')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'collect-tweets-hourly': {
        'task': 'collector.tasks.collect_new_tweets',
        'schedule': crontab(minute='*'),  # هر دقیقه اجرا می‌شه
    },
    'collect-news-hourly': {
        'task': 'news.tasks.collect_news',
        'schedule': crontab(minute='*'),  # هر دقیقه اجرا می‌شه
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')