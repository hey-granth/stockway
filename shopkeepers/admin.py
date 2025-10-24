# shopkeepers/admin.py
from django.contrib import admin
from .models import Notification, SupportTicket


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__phone_number', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'notification_type')
        }),
        ('Content', {
            'fields': ('title', 'message', 'order')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'category', 'subject', 'status', 'priority', 'created_at']
    list_filter = ['category', 'status', 'priority', 'created_at']
    search_fields = ['user__phone_number', 'subject', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'category', 'priority')
        }),
        ('Ticket Details', {
            'fields': ('subject', 'description', 'order')
        }),
        ('Status & Resolution', {
            'fields': ('status', 'admin_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['mark_as_resolved', 'mark_as_closed']

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} ticket(s) marked as resolved.")
    mark_as_resolved.short_description = "Mark selected tickets as resolved"

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f"{queryset.count()} ticket(s) marked as closed.")
    mark_as_closed.short_description = "Mark selected tickets as closed"

