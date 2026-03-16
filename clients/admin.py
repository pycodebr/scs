from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'client_type', 'cpf_cnpj', 'email', 'phone', 'broker', 'is_active']
    list_filter = ['brokerage', 'client_type', 'is_active', 'state', 'broker']
    search_fields = ['name', 'cpf_cnpj', 'email', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage', 'broker']
