from django.db.models.signals import post_save
from django.dispatch import receiver

from policies.models import Policy, PolicyStatus

from .models import Renewal, RenewalStatus


@receiver(post_save, sender=Policy)
def create_renewal_on_policy_save(sender, instance, created, **kwargs):
    """When a policy is saved as active, check if a renewal record needs to be created."""
    if instance.status != PolicyStatus.ACTIVE:
        return

    from datetime import date, timedelta
    today = date.today()
    window_start = today + timedelta(days=60)

    if instance.end_date <= window_start:
        exists = Renewal.objects.filter(
            policy=instance,
            status__in=[
                RenewalStatus.PENDING,
                RenewalStatus.CONTACTED,
                RenewalStatus.QUOTE_SENT,
                RenewalStatus.RENEWED,
            ],
        ).exists()
        if not exists:
            Renewal.objects.create(
                policy=instance,
                status=RenewalStatus.PENDING,
                due_date=instance.end_date,
                broker=instance.broker,
            )
