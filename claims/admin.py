from django.contrib import admin

from .models import Claim, ClaimDocument, ClaimTimeline


class ClaimDocumentInline(admin.TabularInline):
    model = ClaimDocument
    extra = 1
    autocomplete_fields = ['brokerage', 'uploaded_by']


class ClaimTimelineInline(admin.TabularInline):
    model = ClaimTimeline
    extra = 0
    readonly_fields = ['action', 'performed_by', 'old_status', 'new_status', 'created_at']
    autocomplete_fields = ['brokerage', 'performed_by']


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_number', 'brokerage', 'client', 'policy', 'status', 'occurrence_date', 'claimed_amount']
    list_filter = ['brokerage', 'status']
    search_fields = ['claim_number', 'client__name', 'policy__policy_number']
    autocomplete_fields = ['brokerage', 'client', 'broker', 'policy']
    inlines = [ClaimDocumentInline, ClaimTimelineInline]


@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'brokerage', 'claim', 'document_type', 'uploaded_by', 'created_at']
    list_filter = ['brokerage', 'document_type']
    autocomplete_fields = ['brokerage', 'claim', 'uploaded_by']


@admin.register(ClaimTimeline)
class ClaimTimelineAdmin(admin.ModelAdmin):
    list_display = ['claim', 'brokerage', 'action', 'performed_by', 'created_at']
    list_filter = ['brokerage', 'new_status']
    autocomplete_fields = ['brokerage', 'claim', 'performed_by']
