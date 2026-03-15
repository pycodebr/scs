from django import forms

from .models import Claim, ClaimDocument


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = [
            'claim_number', 'policy', 'client', 'status',
            'occurrence_date', 'notification_date', 'description',
            'location', 'claimed_amount', 'approved_amount',
            'resolution_date', 'resolution_notes', 'broker',
        ]
        widgets = {
            'claim_number': forms.TextInput(attrs={'class': 'form-control'}),
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'occurrence_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'notification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'claimed_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'approved_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'resolution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from policies.models import Policy
        User = get_user_model()
        self.fields['broker'].queryset = User.objects.filter(is_active=True)
        self.fields['policy'].queryset = Policy.objects.filter(status='active')


class ClaimDocumentForm(forms.ModelForm):
    class Meta:
        model = ClaimDocument
        fields = ['title', 'file', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
        }
