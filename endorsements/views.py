from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from utils.mixins import BrokerageFilterMixin, BrokerageFormMixin, ModuleRequiredMixin

from .forms import EndorsementForm, EndorsementDocumentForm
from .models import Endorsement, EndorsementDocument


class EndorsementListView(ModuleRequiredMixin, BrokerageFilterMixin, ListView):
    model = Endorsement
    template_name = 'endorsements/endorsement_list.html'
    context_object_name = 'endorsements'
    paginate_by = 20
    broker_field = 'requested_by'
    required_module = 'endorsements'

    def get_queryset(self):
        qs = super().get_queryset().select_related('policy', 'policy__client', 'requested_by')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(endorsement_number__icontains=search) |
                Q(policy__policy_number__icontains=search) |
                Q(policy__client__name__icontains=search)
            )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        endorsement_type = self.request.GET.get('type')
        if endorsement_type:
            qs = qs.filter(endorsement_type=endorsement_type)
        return qs


class EndorsementCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = Endorsement
    form_class = EndorsementForm
    template_name = 'endorsements/endorsement_form.html'
    success_url = reverse_lazy('endorsements:endorsement_list')
    required_module = 'endorsements'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['requested_by'].initial = self.request.user
            form.fields['requested_by'].widget = form.fields['requested_by'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.requested_by = self.request.user
        messages.success(self.request, 'Endosso criado com sucesso.')
        return super().form_valid(form)


class EndorsementUpdateView(ModuleRequiredMixin, BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Endorsement
    form_class = EndorsementForm
    template_name = 'endorsements/endorsement_form.html'
    broker_field = 'requested_by'
    required_module = 'endorsements'

    def get_success_url(self):
        return reverse('endorsements:endorsement_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Endosso atualizado com sucesso.')
        return super().form_valid(form)


class EndorsementDetailView(ModuleRequiredMixin, BrokerageFilterMixin, DetailView):
    model = Endorsement
    template_name = 'endorsements/endorsement_detail.html'
    context_object_name = 'endorsement'
    broker_field = 'requested_by'
    required_module = 'endorsements'

    def get_queryset(self):
        return super().get_queryset().select_related('policy', 'policy__client', 'requested_by')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['documents'] = self.object.documents.select_related('uploaded_by')
        ctx['document_form'] = EndorsementDocumentForm(user=self.request.user)
        return ctx


class EndorsementDeleteView(ModuleRequiredMixin, BrokerageFilterMixin, DeleteView):
    model = Endorsement
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('endorsements:endorsement_list')
    broker_field = 'requested_by'
    required_module = 'endorsements'

    def form_valid(self, form):
        messages.success(self.request, 'Endosso excluido com sucesso.')
        return super().form_valid(form)


# --- Endorsement Documents ---

class EndorsementDocumentCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = EndorsementDocument
    form_class = EndorsementDocumentForm
    required_module = 'endorsements'

    def form_valid(self, form):
        form.instance.endorsement = get_object_or_404(
            Endorsement,
            pk=self.kwargs['pk'],
            brokerage=self.request.user.brokerage,
        )
        form.instance.brokerage = form.instance.endorsement.brokerage
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Documento adicionado com sucesso.')
        form.save()
        return redirect('endorsements:endorsement_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar documento.')
        return redirect('endorsements:endorsement_detail', pk=self.kwargs['pk'])


class EndorsementDocumentDeleteView(ModuleRequiredMixin, BrokerageFilterMixin, DeleteView):
    model = EndorsementDocument
    required_module = 'endorsements'

    def get_success_url(self):
        return reverse('endorsements:endorsement_detail', kwargs={'pk': self.object.endorsement_id})

    def form_valid(self, form):
        messages.success(self.request, 'Documento removido com sucesso.')
        return super().form_valid(form)
