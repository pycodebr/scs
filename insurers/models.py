from django.db import models

from utils.models import TimeStampedModel
from utils.validators import validate_cnpj
from clients.models import UF_CHOICES


class Insurer(TimeStampedModel):
    name = models.CharField('Nome', max_length=255)
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        validators=[validate_cnpj],
    )
    susep_code = models.CharField('Codigo SUSEP', max_length=20, blank=True)
    email = models.EmailField('Email')
    phone = models.CharField('Telefone', max_length=20)
    website = models.URLField('Site', blank=True)
    contact_name = models.CharField('Contato Principal', max_length=150, blank=True)
    contact_email = models.EmailField('Email do Contato', blank=True)
    contact_phone = models.CharField('Telefone do Contato', max_length=20, blank=True)
    zip_code = models.CharField('CEP', max_length=10, blank=True)
    street = models.CharField('Logradouro', max_length=255, blank=True)
    number = models.CharField('Numero', max_length=10, blank=True)
    complement = models.CharField('Complemento', max_length=100, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('UF', max_length=2, choices=UF_CHOICES, blank=True)
    logo = models.ImageField('Logo', upload_to='insurers/', blank=True, null=True)
    is_active = models.BooleanField('Ativa', default=True)
    notes = models.TextField('Observacoes', blank=True)

    class Meta:
        verbose_name = 'Seguradora'
        verbose_name_plural = 'Seguradoras'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.name[:2].upper()


class InsurerBranch(TimeStampedModel):
    insurer = models.ForeignKey(
        Insurer,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name='Seguradora',
    )
    name = models.CharField('Nome do Ramo', max_length=100)
    susep_branch_code = models.CharField('Codigo do Ramo SUSEP', max_length=20, blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Ramo'
        verbose_name_plural = 'Ramos'
        ordering = ['name']
        unique_together = ['insurer', 'name']

    def __str__(self):
        return f'{self.insurer.name} - {self.name}'
