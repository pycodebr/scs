from django.contrib import admin

from .models import InsuranceType, Coverage, CoverageItem


@admin.register(InsuranceType)
class InsuranceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['brokerage', 'is_active']
    search_fields = ['name', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage']


class CoverageItemInline(admin.TabularInline):
    model = CoverageItem
    extra = 1
    autocomplete_fields = ['brokerage']


@admin.register(Coverage)
class CoverageAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'insurance_type', 'is_active']
    list_filter = ['brokerage', 'is_active', 'insurance_type']
    search_fields = ['name', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage', 'insurance_type']
    inlines = [CoverageItemInline]


@admin.register(CoverageItem)
class CoverageItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'coverage', 'is_active']
    list_filter = ['brokerage', 'is_active', 'coverage__insurance_type']
    search_fields = ['name']
    autocomplete_fields = ['brokerage', 'coverage']
