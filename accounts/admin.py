from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'first_name', 'last_name', 'brokerage',
        'role', 'is_platform_admin', 'is_active', 'is_staff',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_platform_admin', 'brokerage')
    search_fields = ('email', 'first_name', 'last_name', 'brokerage__legal_name', 'brokerage__cnpj')
    ordering = ('email',)
    autocomplete_fields = ('brokerage',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'cpf', 'phone', 'avatar', 'brokerage')}),
        ('Permissões', {'fields': ('role', 'is_platform_admin', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'brokerage',
                'role', 'is_platform_admin', 'password1', 'password2',
            ),
        }),
    )
