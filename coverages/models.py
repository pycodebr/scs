from django.db import models
from django.utils.text import slugify

from utils.models import TimeStampedModel


class InsuranceType(TimeStampedModel):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True, blank=True)
    description = models.TextField('Descricao', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Ramo'
        verbose_name_plural = 'Ramos'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Coverage(TimeStampedModel):
    insurance_type = models.ForeignKey(
        InsuranceType,
        on_delete=models.CASCADE,
        related_name='coverages',
        verbose_name='Ramo',
    )
    name = models.CharField('Nome', max_length=200)
    description = models.TextField('Descricao', blank=True)
    is_active = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Cobertura'
        verbose_name_plural = 'Coberturas'
        ordering = ['name']

    def __str__(self):
        return self.name


class CoverageItem(TimeStampedModel):
    coverage = models.ForeignKey(
        Coverage,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Cobertura',
    )
    name = models.CharField('Nome', max_length=200)
    description = models.TextField('Descricao', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Item de Cobertura'
        verbose_name_plural = 'Itens de Cobertura'
        ordering = ['name']

    def __str__(self):
        return self.name
