from django.contrib import admin

from .models import Insurer, InsurerBranch


class InsurerBranchInline(admin.TabularInline):
    model = InsurerBranch
    extra = 1
    autocomplete_fields = ['brokerage']


@admin.register(Insurer)
class InsurerAdmin(admin.ModelAdmin):
    list_display = ['name', 'brokerage', 'cnpj', 'email', 'phone', 'is_active']
    list_filter = ['brokerage', 'is_active']
    search_fields = ['name', 'cnpj', 'brokerage__legal_name']
    autocomplete_fields = ['brokerage']
    inlines = [InsurerBranchInline]


@admin.register(InsurerBranch)
class InsurerBranchAdmin(admin.ModelAdmin):
    list_display = ['insurer', 'brokerage', 'name', 'susep_branch_code', 'is_active']
    list_filter = ['brokerage', 'is_active', 'insurer']
    search_fields = ['name']
    autocomplete_fields = ['brokerage', 'insurer']
