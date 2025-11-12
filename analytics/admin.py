from django.contrib import admin
from .models import AnalyticsSummary


@admin.register(AnalyticsSummary)
class AnalyticsSummaryAdmin(admin.ModelAdmin):
    """Admin interface for AnalyticsSummary model."""

    list_display = ['ref_type', 'ref_id', 'date', 'created_at', 'updated_at']
    list_filter = ['ref_type', 'date']
    search_fields = ['ref_id']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'ref_type']

    fieldsets = (
        ('Reference', {
            'fields': ('ref_type', 'ref_id', 'date')
        }),
        ('Metrics', {
            'fields': ('metrics',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
