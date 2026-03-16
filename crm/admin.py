from django.contrib import admin

from .models import Pipeline, PipelineStage, Deal, DealActivity


class PipelineStageInline(admin.TabularInline):
    model = PipelineStage
    extra = 1
    ordering = ['order']
    autocomplete_fields = ['brokerage']


class DealActivityInline(admin.TabularInline):
    model = DealActivity
    extra = 0
    readonly_fields = ['created_at']
    autocomplete_fields = ['brokerage', 'performed_by']


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'is_default', 'is_active']
    list_filter = ['brokerage', 'is_active']
    autocomplete_fields = ['brokerage']
    search_fields = ['name', 'brokerage__legal_name']
    inlines = [PipelineStageInline]


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'pipeline', 'order', 'color', 'is_won', 'is_lost']
    list_filter = ['brokerage', 'pipeline']
    ordering = ['pipeline', 'order']
    autocomplete_fields = ['brokerage', 'pipeline']
    search_fields = ['name', 'pipeline__name', 'brokerage__legal_name']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['title', 'brokerage', 'client', 'broker', 'stage', 'expected_value', 'priority']
    list_filter = ['brokerage', 'pipeline', 'stage', 'priority', 'source']
    search_fields = ['title', 'client__name', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage', 'client', 'broker', 'proposal', 'policy', 'pipeline', 'stage', 'insurance_type', 'insurer']
    inlines = [DealActivityInline]


@admin.register(DealActivity)
class DealActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'brokerage', 'deal', 'activity_type', 'is_completed', 'performed_by', 'created_at']
    list_filter = ['brokerage', 'activity_type', 'is_completed']
    autocomplete_fields = ['brokerage', 'deal', 'performed_by']
