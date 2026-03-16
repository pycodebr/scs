from django.db import models

from utils.models import TimeStampedModel


class BillingCycle(models.TextChoices):
    MONTHLY = 'monthly', 'Mensal'
    YEARLY = 'yearly', 'Anual'


class SubscriptionStatus(models.TextChoices):
    TRIAL = 'trial', 'Trial'
    ACTIVE = 'active', 'Ativa'
    PENDING_PAYMENT = 'pending_payment', 'Pagamento pendente'
    OVERDUE = 'overdue', 'Em atraso'
    CANCELLED = 'cancelled', 'Cancelada'
    INACTIVE = 'inactive', 'Inativa'


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    PAID = 'paid', 'Pago'
    FAILED = 'failed', 'Falhou'
    REFUNDED = 'refunded', 'Reembolsado'
    OVERDUE = 'overdue', 'Em atraso'


class BillingPaymentMethod(models.TextChoices):
    CREDIT_CARD = 'credit_card', 'Cartão de crédito'
    PIX = 'pix', 'PIX'
    BANK_SLIP = 'bank_slip', 'Boleto'
    MANUAL = 'manual', 'Manual'


class Plan(TimeStampedModel):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Descrição', blank=True)
    is_free = models.BooleanField('Plano gratuito', default=False)
    monthly_price_per_user = models.DecimalField(
        'Preço mensal por usuário',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    yearly_price_per_user = models.DecimalField(
        'Preço anual por usuário',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    trial_days = models.PositiveIntegerField('Dias de trial', default=0)
    max_users = models.PositiveIntegerField('Máximo de usuários', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    highlight_label = models.CharField('Destaque', max_length=50, blank=True)
    sort_order = models.PositiveIntegerField('Ordem', default=0)
    modules = models.ManyToManyField(
        'brokerages.SystemModule',
        blank=True,
        related_name='plans',
        verbose_name='Módulos incluídos',
    )

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['sort_order', 'monthly_price_per_user', 'name']

    def __str__(self):
        return self.name


class Subscription(TimeStampedModel):
    brokerage = models.ForeignKey(
        'brokerages.Brokerage',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Corretora',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='Plano',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    billing_cycle = models.CharField(
        'Ciclo',
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    price_per_user = models.DecimalField(
        'Preço por usuário',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    active_user_count = models.PositiveIntegerField('Usuários ativos', default=1)
    started_at = models.DateField('Início')
    trial_ends_at = models.DateField('Fim do trial', blank=True, null=True)
    next_billing_at = models.DateField('Próxima cobrança', blank=True, null=True)
    cancelled_at = models.DateField('Cancelada em', blank=True, null=True)

    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.brokerage} - {self.plan}'


class PaymentRecord(TimeStampedModel):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Assinatura',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        'Forma de pagamento',
        max_length=20,
        choices=BillingPaymentMethod.choices,
        default=BillingPaymentMethod.MANUAL,
    )
    reference_code = models.CharField('Referência', max_length=100, blank=True)
    due_date = models.DateField('Vencimento')
    paid_at = models.DateTimeField('Pago em', blank=True, null=True)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f'{self.subscription} - {self.amount}'
