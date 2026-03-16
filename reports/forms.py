from django import forms


def get_broker_choices_for_user(user):
    from django.contrib.auth import get_user_model

    if user.role == 'admin':
        User = get_user_model()
        return [('', 'Todos')] + [
            (u.pk, u.get_full_name()) for u in User.objects.filter(
                is_active=True,
                is_platform_admin=False,
                brokerage=user.brokerage,
            )
        ]

    return [(user.pk, user.get_full_name() or user.email)]


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
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from insurers.models import Insurer
        self.fields['broker'].choices = get_broker_choices_for_user(user)
        if user.role != 'admin':
            self.fields['broker'].initial = user.pk
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(
                is_active=True,
                brokerage=user.brokerage,
            )
        ]


class CommissionFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['broker'].choices = get_broker_choices_for_user(user)
        if user.role != 'admin':
            self.fields['broker'].initial = user.pk


class InsurerPortfolioFilterForm(DateRangeForm):
    status = forms.ChoiceField(
        label='Status', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from policies.models import PolicyStatus
        self.fields['status'].choices = [('', 'Todos')] + list(PolicyStatus.choices)


class InsuranceTypePortfolioFilterForm(DateRangeForm):
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from insurers.models import Insurer
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(
                is_active=True,
                brokerage=user.brokerage,
            )
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
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from claims.models import ClaimStatus
        from insurers.models import Insurer
        self.fields['status'].choices = [('', 'Todos')] + list(ClaimStatus.choices)
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(
                is_active=True,
                brokerage=user.brokerage,
            )
        ]


class LossRatioFilterForm(DateRangeForm):
    insurer = forms.ChoiceField(
        label='Seguradora', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from insurers.models import Insurer
        self.fields['insurer'].choices = [('', 'Todas')] + [
            (i.pk, i.name) for i in Insurer.objects.filter(
                is_active=True,
                brokerage=user.brokerage,
            )
        ]


class RenewalFilterForm(DateRangeForm):
    broker = forms.ChoiceField(
        label='Corretor', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['broker'].choices = get_broker_choices_for_user(user)
        if user.role != 'admin':
            self.fields['broker'].initial = user.pk


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
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['broker'].choices = get_broker_choices_for_user(user)
        if user.role != 'admin':
            self.fields['broker'].initial = user.pk


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
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from crm.models import Pipeline
        self.fields['broker'].choices = get_broker_choices_for_user(user)
        if user.role != 'admin':
            self.fields['broker'].initial = user.pk
        self.fields['pipeline'].choices = [('', 'Todos')] + [
            (p.pk, p.name) for p in Pipeline.objects.filter(
                is_active=True,
                brokerage=user.brokerage,
            )
        ]


class EndorsementFilterForm(DateRangeForm):
    endorsement_type = forms.ChoiceField(
        label='Tipo', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        from endorsements.models import EndorsementType
        self.fields['endorsement_type'].choices = [('', 'Todos')] + list(EndorsementType.choices)
