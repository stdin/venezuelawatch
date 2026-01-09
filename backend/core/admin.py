from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'source', 'event_type', 'title', 'severity', 'risk_score']
    list_filter = ['source', 'event_type', 'severity', 'timestamp']
    search_fields = ['title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'
