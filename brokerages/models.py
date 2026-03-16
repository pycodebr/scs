from django.conf import settings
from django.db import models

from clients.models import UF_CHOICES
from utils.models import TimeStampedModel
from utils.validators import validate_cnpj


class BrokerageStatus(models.TextChoices):
    ACTIVE = 'active', 'Ativa'
    INACTIVE = 'inactive', 'Inativa'
    OVERDUE = 'overdue', 'Pagamento em atraso'


class Brokerage(TimeStampedModel):
    legal_name = models.CharField('Razão social', max_length=255)
    trade_name = models.CharField('Nome fantasia', max_length=255, blank=True)
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        validators=[validate_cnpj],
    )
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    zip_code = models.CharField('CEP', max_length=10, blank=True)
    street = models.CharField('Logradouro', max_length=255, blank=True)
    number = models.CharField('Número', max_length=20, blank=True)
    complement = models.CharField('Complemento', max_length=100, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('UF', max_length=2, choices=UF_CHOICES, blank=True)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=BrokerageStatus.choices,
        default=BrokerageStatus.ACTIVE,
    )
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Corretora'
        verbose_name_plural = 'Corretoras'
        ordering = ['legal_name']

    def __str__(self):
        return self.trade_name or self.legal_name

    @property
    def is_active_for_login(self):
        return self.status != BrokerageStatus.INACTIVE


class SystemModule(TimeStampedModel):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    sort_order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Módulo do sistema'
        verbose_name_plural = 'Módulos do sistema'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class BrokerageModule(TimeStampedModel):
    brokerage = models.ForeignKey(
        Brokerage,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Corretora',
    )
    module = models.ForeignKey(
        SystemModule,
        on_delete=models.CASCADE,
        related_name='brokerage_links',
        verbose_name='Módulo',
    )
    is_enabled = models.BooleanField('Habilitado', default=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='granted_brokerage_modules',
        verbose_name='Liberado por',
    )

    class Meta:
        verbose_name = 'Módulo liberado para corretora'
        verbose_name_plural = 'Módulos liberados para corretoras'
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'module'],
                name='unique_brokerage_module',
            ),
        ]

    def __str__(self):
        return f'{self.brokerage} - {self.module}'
