from django.contrib import admin

from .models import Plan, Subscription, PaymentRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'is_free', 'monthly_price_per_user',
        'yearly_price_per_user', 'is_active', 'sort_order',
    )
    list_filter = ('is_free', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('modules',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'brokerage', 'plan', 'status', 'billing_cycle',
        'price_per_user', 'active_user_count', 'next_billing_at',
    )
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('brokerage__legal_name', 'brokerage__cnpj', 'plan__name')
    autocomplete_fields = ('brokerage', 'plan')


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'status', 'amount', 'payment_method', 'due_date', 'paid_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('subscription__brokerage__legal_name', 'reference_code')
    autocomplete_fields = ('subscription',)
