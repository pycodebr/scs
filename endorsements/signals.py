from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Endorsement, EndorsementStatus


@receiver(pre_save, sender=Endorsement)
def apply_endorsement_to_policy(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Endorsement.objects.get(pk=instance.pk)
    except Endorsement.DoesNotExist:
        return
    if old.status != instance.status and instance.status == EndorsementStatus.APPLIED:
        policy = instance.policy
        if instance.premium_difference:
            policy.premium_amount += instance.premium_difference
            policy.save(update_fields=['premium_amount'])
