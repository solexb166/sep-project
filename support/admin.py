from django.contrib import admin
from .models import Ticket, TicketMessage, ChatSession


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ['sender_name', 'created_at', 'is_bot']


def mark_in_progress(modeladmin, request, queryset):
    queryset.update(status='In Progress')
mark_in_progress.short_description = "Mark as In Progress"


def mark_resolved(modeladmin, request, queryset):
    queryset.update(status='Resolved')
mark_resolved.short_description = "Mark as Resolved"


def mark_closed(modeladmin, request, queryset):
    queryset.update(status='Closed')
mark_closed.short_description = "Mark as Closed"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'category', 'subject', 'priority', 'status', 'user', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['ticket_number', 'subject', 'user__email']
    inlines = [TicketMessageInline]
    actions = [mark_in_progress, mark_resolved, mark_closed]
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'page_url', 'started_at', 'message_count']
    readonly_fields = ['session_id', 'started_at']
