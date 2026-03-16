from django.contrib import admin

from .models import ChatSession, ChatMessage, DashboardInsight, EntitySummary


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')
    autocomplete_fields = ('brokerage',)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'brokerage', 'user', 'created_at', 'updated_at')
    list_filter = ('brokerage', 'user',)
    search_fields = ('title', 'brokerage__legal_name')
    autocomplete_fields = ('brokerage', 'user')
    inlines = [ChatMessageInline]


@admin.register(DashboardInsight)
class DashboardInsightAdmin(admin.ModelAdmin):
    list_display = ('user', 'brokerage', 'generated_at')
    list_filter = ('brokerage', 'user',)
    readonly_fields = ('generated_at',)
    autocomplete_fields = ('brokerage', 'user')


@admin.register(EntitySummary)
class EntitySummaryAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'brokerage', 'user', 'generated_at')
    list_filter = ('brokerage', 'entity_type')
    search_fields = ('entity_id', 'brokerage__legal_name', 'user__email')
    readonly_fields = ('generated_at',)
    autocomplete_fields = ('brokerage', 'user')
