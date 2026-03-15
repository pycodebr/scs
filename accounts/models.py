from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from utils.models import TimeStampedModel


class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MANAGER = 'manager', 'Gerente'
    BROKER = 'broker', 'Corretor'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField('Email', unique=True)
    first_name = models.CharField('Nome', max_length=150)
    last_name = models.CharField('Sobrenome', max_length=150, blank=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    role = models.CharField(
        'Papel',
        max_length=10,
        choices=Role.choices,
        default=Role.BROKER,
    )
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Acesso ao admin', default=False)
    date_joined = models.DateTimeField('Data de cadastro', auto_now_add=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name

    def get_short_name(self):
        return self.first_name

    def get_initials(self):
        initials = self.first_name[:1].upper()
        if self.last_name:
            initials += self.last_name[:1].upper()
        return initials

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_manager(self):
        return self.role == Role.MANAGER

    @property
    def is_broker(self):
        return self.role == Role.BROKER

    @property
    def can_manage_users(self):
        return self.role in (Role.ADMIN, Role.MANAGER)
