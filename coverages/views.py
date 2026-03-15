from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView

from .forms import InsuranceTypeForm, CoverageForm, CoverageItemForm
from .models import InsuranceType, Coverage, CoverageItem


class InsuranceTypeListView(LoginRequiredMixin, ListView):
    model = InsuranceType
    template_name = 'coverages/insurance_type_list.html'
    context_object_name = 'types'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


class InsuranceTypeCreateView(LoginRequiredMixin, CreateView):
    model = InsuranceType
    form_class = InsuranceTypeForm
    template_name = 'coverages/insurance_type_form.html'
    success_url = reverse_lazy('coverages:type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ramo criado com sucesso.')
        return super().form_valid(form)


class InsuranceTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = InsuranceType
    form_class = InsuranceTypeForm
    template_name = 'coverages/insurance_type_form.html'
    success_url = reverse_lazy('coverages:type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ramo atualizado com sucesso.')
        return super().form_valid(form)


class CoverageListView(LoginRequiredMixin, ListView):
    model = Coverage
    template_name = 'coverages/coverage_list.html'
    context_object_name = 'coverages'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('insurance_type')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(insurance_type__name__icontains=search)
            )
        insurance_type = self.request.GET.get('type')
        if insurance_type:
            qs = qs.filter(insurance_type_id=insurance_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['insurance_types'] = InsuranceType.objects.filter(is_active=True)
        return ctx


class CoverageCreateView(LoginRequiredMixin, CreateView):
    model = Coverage
    form_class = CoverageForm
    template_name = 'coverages/coverage_form.html'
    success_url = reverse_lazy('coverages:coverage_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cobertura criada com sucesso.')
        return super().form_valid(form)


class CoverageUpdateView(LoginRequiredMixin, UpdateView):
    model = Coverage
    form_class = CoverageForm
    template_name = 'coverages/coverage_form.html'
    success_url = reverse_lazy('coverages:coverage_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = self.object.items.all()
        ctx['item_form'] = CoverageItemForm()
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Cobertura atualizada com sucesso.')
        return super().form_valid(form)


class CoverageItemCreateView(LoginRequiredMixin, CreateView):
    model = CoverageItem
    form_class = CoverageItemForm

    def form_valid(self, form):
        form.instance.coverage = get_object_or_404(Coverage, pk=self.kwargs['coverage_pk'])
        messages.success(self.request, 'Item adicionado com sucesso.')
        form.save()
        return redirect('coverages:coverage_update', pk=self.kwargs['coverage_pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar item.')
        return redirect('coverages:coverage_update', pk=self.kwargs['coverage_pk'])


class CoverageItemUpdateView(LoginRequiredMixin, UpdateView):
    model = CoverageItem
    form_class = CoverageItemForm
    template_name = 'coverages/coverage_item_form.html'

    def get_success_url(self):
        return reverse('coverages:coverage_update', kwargs={'pk': self.object.coverage_id})

    def form_valid(self, form):
        messages.success(self.request, 'Item atualizado com sucesso.')
        return super().form_valid(form)
