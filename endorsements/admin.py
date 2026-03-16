from django.contrib import admin

from .models import Endorsement, EndorsementDocument


class EndorsementDocumentInline(admin.TabularInline):
    model = EndorsementDocument
    extra = 1
    autocomplete_fields = ['brokerage', 'uploaded_by']


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ['endorsement_number', 'brokerage', 'policy', 'endorsement_type', 'status', 'request_date']
    list_filter = ['brokerage', 'status', 'endorsement_type']
    search_fields = ['endorsement_number', 'policy__policy_number']
    autocomplete_fields = ['brokerage', 'policy', 'requested_by']
    inlines = [EndorsementDocumentInline]


@admin.register(EndorsementDocument)
class EndorsementDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'brokerage', 'endorsement', 'uploaded_by', 'created_at']
    autocomplete_fields = ['brokerage', 'endorsement', 'uploaded_by']
