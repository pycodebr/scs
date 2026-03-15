from django.contrib import admin

from .models import Insurer, InsurerBranch


class InsurerBranchInline(admin.TabularInline):
    model = InsurerBranch
    extra = 1


@admin.register(Insurer)
class InsurerAdmin(admin.ModelAdmin):
    list_display = ['name', 'cnpj', 'email', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'cnpj']
    inlines = [InsurerBranchInline]


@admin.register(InsurerBranch)
class InsurerBranchAdmin(admin.ModelAdmin):
    list_display = ['insurer', 'name', 'susep_branch_code', 'is_active']
    list_filter = ['is_active', 'insurer']
    search_fields = ['name']
