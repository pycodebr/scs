from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BrokerageScopedModel(TimeStampedModel):
    brokerage = models.ForeignKey(
        'brokerages.Brokerage',
        on_delete=models.PROTECT,
        verbose_name='Corretora',
    )

    class Meta:
        abstract = True
