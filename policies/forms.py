from django import forms

from utils.forms import BrokerageScopedFormMixin

from .models import Proposal, Policy, PolicyCoverage, PolicyDocument


class ProposalForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'proposal_number', 'client', 'insurer', 'insurance_type',
            'broker', 'status', 'submission_date', 'response_date',
            'premium_amount', 'notes', 'rejection_reason',
        ]
        widgets = {
            'proposal_number': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'insurer': forms.Select(attrs={'class': 'form-select'}),
            'insurance_type': forms.Select(attrs={'class': 'form-select'}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'submission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'response_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'premium_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PolicyForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Policy
        fields = [
            'policy_number', 'proposal', 'client', 'insurer', 'insurance_type',
            'broker', 'status', 'start_date', 'end_date',
            'premium_amount', 'insured_amount', 'commission_rate',
            'commission_amount', 'installments', 'payment_method', 'notes',
        ]
        widgets = {
            'policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'proposal': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'insurer': forms.Select(attrs={'class': 'form-select'}),
            'insurance_type': forms.Select(attrs={'class': 'form-select'}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'premium_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'insured_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'installments': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proposal'].required = False


class PolicyCoverageForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = PolicyCoverage
        fields = ['coverage', 'insured_amount', 'deductible', 'premium_amount', 'notes']
        widgets = {
            'coverage': forms.Select(attrs={'class': 'form-select'}),
            'insured_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'premium_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PolicyDocumentForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = PolicyDocument
        fields = ['title', 'file', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
        }
