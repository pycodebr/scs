from django.apps import apps
from django.db.models.signals import post_migrate
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from brokerages.services import sync_brokerage_modules

from .models import Plan, Subscription


@receiver(post_migrate)
def ensure_billing_catalog(sender, **kwargs):
    if sender.label != 'billing':
        return

    # Avoid touching the catalog before the billing app tables exist.
    try:
        apps.get_model('billing', 'Plan')
    except LookupError:
        return

    from .services import bootstrap_catalog

    bootstrap_catalog()


@receiver(pre_save, sender=Subscription)
def remember_previous_subscription_plan(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_plan_id = None
        return

    instance._previous_plan_id = (
        sender.objects.filter(pk=instance.pk).values_list('plan_id', flat=True).first()
    )


@receiver(post_save, sender=Subscription)
def sync_modules_after_subscription_change(sender, instance, created, **kwargs):
    previous_plan_id = getattr(instance, '_previous_plan_id', None)
    if not created and previous_plan_id == instance.plan_id:
        return

    sync_brokerage_modules(instance.brokerage, instance.plan)


@receiver(m2m_changed, sender=Plan.modules.through)
def sync_modules_after_plan_module_change(sender, instance, action, **kwargs):
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return

    latest_subscription_ids = {}
    for subscription in Subscription.objects.select_related('brokerage', 'plan').order_by(
        'brokerage_id', '-created_at', '-pk'
    ):
        latest_subscription_ids.setdefault(subscription.brokerage_id, subscription.pk)

    for subscription in Subscription.objects.filter(pk__in=latest_subscription_ids.values(), plan=instance):
        sync_brokerage_modules(subscription.brokerage, instance)
