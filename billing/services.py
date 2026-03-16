from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from brokerages.services import bootstrap_system_modules, sync_brokerage_modules

from .models import (
    BillingCycle,
    BillingPaymentMethod,
    PaymentRecord,
    PaymentStatus,
    Plan,
    Subscription,
    SubscriptionStatus,
)


DEFAULT_PLANS = [
    {
        'slug': 'free',
        'name': 'Free',
        'description': 'Comece sem cartão e valide o fluxo da corretora.',
        'is_free': True,
        'monthly_price_per_user': Decimal('0.00'),
        'yearly_price_per_user': Decimal('0.00'),
        'trial_days': 0,
        'max_users': 2,
        'highlight_label': 'Comece agora',
        'modules': ['dashboard', 'crm', 'renewals'],
    },
    {
        'slug': 'smart',
        'name': 'Smart',
        'description': 'Operação completa com IA e relatórios.',
        'is_free': False,
        'monthly_price_per_user': Decimal('69.90'),
        'yearly_price_per_user': Decimal('59.90'),
        'trial_days': 7,
        'max_users': None,
        'highlight_label': 'Mais popular',
        'modules': ['dashboard', 'crm', 'claims', 'endorsements', 'renewals', 'reports', 'ai_agent'],
    },
    {
        'slug': 'scale',
        'name': 'Scale',
        'description': 'Plano para times maiores e gestão inteligente completa.',
        'is_free': False,
        'monthly_price_per_user': Decimal('119.90'),
        'yearly_price_per_user': Decimal('99.90'),
        'trial_days': 14,
        'max_users': None,
        'highlight_label': 'IA avançada',
        'modules': ['dashboard', 'crm', 'claims', 'endorsements', 'renewals', 'reports', 'ai_agent'],
    },
]


def bootstrap_catalog():
    modules = {module.slug: module for module in bootstrap_system_modules()}
    plans = []
    for index, raw_plan_data in enumerate(DEFAULT_PLANS):
        plan_data = raw_plan_data.copy()
        module_slugs = plan_data.pop('modules')
        plan, _ = Plan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults={
                **plan_data,
                'sort_order': index,
                'is_active': True,
            },
        )
        if not plan.modules.exists():
            plan.modules.set([modules[slug] for slug in module_slugs if slug in modules])
        plans.append(plan)
    return plans


def create_subscription_for_signup(*, brokerage, plan, active_user_count=1, granted_by=None):
    today = timezone.localdate()
    price_per_user = plan.monthly_price_per_user
    if plan.is_free:
        status = SubscriptionStatus.ACTIVE
        next_billing_at = None
        trial_ends_at = None
    elif plan.trial_days:
        status = SubscriptionStatus.TRIAL
        trial_ends_at = today + timedelta(days=plan.trial_days)
        next_billing_at = trial_ends_at
    else:
        status = SubscriptionStatus.PENDING_PAYMENT
        trial_ends_at = None
        next_billing_at = today

    subscription = Subscription.objects.create(
        brokerage=brokerage,
        plan=plan,
        status=status,
        billing_cycle=BillingCycle.MONTHLY,
        price_per_user=price_per_user,
        active_user_count=active_user_count,
        started_at=today,
        trial_ends_at=trial_ends_at,
        next_billing_at=next_billing_at,
    )

    if not plan.is_free:
        PaymentRecord.objects.create(
            subscription=subscription,
            status=PaymentStatus.PENDING,
            amount=price_per_user * active_user_count,
            payment_method=BillingPaymentMethod.MANUAL,
            due_date=next_billing_at or today,
            notes='Pagamento pendente até integração com gateway.',
        )

    sync_brokerage_modules(brokerage, plan, granted_by=granted_by)
    return subscription
