from django import forms
from django.contrib.auth import get_user_model

from brokerages.models import Brokerage
from utils.validators import validate_cnpj


class SignupForm(forms.Form):
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    phone = forms.CharField(
        label='Telefone',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    legal_name = forms.CharField(
        label='Razão social',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    trade_name = forms.CharField(
        label='Nome fantasia',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
        validators=[validate_cnpj],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    brokerage_email = forms.EmailField(
        label='Email da corretora',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    brokerage_phone = forms.CharField(
        label='Telefone da corretora',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    zip_code = forms.CharField(
        label='CEP',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    street = forms.CharField(
        label='Logradouro',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    number = forms.CharField(
        label='Número',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    complement = forms.CharField(
        label='Complemento',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    neighborhood = forms.CharField(
        label='Bairro',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    city = forms.CharField(
        label='Cidade',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    state = forms.ChoiceField(
        label='UF',
        required=False,
        choices=[('', '---------')] + Brokerage._meta.get_field('state').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    plan = forms.ModelChoiceField(
        queryset=None,
        label='Plano',
        empty_label=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        plan_queryset = kwargs.pop('plan_queryset')
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = plan_queryset

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        user_model = get_user_model()
        if user_model.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe um usuário com este email.')
        return email

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        if Brokerage.objects.filter(cnpj=cnpj).exists():
            raise forms.ValidationError('Já existe uma corretora com este CNPJ.')
        return cnpj

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'As senhas não conferem.')
        return cleaned_data
