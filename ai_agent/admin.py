from django.contrib import admin

from .models import ChatSession, ChatMessage, DashboardInsight


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('user',)
    search_fields = ('title',)
    inlines = [ChatMessageInline]


@admin.register(DashboardInsight)
class DashboardInsightAdmin(admin.ModelAdmin):
    list_display = ('user', 'generated_at')
    list_filter = ('user',)
    readonly_fields = ('generated_at',)
