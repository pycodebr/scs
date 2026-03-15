from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_type', 'cpf_cnpj', 'email', 'phone', 'broker', 'is_active']
    list_filter = ['client_type', 'is_active', 'state', 'broker']
    search_fields = ['name', 'cpf_cnpj', 'email']
    raw_id_fields = ['broker']
