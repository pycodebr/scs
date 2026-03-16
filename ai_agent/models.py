from django.conf import settings
from django.db import models

from utils.models import BrokerageScopedModel, TimeStampedModel


class ChatSession(BrokerageScopedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='chat_sessions', verbose_name='Usuario',
    )
    title = models.CharField('Titulo', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Sessao de Chat'
        verbose_name_plural = 'Sessoes de Chat'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Chat #{self.pk}'


class ChatMessage(BrokerageScopedModel):
    class Role(models.TextChoices):
        USER = 'user', 'Usuario'
        ASSISTANT = 'assistant', 'Assistente'

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE,
        related_name='messages', verbose_name='Sessao',
    )
    role = models.CharField(
        'Papel', max_length=10, choices=Role.choices,
    )
    content = models.TextField('Conteudo')

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_role_display()}: {self.content[:50]}'

    def save(self, *args, **kwargs):
        if self.session_id and not self.brokerage_id:
            self.brokerage = self.session.brokerage
        super().save(*args, **kwargs)


class EntitySummary(TimeStampedModel):
    ENTITY_TYPES = [
        ('client', 'Cliente'),
        ('deal', 'Negociacao'),
        ('policy', 'Apolice'),
        ('proposal', 'Proposta'),
        ('claim', 'Sinistro'),
    ]
    entity_type = models.CharField('Tipo', max_length=20, choices=ENTITY_TYPES)
    entity_id = models.PositiveIntegerField('ID da Entidade')
    brokerage = models.ForeignKey(
        'brokerages.Brokerage',
        on_delete=models.PROTECT,
        related_name='entity_summaries',
        verbose_name='Corretora',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='entity_summaries', verbose_name='Usuario',
    )
    content = models.TextField('Conteudo')
    generated_at = models.DateTimeField('Gerado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Resumo de Entidade'
        verbose_name_plural = 'Resumos de Entidades'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'Resumo {self.entity_type} #{self.entity_id}'


class DashboardInsight(TimeStampedModel):
    brokerage = models.ForeignKey(
        'brokerages.Brokerage',
        on_delete=models.PROTECT,
        related_name='dashboard_insights',
        verbose_name='Corretora',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='dashboard_insights', verbose_name='Usuario',
    )
    content = models.TextField('Conteudo')
    generated_at = models.DateTimeField('Gerado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Insight do Dashboard'
        verbose_name_plural = 'Insights do Dashboard'
        ordering = ['-generated_at']

    def __str__(self):
        return f'Insight para {self.user} em {self.generated_at}'
