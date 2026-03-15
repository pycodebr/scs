from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Claim, ClaimTimeline


@receiver(pre_save, sender=Claim)
def track_claim_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Claim.objects.get(pk=instance.pk)
    except Claim.DoesNotExist:
        return
    if old.status != instance.status:
        ClaimTimeline.objects.create(
            claim=instance,
            action=f'Status alterado de {old.get_status_display()} para {instance.get_status_display()}',
            performed_by=instance._changed_by if hasattr(instance, '_changed_by') else instance.broker,
            old_status=old.status,
            new_status=instance.status,
        )
