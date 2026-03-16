from django.db import models
from django.utils.text import slugify

from utils.models import BrokerageScopedModel


class InsuranceType(BrokerageScopedModel):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', blank=True)
    description = models.TextField('Descricao', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Ramo'
        verbose_name_plural = 'Ramos'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'slug'],
                name='unique_insurance_type_slug_per_brokerage',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Coverage(BrokerageScopedModel):
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
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'insurance_type', 'name'],
                name='unique_coverage_per_brokerage',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.insurance_type_id and not self.brokerage_id:
            self.brokerage = self.insurance_type.brokerage
        super().save(*args, **kwargs)


class CoverageItem(BrokerageScopedModel):
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
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'coverage', 'name'],
                name='unique_coverage_item_per_brokerage',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.coverage_id and not self.brokerage_id:
            self.brokerage = self.coverage.brokerage
        super().save(*args, **kwargs)
