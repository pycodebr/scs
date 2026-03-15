from django import forms


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        label='Data Inicio',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
    )
    end_date = forms.DateField(
        label='Data Fim',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
    )


class ProductionFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from insurers.models import Insurer
        User = get_user_model()
        self.fields['broker'].choices = [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(is_active=True)
        ]
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(is_active=True)
        ]


class CommissionFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['broker'].choices = [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(is_active=True)
        ]


class InsurerPortfolioFilterForm(DateRangeForm):
    status = forms.ChoiceField(
        label='Status', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from policies.models import PolicyStatus
        self.fields['status'].choices = [('', 'Todos')] + list(PolicyStatus.choices)


class InsuranceTypePortfolioFilterForm(DateRangeForm):
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from insurers.models import Insurer
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(is_active=True)
        ]


class ClaimsFilterForm(DateRangeForm):
    status = forms.ChoiceField(
        label='Status', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from claims.models import ClaimStatus
        from insurers.models import Insurer
        self.fields['status'].choices = [('', 'Todos')] + list(ClaimStatus.choices)
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(is_active=True)
        ]


class LossRatioFilterForm(DateRangeForm):
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from insurers.models import Insurer
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(is_active=True)
        ]


class RenewalFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['broker'].choices = [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(is_active=True)
        ]


class ClientsByBrokerFilterForm(forms.Form):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        label='Status', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        choices=[('', 'Todos'), ('active', 'Ativo'), ('inactive', 'Inativo')],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['broker'].choices = [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(is_active=True)
        ]


class CRMFunnelFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    pipeline = forms.ChoiceField(
        label='Pipeline', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from crm.models import Pipeline
        User = get_user_model()
        self.fields['broker'].choices = [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(is_active=True)
        ]
        self.fields['pipeline'].choices = [('', 'Todos')] + [
            (p.pk, p.name) for p in Pipeline.objects.filter(is_active=True)
        ]


class EndorsementFilterForm(DateRangeForm):
    endorsement_type = forms.ChoiceField(
        label='Tipo', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from endorsements.models import EndorsementType
        self.fields['endorsement_type'].choices = [('', 'Todos')] + list(EndorsementType.choices)
