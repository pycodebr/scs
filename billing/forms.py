from django import forms


class SignupPlanSelectionForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=None,
        label='Plano',
        widget=forms.RadioSelect,
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        plan_queryset = kwargs.pop('plan_queryset')
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = plan_queryset
