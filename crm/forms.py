from django import forms

from utils.forms import BrokerageScopedFormMixin

from .models import Deal, DealActivity, Pipeline, PipelineStage


class DealForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'title', 'client', 'broker', 'pipeline', 'stage',
            'insurance_type', 'insurer', 'expected_value',
            'expected_close_date', 'priority', 'source',
            'proposal', 'policy', 'lost_reason', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'pipeline': forms.Select(attrs={'class': 'form-select', 'id': 'id_pipeline'}),
            'stage': forms.Select(attrs={'class': 'form-select', 'id': 'id_stage'}),
            'insurance_type': forms.Select(attrs={'class': 'form-select'}),
            'insurer': forms.Select(attrs={'class': 'form-select'}),
            'expected_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'proposal': forms.Select(attrs={'class': 'form-select'}),
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'lost_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pipeline'].queryset = Pipeline.objects.filter(is_active=True)
        self.fields['stage'].queryset = PipelineStage.objects.select_related('pipeline')
        self.fields['proposal'].required = False
        self.fields['policy'].required = False
        self.fields['insurer'].required = False
        self.fields['insurance_type'].required = False


class DealActivityForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = DealActivity
        fields = ['activity_type', 'title', 'description', 'due_date', 'is_completed']
        widgets = {
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PipelineForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Pipeline
        fields = ['name', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PipelineStageForm(BrokerageScopedFormMixin, forms.ModelForm):
    class Meta:
        model = PipelineStage
        fields = ['name', 'order', 'color', 'is_won', 'is_lost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_won': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_lost': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
