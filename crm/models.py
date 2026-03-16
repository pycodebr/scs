from django.conf import settings
from django.db import models

from utils.models import BrokerageScopedModel


class Pipeline(BrokerageScopedModel):
    name = models.CharField('Nome', max_length=100)
    is_default = models.BooleanField('Pipeline Padrao', default=False)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'name'],
                name='unique_pipeline_name_per_brokerage',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            Pipeline.objects.filter(
                brokerage=self.brokerage,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PipelineStage(BrokerageScopedModel):
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE,
        related_name='stages', verbose_name='Pipeline',
    )
    name = models.CharField('Nome', max_length=100)
    order = models.PositiveIntegerField('Ordem', default=0)
    color = models.CharField('Cor', max_length=7, default='#6c757d')
    is_won = models.BooleanField('Etapa de Ganho', default=False)
    is_lost = models.BooleanField('Etapa de Perda', default=False)

    class Meta:
        verbose_name = 'Etapa do Pipeline'
        verbose_name_plural = 'Etapas do Pipeline'
        ordering = ['pipeline', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'pipeline', 'name'],
                name='unique_pipeline_stage_per_brokerage',
            ),
        ]

    def __str__(self):
        return f'{self.pipeline.name} - {self.name}'

    def save(self, *args, **kwargs):
        if self.pipeline_id and not self.brokerage_id:
            self.brokerage = self.pipeline.brokerage
        super().save(*args, **kwargs)


class DealPriority(models.TextChoices):
    LOW = 'low', 'Baixa'
    MEDIUM = 'medium', 'Media'
    HIGH = 'high', 'Alta'
    URGENT = 'urgent', 'Urgente'


class DealSource(models.TextChoices):
    REFERRAL = 'referral', 'Indicacao'
    WEBSITE = 'website', 'Site'
    PHONE = 'phone', 'Telefone'
    WALK_IN = 'walk_in', 'Presencial'
    SOCIAL_MEDIA = 'social_media', 'Redes Sociais'
    RENEWAL = 'renewal', 'Renovacao'
    OTHER = 'other', 'Outro'


class Deal(BrokerageScopedModel):
    title = models.CharField('Titulo', max_length=200)
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='deals', verbose_name='Cliente',
    )
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='deals', verbose_name='Corretor',
    )
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.PROTECT,
        related_name='deals', verbose_name='Pipeline',
    )
    stage = models.ForeignKey(
        PipelineStage, on_delete=models.PROTECT,
        related_name='deals', verbose_name='Etapa',
    )
    insurance_type = models.ForeignKey(
        'coverages.InsuranceType', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='deals',
        verbose_name='Ramo',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='deals',
        verbose_name='Seguradora',
    )
    expected_value = models.DecimalField(
        'Valor Esperado', max_digits=12, decimal_places=2, default=0,
    )
    expected_close_date = models.DateField(
        'Data Prevista de Fechamento', blank=True, null=True,
    )
    priority = models.CharField(
        'Prioridade', max_length=10,
        choices=DealPriority.choices, default=DealPriority.MEDIUM,
    )
    source = models.CharField(
        'Origem', max_length=20,
        choices=DealSource.choices, default=DealSource.OTHER,
    )
    proposal = models.ForeignKey(
        'policies.Proposal', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='deals',
        verbose_name='Proposta',
    )
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='deals',
        verbose_name='Apolice',
    )
    lost_reason = models.TextField('Motivo da Perda', blank=True)
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Negociacao'
        verbose_name_plural = 'Negociacoes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.client_id and not self.brokerage_id:
            self.brokerage = self.client.brokerage
        if self.pipeline_id and not self.brokerage_id:
            self.brokerage = self.pipeline.brokerage
        super().save(*args, **kwargs)


class ActivityType(models.TextChoices):
    NOTE = 'note', 'Nota'
    CALL = 'call', 'Ligacao'
    EMAIL = 'email', 'Email'
    MEETING = 'meeting', 'Reuniao'
    TASK = 'task', 'Tarefa'


class DealActivity(BrokerageScopedModel):
    deal = models.ForeignKey(
        Deal, on_delete=models.CASCADE,
        related_name='activities', verbose_name='Negociacao',
    )
    activity_type = models.CharField(
        'Tipo', max_length=10,
        choices=ActivityType.choices, default=ActivityType.NOTE,
    )
    title = models.CharField('Titulo', max_length=200)
    description = models.TextField('Descricao', blank=True)
    due_date = models.DateTimeField('Data/Hora', blank=True, null=True)
    is_completed = models.BooleanField('Concluida', default=False)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='deal_activities', verbose_name='Realizado por',
    )

    class Meta:
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_activity_type_display()}: {self.title}'

    def save(self, *args, **kwargs):
        if self.deal_id and not self.brokerage_id:
            self.brokerage = self.deal.brokerage
        super().save(*args, **kwargs)
