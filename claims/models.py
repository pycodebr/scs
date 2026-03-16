from django.conf import settings
from django.db import models

from utils.models import BrokerageScopedModel


class ClaimStatus(models.TextChoices):
    OPEN = 'open', 'Aberto'
    UNDER_ANALYSIS = 'under_analysis', 'Em Analise'
    DOCUMENTATION_PENDING = 'documentation_pending', 'Pendente de Documentacao'
    APPROVED = 'approved', 'Aprovado'
    PARTIALLY_APPROVED = 'partially_approved', 'Parcialmente Aprovado'
    DENIED = 'denied', 'Negado'
    PAID = 'paid', 'Pago'
    CLOSED = 'closed', 'Encerrado'


class ClaimDocumentType(models.TextChoices):
    REPORT = 'report', 'Laudo'
    PHOTO = 'photo', 'Foto'
    INVOICE = 'invoice', 'Nota Fiscal'
    POLICE_REPORT = 'police_report', 'Boletim de Ocorrencia'
    OTHER = 'other', 'Outros'


class Claim(BrokerageScopedModel):
    claim_number = models.CharField('Numero do Sinistro', max_length=50)
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.PROTECT,
        related_name='claims', verbose_name='Apolice',
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='claims', verbose_name='Cliente',
    )
    status = models.CharField(
        'Status', max_length=30,
        choices=ClaimStatus.choices, default=ClaimStatus.OPEN,
    )
    occurrence_date = models.DateField('Data da Ocorrencia')
    notification_date = models.DateField('Data da Notificacao')
    description = models.TextField('Descricao')
    location = models.CharField('Local da Ocorrencia', max_length=255, blank=True)
    claimed_amount = models.DecimalField(
        'Valor Reclamado', max_digits=14, decimal_places=2, default=0,
    )
    approved_amount = models.DecimalField(
        'Valor Aprovado', max_digits=14, decimal_places=2, blank=True, null=True,
    )
    resolution_date = models.DateField('Data de Resolucao', blank=True, null=True)
    resolution_notes = models.TextField('Observacoes da Resolucao', blank=True)
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='claims', verbose_name='Corretor',
    )

    class Meta:
        verbose_name = 'Sinistro'
        verbose_name_plural = 'Sinistros'
        ordering = ['-occurrence_date']
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'claim_number'],
                name='unique_claim_number_per_brokerage',
            ),
        ]

    def __str__(self):
        return f'{self.claim_number} - {self.client.name}'

    def save(self, *args, **kwargs):
        if self.policy_id and not self.brokerage_id:
            self.brokerage = self.policy.brokerage
        super().save(*args, **kwargs)


class ClaimDocument(BrokerageScopedModel):
    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE,
        related_name='documents', verbose_name='Sinistro',
    )
    title = models.CharField('Titulo', max_length=200)
    file = models.FileField('Arquivo', upload_to='claims/documents/')
    document_type = models.CharField(
        'Tipo', max_length=20,
        choices=ClaimDocumentType.choices, default=ClaimDocumentType.OTHER,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='uploaded_claim_documents', verbose_name='Enviado por',
    )

    class Meta:
        verbose_name = 'Documento do Sinistro'
        verbose_name_plural = 'Documentos do Sinistro'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.claim_id and not self.brokerage_id:
            self.brokerage = self.claim.brokerage
        super().save(*args, **kwargs)


class ClaimTimeline(BrokerageScopedModel):
    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE,
        related_name='timeline', verbose_name='Sinistro',
    )
    action = models.CharField('Acao', max_length=200)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='claim_actions', verbose_name='Realizado por',
    )
    old_status = models.CharField('Status Anterior', max_length=30, blank=True)
    new_status = models.CharField('Novo Status', max_length=30, blank=True)
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Historico'
        verbose_name_plural = 'Historico'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.claim.claim_number} - {self.action}'

    def save(self, *args, **kwargs):
        if self.claim_id and not self.brokerage_id:
            self.brokerage = self.claim.brokerage
        super().save(*args, **kwargs)
