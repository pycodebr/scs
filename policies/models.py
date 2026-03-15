from django.conf import settings
from django.db import models

from utils.models import TimeStampedModel


class ProposalStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    SUBMITTED = 'submitted', 'Enviada'
    UNDER_ANALYSIS = 'under_analysis', 'Em Analise'
    APPROVED = 'approved', 'Aprovada'
    REJECTED = 'rejected', 'Recusada'
    CANCELLED = 'cancelled', 'Cancelada'


class PolicyStatus(models.TextChoices):
    ACTIVE = 'active', 'Ativa'
    EXPIRED = 'expired', 'Vencida'
    CANCELLED = 'cancelled', 'Cancelada'
    SUSPENDED = 'suspended', 'Suspensa'
    PENDING = 'pending', 'Pendente'


class PaymentMethod(models.TextChoices):
    BANK_SLIP = 'bank_slip', 'Boleto Bancario'
    CREDIT_CARD = 'credit_card', 'Cartao de Credito'
    DEBIT = 'debit', 'Debito em Conta'
    PIX = 'pix', 'PIX'
    INVOICE = 'invoice', 'Fatura'


class DocumentType(models.TextChoices):
    PROPOSAL = 'proposal', 'Proposta'
    POLICY = 'policy', 'Apolice'
    CI = 'ci', 'CI'
    OTHER = 'other', 'Outros'


class Proposal(TimeStampedModel):
    proposal_number = models.CharField('Numero da Proposta', max_length=50, unique=True)
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='proposals', verbose_name='Cliente',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer', on_delete=models.PROTECT,
        related_name='proposals', verbose_name='Seguradora',
    )
    insurance_type = models.ForeignKey(
        'coverages.InsuranceType', on_delete=models.PROTECT,
        related_name='proposals', verbose_name='Ramo',
    )
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='proposals', verbose_name='Corretor',
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=ProposalStatus.choices, default=ProposalStatus.DRAFT,
    )
    submission_date = models.DateField('Data de Envio')
    response_date = models.DateField('Data da Resposta', blank=True, null=True)
    premium_amount = models.DecimalField(
        'Valor do Premio', max_digits=12, decimal_places=2, default=0,
    )
    notes = models.TextField('Observacoes', blank=True)
    rejection_reason = models.TextField('Motivo da Recusa', blank=True)

    class Meta:
        verbose_name = 'Proposta'
        verbose_name_plural = 'Propostas'
        ordering = ['-submission_date']

    def __str__(self):
        return f'{self.proposal_number} - {self.client.name}'


class Policy(TimeStampedModel):
    policy_number = models.CharField('Numero da Apolice', max_length=50, unique=True)
    proposal = models.ForeignKey(
        Proposal, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='policies',
        verbose_name='Proposta de Origem',
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='policies', verbose_name='Cliente',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer', on_delete=models.PROTECT,
        related_name='policies', verbose_name='Seguradora',
    )
    insurance_type = models.ForeignKey(
        'coverages.InsuranceType', on_delete=models.PROTECT,
        related_name='policies', verbose_name='Ramo',
    )
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='policies', verbose_name='Corretor',
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=PolicyStatus.choices, default=PolicyStatus.PENDING,
    )
    start_date = models.DateField('Inicio de Vigencia')
    end_date = models.DateField('Fim de Vigencia')
    premium_amount = models.DecimalField(
        'Valor do Premio', max_digits=12, decimal_places=2, default=0,
    )
    insured_amount = models.DecimalField(
        'Importancia Segurada', max_digits=14, decimal_places=2, default=0,
    )
    commission_rate = models.DecimalField(
        'Comissao (%)', max_digits=5, decimal_places=2, default=0,
    )
    commission_amount = models.DecimalField(
        'Valor da Comissao', max_digits=12, decimal_places=2, default=0,
    )
    installments = models.PositiveIntegerField('Parcelas', default=1)
    payment_method = models.CharField(
        'Forma de Pagamento', max_length=20,
        choices=PaymentMethod.choices, default=PaymentMethod.BANK_SLIP,
    )
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Apolice'
        verbose_name_plural = 'Apolices'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.policy_number} - {self.client.name}'

    @property
    def is_expiring_soon(self):
        from datetime import date, timedelta
        today = date.today()
        return self.status == PolicyStatus.ACTIVE and self.end_date <= today + timedelta(days=30)

    @property
    def is_expired(self):
        from datetime import date
        return self.end_date < date.today()


class PolicyCoverage(TimeStampedModel):
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE,
        related_name='coverages', verbose_name='Apolice',
    )
    coverage = models.ForeignKey(
        'coverages.Coverage', on_delete=models.PROTECT,
        related_name='policy_coverages', verbose_name='Cobertura',
    )
    insured_amount = models.DecimalField(
        'Valor Segurado', max_digits=14, decimal_places=2, default=0,
    )
    deductible = models.DecimalField(
        'Franquia', max_digits=12, decimal_places=2, default=0,
    )
    premium_amount = models.DecimalField(
        'Premio', max_digits=12, decimal_places=2, default=0,
    )
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Cobertura Contratada'
        verbose_name_plural = 'Coberturas Contratadas'

    def __str__(self):
        return f'{self.policy.policy_number} - {self.coverage.name}'


class PolicyDocument(TimeStampedModel):
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE,
        related_name='documents', verbose_name='Apolice',
    )
    title = models.CharField('Titulo', max_length=200)
    file = models.FileField('Arquivo', upload_to='policies/documents/')
    document_type = models.CharField(
        'Tipo', max_length=20,
        choices=DocumentType.choices, default=DocumentType.OTHER,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='uploaded_policy_documents', verbose_name='Enviado por',
    )

    class Meta:
        verbose_name = 'Documento da Apolice'
        verbose_name_plural = 'Documentos da Apolice'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
