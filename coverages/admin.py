from django.contrib import admin

from .models import InsuranceType, Coverage, CoverageItem


@admin.register(InsuranceType)
class InsuranceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']
    search_fields = ['name']


class CoverageItemInline(admin.TabularInline):
    model = CoverageItem
    extra = 1


@admin.register(Coverage)
class CoverageAdmin(admin.ModelAdmin):
    list_display = ['name', 'insurance_type', 'is_active']
    list_filter = ['is_active', 'insurance_type']
    search_fields = ['name']
    inlines = [CoverageItemInline]


@admin.register(CoverageItem)
class CoverageItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'coverage', 'is_active']
    list_filter = ['is_active', 'coverage__insurance_type']
    search_fields = ['name']
