from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from .forms import InsurerForm, InsurerBranchForm
from .models import Insurer, InsurerBranch


class InsurerListView(LoginRequiredMixin, ListView):
    model = Insurer
    template_name = 'insurers/insurer_list.html'
    context_object_name = 'insurers'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(cnpj__icontains=search)
            )
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class InsurerCreateView(LoginRequiredMixin, CreateView):
    model = Insurer
    form_class = InsurerForm
    template_name = 'insurers/insurer_form.html'
    success_url = reverse_lazy('insurers:insurer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Seguradora criada com sucesso.')
        return super().form_valid(form)


class InsurerUpdateView(LoginRequiredMixin, UpdateView):
    model = Insurer
    form_class = InsurerForm
    template_name = 'insurers/insurer_form.html'
    success_url = reverse_lazy('insurers:insurer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Seguradora atualizada com sucesso.')
        return super().form_valid(form)


class InsurerDetailView(LoginRequiredMixin, DetailView):
    model = Insurer
    template_name = 'insurers/insurer_detail.html'
    context_object_name = 'insurer'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['branches'] = self.object.branches.all()
        ctx['branch_form'] = InsurerBranchForm()
        return ctx


class InsurerDeleteView(LoginRequiredMixin, DeleteView):
    model = Insurer
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('insurers:insurer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Seguradora excluida com sucesso.')
        return super().form_valid(form)


class InsurerBranchCreateView(LoginRequiredMixin, CreateView):
    model = InsurerBranch
    form_class = InsurerBranchForm

    def form_valid(self, form):
        form.instance.insurer = get_object_or_404(Insurer, pk=self.kwargs['pk'])
        messages.success(self.request, 'Ramo adicionado com sucesso.')
        form.save()
        return redirect('insurers:insurer_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar ramo.')
        return redirect('insurers:insurer_detail', pk=self.kwargs['pk'])


class InsurerBranchDeleteView(LoginRequiredMixin, DeleteView):
    model = InsurerBranch

    def get_success_url(self):
        return reverse('insurers:insurer_detail', kwargs={'pk': self.object.insurer_id})

    def form_valid(self, form):
        messages.success(self.request, 'Ramo removido com sucesso.')
        return super().form_valid(form)
