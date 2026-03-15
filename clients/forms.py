from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'client_type', 'name', 'cpf_cnpj', 'rg_ie',
            'birth_date', 'gender', 'marital_status', 'occupation',
            'email', 'phone', 'secondary_phone',
            'zip_code', 'street', 'number', 'complement',
            'neighborhood', 'city', 'state',
            'notes', 'is_active', 'broker',
        ]
        widgets = {
            'client_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF ou CNPJ'}),
            'rg_ie': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'id': 'id_zip_code'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_street'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'complement': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_neighborhood'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_city'}),
            'state': forms.Select(attrs={'class': 'form-select', 'id': 'id_state'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['broker'].queryset = User.objects.filter(is_active=True)
