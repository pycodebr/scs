from django import forms

from utils.forms import BrokerageScopedFormMixin

from .models import Endorsement, EndorsementDocument


class EndorsementForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Endorsement
        fields = [
            'endorsement_number', 'policy', 'endorsement_type',
            'status', 'request_date', 'effective_date',
            'description', 'premium_difference', 'requested_by', 'notes',
        ]
        widgets = {
            'endorsement_number': forms.TextInput(attrs={'class': 'form-control'}),
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'endorsement_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'request_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'premium_difference': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'requested_by': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EndorsementDocumentForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = EndorsementDocument
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
