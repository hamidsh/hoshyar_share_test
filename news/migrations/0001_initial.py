# Generated by Django 5.2 on 2025-04-11 06:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewsSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('rss_url', models.URLField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('logo_url', models.URLField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_fetch', models.DateTimeField(blank=True, null=True)),
                ('fetch_interval', models.IntegerField(default=60)),
                ('total_articles', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'News Source',
                'verbose_name_plural': 'News Sources',
            },
        ),
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('url', models.URLField(unique=True)),
                ('guid', models.CharField(blank=True, max_length=500)),
                ('author', models.CharField(blank=True, max_length=200, null=True)),
                ('published_at', models.DateTimeField()),
                ('collected_at', models.DateTimeField(auto_now_add=True)),
                ('summary', models.TextField(blank=True)),
                ('content', models.TextField(blank=True)),
                ('image_url', models.URLField(blank=True, null=True)),
                ('is_valid', models.BooleanField(default=True)),
                ('importance_score', models.FloatField(default=0.0)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='news.newssource')),
            ],
            options={
                'verbose_name': 'News Article',
                'verbose_name_plural': 'News Articles',
                'indexes': [models.Index(fields=['published_at'], name='news_newsar_publish_df29a9_idx'), models.Index(fields=['importance_score'], name='news_newsar_importa_e23d6b_idx')],
            },
        ),
    ]
