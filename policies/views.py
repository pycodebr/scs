import csv

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from utils.mixins import BrokerageFilterMixin, BrokerageFormMixin, BrokerageRequiredMixin

from .forms import ProposalForm, PolicyForm, PolicyCoverageForm, PolicyDocumentForm
from .models import Proposal, Policy, PolicyCoverage, PolicyDocument


# --- Proposals ---

class ProposalListView(BrokerageFilterMixin, ListView):
    model = Proposal
    template_name = 'policies/proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('client', 'insurer', 'insurance_type', 'broker')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(proposal_number__icontains=search) |
                Q(client__name__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class ProposalCreateView(BrokerageFormMixin, CreateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'policies/proposal_form.html'
    success_url = reverse_lazy('policies:proposal_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Proposta criada com sucesso.')
        return super().form_valid(form)


class ProposalUpdateView(BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'policies/proposal_form.html'
    success_url = reverse_lazy('policies:proposal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Proposta atualizada com sucesso.')
        return super().form_valid(form)


class ProposalDetailView(BrokerageFilterMixin, DetailView):
    model = Proposal
    template_name = 'policies/proposal_detail.html'
    context_object_name = 'proposal'

    def get_queryset(self):
        return super().get_queryset().select_related('client', 'insurer', 'insurance_type', 'broker')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from ai_agent.models import EntitySummary
        ctx['ai_summary'] = EntitySummary.objects.filter(
            brokerage=self.request.user.brokerage,
            entity_type='proposal', entity_id=self.object.pk,
        ).first()
        return ctx


class ProposalDeleteView(BrokerageFilterMixin, DeleteView):
    model = Proposal
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('policies:proposal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Proposta excluida com sucesso.')
        return super().form_valid(form)


class ProposalConvertView(BrokerageFormMixin, BrokerageRequiredMixin, View):
    """Convert an approved proposal into a new policy."""

    def get(self, request, pk):
        proposal = get_object_or_404(Proposal.objects.select_related(
            'client', 'insurer', 'insurance_type', 'broker',
        ), pk=pk, brokerage=request.user.brokerage)
        if proposal.status != 'approved':
            messages.error(request, 'Apenas propostas aprovadas podem ser convertidas em apolice.')
            return redirect('policies:proposal_detail', pk=pk)
        form = PolicyForm(user=request.user, initial={
            'proposal': proposal,
            'client': proposal.client,
            'insurer': proposal.insurer,
            'insurance_type': proposal.insurance_type,
            'broker': proposal.broker,
            'premium_amount': proposal.premium_amount,
        })
        if request.user.role == 'broker':
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return self.render(request, form, proposal)

    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk, brokerage=request.user.brokerage)
        form = PolicyForm(request.POST, user=request.user)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.brokerage = request.user.brokerage
            policy.save()
            messages.success(request, f'Apolice {policy.policy_number} criada a partir da proposta {proposal.proposal_number}.')
            return redirect('policies:policy_detail', pk=policy.pk)
        return self.render(request, form, proposal)

    def render(self, request, form, proposal):
        from django.shortcuts import render
        return render(request, 'policies/policy_form.html', {
            'form': form,
            'proposal': proposal,
            'converting': True,
        })


# --- Policies ---

class PolicyListView(BrokerageFilterMixin, ListView):
    model = Policy
    template_name = 'policies/policy_list.html'
    context_object_name = 'policies'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('client', 'insurer', 'insurance_type', 'broker')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(policy_number__icontains=search) |
                Q(client__name__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class PolicyCreateView(BrokerageFormMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'policies/policy_form.html'
    success_url = reverse_lazy('policies:policy_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Apolice criada com sucesso.')
        return super().form_valid(form)


class PolicyUpdateView(BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'policies/policy_form.html'

    def get_success_url(self):
        return reverse('policies:policy_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['coverages'] = self.object.coverages.select_related('coverage')
        ctx['coverage_form'] = PolicyCoverageForm(user=self.request.user)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Apolice atualizada com sucesso.')
        return super().form_valid(form)


class PolicyDetailView(BrokerageFilterMixin, DetailView):
    model = Policy
    template_name = 'policies/policy_detail.html'
    context_object_name = 'policy'

    def get_queryset(self):
        return super().get_queryset().select_related('client', 'insurer', 'insurance_type', 'broker', 'proposal')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['coverages'] = self.object.coverages.select_related('coverage')
        ctx['documents'] = self.object.documents.select_related('uploaded_by')
        ctx['document_form'] = PolicyDocumentForm(user=self.request.user)
        ctx['coverage_form'] = PolicyCoverageForm(user=self.request.user)
        from ai_agent.models import EntitySummary
        ctx['ai_summary'] = EntitySummary.objects.filter(
            brokerage=self.request.user.brokerage,
            entity_type='policy', entity_id=self.object.pk,
        ).first()
        return ctx


class PolicyDeleteView(BrokerageFilterMixin, DeleteView):
    model = Policy
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('policies:policy_list')

    def form_valid(self, form):
        messages.success(self.request, 'Apolice excluida com sucesso.')
        return super().form_valid(form)


class PolicyExportView(BrokerageRequiredMixin, View):
    def get(self, request):
        qs = Policy.objects.select_related('client', 'insurer', 'broker').filter(
            brokerage=request.user.brokerage,
        )
        if request.user.role == 'broker':
            qs = qs.filter(broker=request.user)
        qs = qs.order_by('-start_date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="apolices.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([
            'Numero', 'Cliente', 'Seguradora', 'Tipo',
            'Status', 'Inicio', 'Fim', 'Premio', 'Comissao',
        ])
        for p in qs:
            writer.writerow([
                p.policy_number,
                p.client.name,
                p.insurer.name,
                p.insurance_type.name if p.insurance_type else '',
                p.get_status_display(),
                p.start_date.strftime('%d/%m/%Y'),
                p.end_date.strftime('%d/%m/%Y'),
                p.premium_amount,
                p.commission_amount,
            ])
        return response


# --- Policy Coverages ---

class PolicyCoverageCreateView(BrokerageFormMixin, CreateView):
    model = PolicyCoverage
    form_class = PolicyCoverageForm

    def form_valid(self, form):
        form.instance.policy = get_object_or_404(
            Policy,
            pk=self.kwargs['pk'],
            brokerage=self.request.user.brokerage,
        )
        form.instance.brokerage = form.instance.policy.brokerage
        messages.success(self.request, 'Cobertura adicionada com sucesso.')
        form.save()
        return redirect('policies:policy_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar cobertura.')
        return redirect('policies:policy_detail', pk=self.kwargs['pk'])


class PolicyCoverageDeleteView(BrokerageFilterMixin, DeleteView):
    model = PolicyCoverage

    def get_success_url(self):
        return reverse('policies:policy_detail', kwargs={'pk': self.object.policy_id})

    def form_valid(self, form):
        messages.success(self.request, 'Cobertura removida com sucesso.')
        return super().form_valid(form)


# --- Policy Documents ---

class PolicyDocumentCreateView(BrokerageFormMixin, CreateView):
    model = PolicyDocument
    form_class = PolicyDocumentForm

    def form_valid(self, form):
        form.instance.policy = get_object_or_404(
            Policy,
            pk=self.kwargs['pk'],
            brokerage=self.request.user.brokerage,
        )
        form.instance.brokerage = form.instance.policy.brokerage
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Documento adicionado com sucesso.')
        form.save()
        return redirect('policies:policy_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar documento.')
        return redirect('policies:policy_detail', pk=self.kwargs['pk'])


class PolicyDocumentDeleteView(BrokerageFilterMixin, DeleteView):
    model = PolicyDocument

    def get_success_url(self):
        return reverse('policies:policy_detail', kwargs={'pk': self.object.policy_id})

    def form_valid(self, form):
        messages.success(self.request, 'Documento removido com sucesso.')
        return super().form_valid(form)
