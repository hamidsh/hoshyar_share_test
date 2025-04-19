from django.contrib import admin
from .models import Topic, UserRelationship, MemoryRecord

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(UserRelationship)
class UserRelationshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'relationship_type', 'to_user', 'strength')
    search_fields = ('from_user__username', 'to_user__username')
    list_filter = ('relationship_type',)

@admin.register(MemoryRecord)
class MemoryRecordAdmin(admin.ModelAdmin):
    list_display = ('topic', 'memory_type', 'content_type', 'created_at')
    search_fields = ('topic__name', 'summary')
    list_filter = ('memory_type', 'content_type')