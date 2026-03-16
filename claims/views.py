from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from utils.mixins import BrokerageFilterMixin, BrokerageFormMixin, ModuleRequiredMixin

from .forms import ClaimForm, ClaimDocumentForm
from .models import Claim, ClaimDocument


class ClaimListView(ModuleRequiredMixin, BrokerageFilterMixin, ListView):
    model = Claim
    template_name = 'claims/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 20
    required_module = 'claims'

    def get_queryset(self):
        qs = super().get_queryset().select_related('policy', 'client', 'broker')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(claim_number__icontains=search) |
                Q(client__name__icontains=search) |
                Q(policy__policy_number__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class ClaimCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'claims/claim_form.html'
    success_url = reverse_lazy('claims:claim_list')
    required_module = 'claims'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Sinistro criado com sucesso.')
        return super().form_valid(form)


class ClaimUpdateView(ModuleRequiredMixin, BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'claims/claim_form.html'
    required_module = 'claims'

    def get_success_url(self):
        return reverse('claims:claim_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Sinistro atualizado com sucesso.')
        return super().form_valid(form)


class ClaimDetailView(ModuleRequiredMixin, BrokerageFilterMixin, DetailView):
    model = Claim
    template_name = 'claims/claim_detail.html'
    context_object_name = 'claim'
    required_module = 'claims'

    def get_queryset(self):
        return super().get_queryset().select_related('policy', 'client', 'broker')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['documents'] = self.object.documents.select_related('uploaded_by')
        ctx['timeline'] = self.object.timeline.select_related('performed_by')
        ctx['document_form'] = ClaimDocumentForm(user=self.request.user)
        from ai_agent.models import EntitySummary
        ctx['ai_summary'] = EntitySummary.objects.filter(
            brokerage=self.request.user.brokerage,
            entity_type='claim', entity_id=self.object.pk,
        ).first()
        return ctx


class ClaimDeleteView(ModuleRequiredMixin, BrokerageFilterMixin, DeleteView):
    model = Claim
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('claims:claim_list')
    required_module = 'claims'

    def form_valid(self, form):
        messages.success(self.request, 'Sinistro excluido com sucesso.')
        return super().form_valid(form)


# --- Claim Documents ---

class ClaimDocumentCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = ClaimDocument
    form_class = ClaimDocumentForm
    required_module = 'claims'

    def form_valid(self, form):
        form.instance.claim = get_object_or_404(
            Claim,
            pk=self.kwargs['pk'],
            brokerage=self.request.user.brokerage,
        )
        form.instance.brokerage = form.instance.claim.brokerage
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Documento adicionado com sucesso.')
        form.save()
        return redirect('claims:claim_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar documento.')
        return redirect('claims:claim_detail', pk=self.kwargs['pk'])


class ClaimDocumentDeleteView(ModuleRequiredMixin, BrokerageFilterMixin, DeleteView):
    model = ClaimDocument
    required_module = 'claims'

    def get_success_url(self):
        return reverse('claims:claim_detail', kwargs={'pk': self.object.claim_id})

    def form_valid(self, form):
        messages.success(self.request, 'Documento removido com sucesso.')
        return super().form_valid(form)
