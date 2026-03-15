from django.contrib import admin

from .models import Claim, ClaimDocument, ClaimTimeline


class ClaimDocumentInline(admin.TabularInline):
    model = ClaimDocument
    extra = 1


class ClaimTimelineInline(admin.TabularInline):
    model = ClaimTimeline
    extra = 0
    readonly_fields = ['action', 'performed_by', 'old_status', 'new_status', 'created_at']


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_number', 'client', 'policy', 'status', 'occurrence_date', 'claimed_amount']
    list_filter = ['status']
    search_fields = ['claim_number', 'client__name', 'policy__policy_number']
    raw_id_fields = ['client', 'broker', 'policy']
    inlines = [ClaimDocumentInline, ClaimTimelineInline]


@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'claim', 'document_type', 'uploaded_by', 'created_at']
    list_filter = ['document_type']


@admin.register(ClaimTimeline)
class ClaimTimelineAdmin(admin.ModelAdmin):
    list_display = ['claim', 'action', 'performed_by', 'created_at']
    list_filter = ['new_status']
