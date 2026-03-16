from django.contrib import admin

from .models import Brokerage, SystemModule, BrokerageModule


@admin.register(Brokerage)
class BrokerageAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'cnpj', 'status', 'city', 'state', 'created_at')
    list_filter = ('status', 'state')
    search_fields = ('legal_name', 'trade_name', 'cnpj', 'email')


@admin.register(SystemModule)
class SystemModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BrokerageModule)
class BrokerageModuleAdmin(admin.ModelAdmin):
    list_display = ('brokerage', 'module', 'is_enabled', 'granted_by', 'updated_at')
    list_filter = ('is_enabled', 'module')
    search_fields = ('brokerage__legal_name', 'brokerage__cnpj', 'module__name')
    autocomplete_fields = ('brokerage', 'module', 'granted_by')
