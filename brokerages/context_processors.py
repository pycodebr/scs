from billing.models import Subscription


def brokerage_context(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or user.is_platform_admin or user.is_superuser:
        return {
            'current_brokerage': None,
            'enabled_modules': set(),
            'current_subscription': None,
        }

    brokerage = getattr(user, 'brokerage', None)
    enabled_modules = set()
    module_overrides = {}
    subscription = None

    if brokerage:
        module_overrides = dict(
            brokerage.modules.filter(module__is_active=True)
            .values_list('module__slug', 'is_enabled')
        )
        enabled_modules = {slug for slug, is_enabled in module_overrides.items() if is_enabled}
        subscription = Subscription.objects.filter(
            brokerage=brokerage,
        ).select_related('plan').order_by('-created_at').first()
        if subscription:
            plan_modules = set(
                subscription.plan.modules.filter(is_active=True).values_list('slug', flat=True)
            )
            enabled_modules |= {slug for slug in plan_modules if slug not in module_overrides}

    return {
        'current_brokerage': brokerage,
        'enabled_modules': enabled_modules,
        'current_subscription': subscription,
    }
