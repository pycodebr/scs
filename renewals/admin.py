from django.contrib import admin

from .models import Renewal


@admin.register(Renewal)
class RenewalAdmin(admin.ModelAdmin):
    list_display = ['policy', 'status', 'due_date', 'broker', 'contact_date', 'new_premium']
    list_filter = ['status']
    search_fields = ['policy__policy_number', 'policy__client__name']
    raw_id_fields = ['policy', 'renewed_policy', 'broker', 'new_insurer']
