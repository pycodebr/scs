import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView

from utils.mixins import BrokerFilterMixin, ManagerRequiredMixin

from .forms import DealForm, DealActivityForm, PipelineForm, PipelineStageForm
from .models import Pipeline, PipelineStage, Deal, DealActivity


# --- Kanban ---

class DealKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/deal_kanban.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pipeline_id = self.request.GET.get('pipeline')
        pipelines = Pipeline.objects.filter(is_active=True)

        if pipeline_id:
            pipeline = get_object_or_404(Pipeline, pk=pipeline_id, is_active=True)
        else:
            pipeline = pipelines.filter(is_default=True).first() or pipelines.first()

        if not pipeline:
            ctx['pipeline'] = None
            ctx['pipelines'] = pipelines
            ctx['stages'] = []
            return ctx

        stages = pipeline.stages.order_by('order')
        deals_qs = Deal.objects.filter(pipeline=pipeline).select_related(
            'client', 'broker', 'stage',
        )
        if self.request.user.role == 'broker':
            deals_qs = deals_qs.filter(broker=self.request.user)

        # Filters
        priority = self.request.GET.get('priority')
        if priority:
            deals_qs = deals_qs.filter(priority=priority)
        broker_id = self.request.GET.get('broker')
        if broker_id and self.request.user.role != 'broker':
            deals_qs = deals_qs.filter(broker_id=broker_id)

        # Pre-compute deals per stage
        stages_data = []
        for stage in stages:
            stage_deals = deals_qs.filter(stage=stage).order_by('-updated_at')
            stage_total = stage_deals.aggregate(total=Sum('expected_value'))['total'] or 0
            stages_data.append({
                'stage': stage,
                'deals': stage_deals,
                'count': stage_deals.count(),
                'total': stage_total,
            })

        ctx['pipeline'] = pipeline
        ctx['pipelines'] = pipelines
        ctx['stages_data'] = stages_data

        # Brokers list for filter
        from django.contrib.auth import get_user_model
        User = get_user_model()
        ctx['brokers'] = User.objects.filter(is_active=True)
        return ctx


# --- Deal Grid (Table) ---

class DealListView(LoginRequiredMixin, BrokerFilterMixin, ListView):
    model = Deal
    template_name = 'crm/deal_list.html'
    context_object_name = 'deals'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'client', 'broker', 'pipeline', 'stage', 'insurance_type',
        )
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(client__name__icontains=search)
            )
        status = self.request.GET.get('priority')
        if status:
            qs = qs.filter(priority=status)
        pipeline = self.request.GET.get('pipeline')
        if pipeline:
            qs = qs.filter(pipeline_id=pipeline)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pipelines'] = Pipeline.objects.filter(is_active=True)
        return ctx


# --- Deal CRUD ---

class DealCreateView(LoginRequiredMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'
    success_url = reverse_lazy('crm:deal_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        # Default pipeline and first stage
        default_pipeline = Pipeline.objects.filter(is_default=True, is_active=True).first()
        if default_pipeline and not form.initial.get('pipeline'):
            form.fields['pipeline'].initial = default_pipeline.pk
            first_stage = default_pipeline.stages.order_by('order').first()
            if first_stage:
                form.fields['stage'].initial = first_stage.pk
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Negociacao criada com sucesso.')
        return super().form_valid(form)


class DealUpdateView(LoginRequiredMixin, BrokerFilterMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'

    def get_success_url(self):
        return reverse('crm:deal_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Negociacao atualizada com sucesso.')
        return super().form_valid(form)


class DealDetailView(LoginRequiredMixin, BrokerFilterMixin, DetailView):
    model = Deal
    template_name = 'crm/deal_detail.html'
    context_object_name = 'deal'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'client', 'broker', 'pipeline', 'stage',
            'insurance_type', 'insurer', 'proposal', 'policy',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['activities'] = self.object.activities.select_related('performed_by')
        ctx['activity_form'] = DealActivityForm()
        return ctx


class DealDeleteView(LoginRequiredMixin, BrokerFilterMixin, DeleteView):
    model = Deal
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('crm:deal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Negociacao excluida com sucesso.')
        return super().form_valid(form)


# --- Move Stage (AJAX) ---

class DealMoveStageView(LoginRequiredMixin, View):
    """AJAX endpoint to move a deal to a different stage."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            stage_id = data.get('stage_id')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Dados invalidos.'}, status=400)

        deal = get_object_or_404(Deal, pk=pk)

        # Broker can only move own deals
        if request.user.role == 'broker' and deal.broker != request.user:
            return JsonResponse({'error': 'Sem permissao.'}, status=403)

        stage = get_object_or_404(PipelineStage, pk=stage_id, pipeline=deal.pipeline)
        old_stage = deal.stage

        deal.stage = stage
        deal.save(update_fields=['stage', 'updated_at'])

        # Create activity log for stage change
        DealActivity.objects.create(
            deal=deal,
            activity_type='note',
            title=f'Movido de "{old_stage.name}" para "{stage.name}"',
            performed_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'deal_id': deal.pk,
            'new_stage_id': stage.pk,
            'stage_name': stage.name,
        })


# --- Deal Activities ---

class DealActivityCreateView(LoginRequiredMixin, CreateView):
    model = DealActivity
    form_class = DealActivityForm

    def form_valid(self, form):
        form.instance.deal = get_object_or_404(Deal, pk=self.kwargs['pk'])
        form.instance.performed_by = self.request.user
        messages.success(self.request, 'Atividade adicionada com sucesso.')
        form.save()
        return redirect('crm:deal_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar atividade.')
        return redirect('crm:deal_detail', pk=self.kwargs['pk'])


# --- Pipeline Management ---

class PipelineManageView(ManagerRequiredMixin, TemplateView):
    template_name = 'crm/pipeline_manage.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pipelines'] = Pipeline.objects.prefetch_related('stages').all()
        ctx['pipeline_form'] = PipelineForm()
        ctx['stage_form'] = PipelineStageForm()
        return ctx


class PipelineCreateView(ManagerRequiredMixin, CreateView):
    model = Pipeline
    form_class = PipelineForm
    success_url = reverse_lazy('crm:pipeline_manage')

    def form_valid(self, form):
        messages.success(self.request, 'Pipeline criado com sucesso.')
        pipeline = form.save()

        # Create default stages
        default_stages = [
            ('Prospeccao', 0, '#6c757d', False, False),
            ('Primeiro Contato', 1, '#0d6efd', False, False),
            ('Cotacao', 2, '#ffc107', False, False),
            ('Proposta Enviada', 3, '#fd7e14', False, False),
            ('Negociacao', 4, '#6610f2', False, False),
            ('Fechamento', 5, '#198754', True, False),
            ('Perdido', 6, '#dc3545', False, True),
        ]
        for name, order, color, is_won, is_lost in default_stages:
            PipelineStage.objects.create(
                pipeline=pipeline,
                name=name,
                order=order,
                color=color,
                is_won=is_won,
                is_lost=is_lost,
            )

        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao criar pipeline.')
        return redirect(self.success_url)


class PipelineStageCreateView(ManagerRequiredMixin, View):
    def post(self, request, pipeline_pk):
        pipeline = get_object_or_404(Pipeline, pk=pipeline_pk)
        form = PipelineStageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.pipeline = pipeline
            stage.save()
            messages.success(request, f'Etapa "{stage.name}" adicionada ao pipeline.')
        else:
            messages.error(request, 'Erro ao criar etapa.')
        return redirect('crm:pipeline_manage')


class PipelineStageDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        stage = get_object_or_404(PipelineStage, pk=pk)
        if stage.deals.exists():
            messages.error(request, 'Nao e possivel excluir uma etapa com negociacoes vinculadas.')
        else:
            stage.delete()
            messages.success(request, 'Etapa excluida com sucesso.')
        return redirect('crm:pipeline_manage')
