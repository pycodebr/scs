from django.conf import settings
from django.db import models

from utils.models import TimeStampedModel
from utils.validators import validate_cpf_cnpj


UF_CHOICES = [
    ('AC', 'AC'), ('AL', 'AL'), ('AP', 'AP'), ('AM', 'AM'), ('BA', 'BA'),
    ('CE', 'CE'), ('DF', 'DF'), ('ES', 'ES'), ('GO', 'GO'), ('MA', 'MA'),
    ('MT', 'MT'), ('MS', 'MS'), ('MG', 'MG'), ('PA', 'PA'), ('PB', 'PB'),
    ('PR', 'PR'), ('PE', 'PE'), ('PI', 'PI'), ('RJ', 'RJ'), ('RN', 'RN'),
    ('RS', 'RS'), ('RO', 'RO'), ('RR', 'RR'), ('SC', 'SC'), ('SP', 'SP'),
    ('SE', 'SE'), ('TO', 'TO'),
]


class ClientType(models.TextChoices):
    INDIVIDUAL = 'pf', 'Pessoa Fisica'
    COMPANY = 'pj', 'Pessoa Juridica'


class Gender(models.TextChoices):
    MALE = 'M', 'Masculino'
    FEMALE = 'F', 'Feminino'
    OTHER = 'O', 'Outro'


class MaritalStatus(models.TextChoices):
    SINGLE = 'single', 'Solteiro(a)'
    MARRIED = 'married', 'Casado(a)'
    DIVORCED = 'divorced', 'Divorciado(a)'
    WIDOWED = 'widowed', 'Viuvo(a)'
    SEPARATED = 'separated', 'Separado(a)'


class Client(TimeStampedModel):
    client_type = models.CharField(
        'Tipo',
        max_length=2,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL,
    )
    name = models.CharField('Nome / Razao Social', max_length=255)
    cpf_cnpj = models.CharField(
        'CPF / CNPJ',
        max_length=18,
        unique=True,
        validators=[validate_cpf_cnpj],
    )
    rg_ie = models.CharField('RG / IE', max_length=20, blank=True)
    birth_date = models.DateField('Data de Nascimento', blank=True, null=True)
    gender = models.CharField(
        'Genero',
        max_length=1,
        choices=Gender.choices,
        blank=True,
    )
    marital_status = models.CharField(
        'Estado Civil',
        max_length=10,
        choices=MaritalStatus.choices,
        blank=True,
    )
    occupation = models.CharField('Profissao', max_length=100, blank=True)
    email = models.EmailField('Email')
    phone = models.CharField('Telefone', max_length=20)
    secondary_phone = models.CharField('Telefone Secundario', max_length=20, blank=True)
    zip_code = models.CharField('CEP', max_length=10, blank=True)
    street = models.CharField('Logradouro', max_length=255, blank=True)
    number = models.CharField('Numero', max_length=10, blank=True)
    complement = models.CharField('Complemento', max_length=100, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('UF', max_length=2, choices=UF_CHOICES, blank=True)
    notes = models.TextField('Observacoes', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    broker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='clients',
        verbose_name='Corretor',
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.name[:2].upper()
