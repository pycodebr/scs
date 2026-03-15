from django.contrib import admin

from .models import Endorsement, EndorsementDocument


class EndorsementDocumentInline(admin.TabularInline):
    model = EndorsementDocument
    extra = 1


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ['endorsement_number', 'policy', 'endorsement_type', 'status', 'request_date']
    list_filter = ['status', 'endorsement_type']
    search_fields = ['endorsement_number', 'policy__policy_number']
    raw_id_fields = ['requested_by']
    inlines = [EndorsementDocumentInline]


@admin.register(EndorsementDocument)
class EndorsementDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'endorsement', 'uploaded_by', 'created_at']
