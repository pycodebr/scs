from django import forms

from .models import InsuranceType, Coverage, CoverageItem


class InsuranceTypeForm(forms.ModelForm):
    class Meta:
        model = InsuranceType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CoverageForm(forms.ModelForm):
    class Meta:
        model = Coverage
        fields = ['insurance_type', 'name', 'description', 'is_active']
        widgets = {
            'insurance_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CoverageItemForm(forms.ModelForm):
    class Meta:
        model = CoverageItem
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
