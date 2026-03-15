from django import forms

from .models import Renewal


class RenewalForm(forms.ModelForm):
    class Meta:
        model = Renewal
        fields = [
            'policy', 'status', 'due_date', 'contact_date',
            'new_premium', 'new_insurer', 'broker', 'notes',
        ]
        widgets = {
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'contact_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'new_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'new_insurer': forms.Select(attrs={'class': 'form-select'}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['broker'].queryset = User.objects.filter(is_active=True)


class RenewalRenewForm(forms.Form):
    """Form used when renewing — creates a new Policy from the original."""
    policy_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Numero da Nova Apolice',
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        label='Inicio de Vigencia',
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        label='Fim de Vigencia',
    )
    premium_amount = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Valor do Premio',
    )
    insurer = forms.IntegerField(
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Seguradora',
        required=False,
    )
