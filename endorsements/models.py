from django.conf import settings
from django.db import models

from utils.models import BrokerageScopedModel


class EndorsementType(models.TextChoices):
    INCLUSION = 'inclusion', 'Inclusao'
    EXCLUSION = 'exclusion', 'Exclusao'
    MODIFICATION = 'modification', 'Alteracao'
    CANCELLATION = 'cancellation', 'Cancelamento'
    TRANSFER = 'transfer', 'Transferencia'


class EndorsementStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    REQUESTED = 'requested', 'Solicitado'
    UNDER_ANALYSIS = 'under_analysis', 'Em Analise'
    APPROVED = 'approved', 'Aprovado'
    REJECTED = 'rejected', 'Rejeitado'
    APPLIED = 'applied', 'Aplicado'


class Endorsement(BrokerageScopedModel):
    endorsement_number = models.CharField('Numero do Endosso', max_length=50)
    policy = models.ForeignKey(
        'policies.Policy', on_delete=models.PROTECT,
        related_name='endorsements', verbose_name='Apolice',
    )
    endorsement_type = models.CharField(
        'Tipo de Endosso', max_length=20,
        choices=EndorsementType.choices,
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=EndorsementStatus.choices, default=EndorsementStatus.DRAFT,
    )
    request_date = models.DateField('Data da Solicitacao')
    effective_date = models.DateField('Data de Efeito')
    description = models.TextField('Descricao das Alteracoes')
    premium_difference = models.DecimalField(
        'Diferenca de Premio', max_digits=12, decimal_places=2, default=0,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='endorsements', verbose_name='Solicitado por',
    )
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Endosso'
        verbose_name_plural = 'Endossos'
        ordering = ['-request_date']
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'endorsement_number'],
                name='unique_endorsement_number_per_brokerage',
            ),
        ]

    def __str__(self):
        return f'{self.endorsement_number} - {self.policy.policy_number}'

    def save(self, *args, **kwargs):
        if self.policy_id and not self.brokerage_id:
            self.brokerage = self.policy.brokerage
        super().save(*args, **kwargs)


class EndorsementDocument(BrokerageScopedModel):
    endorsement = models.ForeignKey(
        Endorsement, on_delete=models.CASCADE,
        related_name='documents', verbose_name='Endosso',
    )
    title = models.CharField('Titulo', max_length=200)
    file = models.FileField('Arquivo', upload_to='endorsements/documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='uploaded_endorsement_documents', verbose_name='Enviado por',
    )

    class Meta:
        verbose_name = 'Documento do Endosso'
        verbose_name_plural = 'Documentos do Endosso'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.endorsement_id and not self.brokerage_id:
            self.brokerage = self.endorsement.brokerage
        super().save(*args, **kwargs)
