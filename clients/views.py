import csv

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from utils.mixins import BrokerageFilterMixin, BrokerageFormMixin

from .forms import ClientForm
from .models import Client


class ClientListView(BrokerageFilterMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(cpf_cnpj__icontains=search) |
                Q(email__icontains=search)
            )
        client_type = self.request.GET.get('type')
        if client_type:
            qs = qs.filter(client_type=client_type)
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        broker = self.request.GET.get('broker')
        if broker:
            qs = qs.filter(broker_id=broker)
        return qs


class ClientCreateView(BrokerageFormMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Cliente criado com sucesso.')
        return super().form_valid(form)


class ClientUpdateView(BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado com sucesso.')
        return super().form_valid(form)


class ClientDetailView(BrokerageFilterMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from ai_agent.models import EntitySummary
        ctx['ai_summary'] = EntitySummary.objects.filter(
            brokerage=self.request.user.brokerage,
            entity_type='client', entity_id=self.object.pk,
        ).first()
        return ctx


class ClientDeleteView(BrokerageFilterMixin, DeleteView):
    model = Client
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente excluido com sucesso.')
        return super().form_valid(form)


class ClientExportView(BrokerageFormMixin, View):
    def get(self, request):
        qs = Client.objects.filter(brokerage=request.user.brokerage)
        if request.user.role == 'broker':
            qs = qs.filter(broker=request.user)
        qs = qs.select_related('broker').order_by('name')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clientes.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([
            'Nome', 'Tipo', 'CPF/CNPJ', 'Email', 'Telefone',
            'Cidade', 'UF', 'Corretor', 'Status',
        ])
        for client in qs:
            writer.writerow([
                client.name,
                client.get_client_type_display(),
                client.cpf_cnpj,
                client.email,
                client.phone,
                client.city,
                client.state,
                client.broker.get_full_name(),
                'Ativo' if client.is_active else 'Inativo',
            ])
        return response
