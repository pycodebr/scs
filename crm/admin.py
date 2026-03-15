from django.contrib import admin

from .models import Pipeline, PipelineStage, Deal, DealActivity


class PipelineStageInline(admin.TabularInline):
    model = PipelineStage
    extra = 1
    ordering = ['order']


class DealActivityInline(admin.TabularInline):
    model = DealActivity
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active']
    list_filter = ['is_active']
    inlines = [PipelineStageInline]


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'pipeline', 'order', 'color', 'is_won', 'is_lost']
    list_filter = ['pipeline']
    ordering = ['pipeline', 'order']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'broker', 'stage', 'expected_value', 'priority']
    list_filter = ['pipeline', 'stage', 'priority', 'source']
    search_fields = ['title', 'client__name']
    raw_id_fields = ['client', 'broker', 'proposal', 'policy']
    inlines = [DealActivityInline]


@admin.register(DealActivity)
class DealActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'deal', 'activity_type', 'is_completed', 'performed_by', 'created_at']
    list_filter = ['activity_type', 'is_completed']
