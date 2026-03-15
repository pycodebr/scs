from django import forms

from .models import Insurer, InsurerBranch


class InsurerForm(forms.ModelForm):
    class Meta:
        model = Insurer
        fields = [
            'name', 'cnpj', 'susep_code',
            'email', 'phone', 'website',
            'contact_name', 'contact_email', 'contact_phone',
            'zip_code', 'street', 'number', 'complement',
            'neighborhood', 'city', 'state',
            'logo', 'is_active', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'susep_code': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 0000-0000'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'id': 'id_zip_code'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_street'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'complement': forms.TextInput(attrs={'class': 'form-control'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_neighborhood'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_city'}),
            'state': forms.Select(attrs={'class': 'form-select', 'id': 'id_state'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InsurerBranchForm(forms.ModelForm):
    class Meta:
        model = InsurerBranch
        fields = ['name', 'susep_branch_code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'susep_branch_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
