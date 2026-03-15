from django.conf import settings
from django.db import models

from utils.models import TimeStampedModel


class RenewalStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    CONTACTED = 'contacted', 'Cliente Contatado'
    QUOTE_SENT = 'quote_sent', 'Cotacao Enviada'
    RENEWED = 'renewed', 'Renovada'
    NOT_RENEWED = 'not_renewed', 'Nao Renovada'
    CANCELLED = 'cancelled', 'Cancelada'


class Renewal(TimeStampedModel):
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.PROTECT,
        related_name='renewals', verbose_name='Apolice Original',
    )
    renewed_policy = models.ForeignKey(
        'policies.Policy', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='renewal_origin',
        verbose_name='Nova Apolice',
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=RenewalStatus.choices, default=RenewalStatus.PENDING,
    )
    due_date = models.DateField('Data Limite para Renovacao')
    contact_date = models.DateField('Data do Contato', blank=True, null=True)
    new_premium = models.DecimalField(
        'Novo Valor do Premio', max_digits=12, decimal_places=2,
        blank=True, null=True,
    )
    new_insurer = models.ForeignKey(
        'insurers.Insurer', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='renewals',
        verbose_name='Nova Seguradora',
    )
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='renewals', verbose_name='Corretor',
    )
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Renovacao'
        verbose_name_plural = 'Renovacoes'
        ordering = ['due_date']

    def __str__(self):
        return f'Renovacao {self.policy.policy_number} - {self.get_status_display()}'

    @property
    def is_urgent(self):
        from datetime import date, timedelta
        return self.status == RenewalStatus.PENDING and self.due_date <= date.today() + timedelta(days=15)

    @property
    def is_overdue(self):
        from datetime import date
        return self.status in (RenewalStatus.PENDING, RenewalStatus.CONTACTED, RenewalStatus.QUOTE_SENT) and self.due_date < date.today()
