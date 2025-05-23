# Generated by Django 5.1.8 on 2025-04-15 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0005_alter_tasklog_unique_together_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchquery',
            name='last_tweet_timestamp',
        ),
        migrations.AddField(
            model_name='searchquery',
            name='last_cursor',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='result_type',
            field=models.CharField(choices=[('recent', 'Recent'), ('popular', 'Popular'), ('mixed', 'Mixed')], default='mixed', max_length=20),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='schedule_interval',
            field=models.IntegerField(default=1),
        ),
    ]
