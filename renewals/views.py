from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from utils.mixins import BrokerFilterMixin

from .forms import RenewalForm, RenewalRenewForm
from .models import Renewal, RenewalStatus


class RenewalListView(LoginRequiredMixin, BrokerFilterMixin, ListView):
    model = Renewal
    template_name = 'renewals/renewal_list.html'
    context_object_name = 'renewals'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'policy', 'policy__client', 'policy__insurer',
            'policy__insurance_type', 'broker', 'new_insurer',
        )
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(policy__policy_number__icontains=search) |
                Q(policy__client__name__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        period = self.request.GET.get('period')
        if period:
            from datetime import date, timedelta
            today = date.today()
            if period == '30':
                qs = qs.filter(due_date__lte=today + timedelta(days=30))
            elif period == '60':
                qs = qs.filter(due_date__lte=today + timedelta(days=60))
            elif period == '90':
                qs = qs.filter(due_date__lte=today + timedelta(days=90))
        return qs


class RenewalCreateView(LoginRequiredMixin, CreateView):
    model = Renewal
    form_class = RenewalForm
    template_name = 'renewals/renewal_form.html'
    success_url = reverse_lazy('renewals:renewal_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Renovacao criada com sucesso.')
        return super().form_valid(form)


class RenewalUpdateView(LoginRequiredMixin, BrokerFilterMixin, UpdateView):
    model = Renewal
    form_class = RenewalForm
    template_name = 'renewals/renewal_form.html'

    def get_success_url(self):
        return reverse('renewals:renewal_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Renovacao atualizada com sucesso.')
        return super().form_valid(form)


class RenewalDetailView(LoginRequiredMixin, BrokerFilterMixin, DetailView):
    model = Renewal
    template_name = 'renewals/renewal_detail.html'
    context_object_name = 'renewal'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'policy', 'policy__client', 'policy__insurer',
            'policy__insurance_type', 'broker', 'renewed_policy', 'new_insurer',
        )


class RenewalRenewView(LoginRequiredMixin, View):
    """Renew a policy — create a new Policy from the original, mark Renewal as renewed."""

    def get(self, request, pk):
        renewal = get_object_or_404(Renewal.objects.select_related(
            'policy', 'policy__client', 'policy__insurer', 'policy__insurance_type',
        ), pk=pk)
        policy = renewal.policy
        from datetime import timedelta
        form = RenewalRenewForm(initial={
            'start_date': policy.end_date,
            'end_date': policy.end_date + timedelta(days=365),
            'premium_amount': renewal.new_premium or policy.premium_amount,
        })
        # Populate insurer choices
        from insurers.models import Insurer
        insurers = Insurer.objects.filter(is_active=True)
        form.fields['insurer'].widget = forms_select_widget(insurers, policy.insurer_id)
        return render(request, 'renewals/renewal_renew.html', {
            'renewal': renewal,
            'form': form,
            'policy': policy,
        })

    def post(self, request, pk):
        renewal = get_object_or_404(Renewal.objects.select_related(
            'policy', 'policy__client', 'policy__insurer', 'policy__insurance_type',
        ), pk=pk)
        form = RenewalRenewForm(request.POST)
        from insurers.models import Insurer
        insurers = Insurer.objects.filter(is_active=True)
        form.fields['insurer'].widget = forms_select_widget(insurers, renewal.policy.insurer_id)

        if form.is_valid():
            from policies.models import Policy, PolicyStatus
            policy = renewal.policy
            insurer_id = form.cleaned_data.get('insurer') or policy.insurer_id
            new_policy = Policy.objects.create(
                policy_number=form.cleaned_data['policy_number'],
                proposal=None,
                client=policy.client,
                insurer_id=insurer_id,
                insurance_type=policy.insurance_type,
                broker=renewal.broker,
                status=PolicyStatus.ACTIVE,
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                premium_amount=form.cleaned_data['premium_amount'],
                insured_amount=policy.insured_amount,
                commission_rate=policy.commission_rate,
                commission_amount=(
                    form.cleaned_data['premium_amount'] * policy.commission_rate / 100
                ),
                installments=policy.installments,
                payment_method=policy.payment_method,
            )
            renewal.renewed_policy = new_policy
            renewal.status = RenewalStatus.RENEWED
            renewal.save(update_fields=['renewed_policy', 'status', 'updated_at'])
            messages.success(
                request,
                f'Apolice {new_policy.policy_number} criada a partir da renovacao de {policy.policy_number}.',
            )
            return redirect('policies:policy_detail', pk=new_policy.pk)
        return render(request, 'renewals/renewal_renew.html', {
            'renewal': renewal,
            'form': form,
            'policy': renewal.policy,
        })


def forms_select_widget(insurers, selected_id=None):
    """Build a Select widget with insurer choices."""
    from django import forms
    choices = [('', '---------')]
    for ins in insurers:
        choices.append((ins.pk, ins.name))
    widget = forms.Select(attrs={'class': 'form-select'}, choices=choices)
    return widget
