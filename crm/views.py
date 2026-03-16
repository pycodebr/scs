import json

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView

from utils.mixins import BrokerageFilterMixin, BrokerageFormMixin, ManagerRequiredMixin, ModuleRequiredMixin

from .forms import DealForm, DealActivityForm, PipelineForm, PipelineStageForm
from .models import Pipeline, PipelineStage, Deal, DealActivity


# --- Kanban ---

class DealKanbanView(ModuleRequiredMixin, TemplateView):
    template_name = 'crm/deal_kanban.html'
    required_module = 'crm'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pipeline_id = self.request.GET.get('pipeline')
        pipelines = Pipeline.objects.filter(
            brokerage=self.request.user.brokerage,
            is_active=True,
        )

        if pipeline_id:
            pipeline = get_object_or_404(
                Pipeline,
                pk=pipeline_id,
                is_active=True,
                brokerage=self.request.user.brokerage,
            )
        else:
            pipeline = pipelines.filter(is_default=True).first() or pipelines.first()

        if not pipeline:
            ctx['pipeline'] = None
            ctx['pipelines'] = pipelines
            ctx['stages'] = []
            return ctx

        stages = pipeline.stages.order_by('order')
        deals_qs = Deal.objects.filter(
            brokerage=self.request.user.brokerage,
            pipeline=pipeline,
        ).select_related(
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
        ctx['brokers'] = User.objects.filter(
            brokerage=self.request.user.brokerage,
            is_active=True,
            is_platform_admin=False,
        )
        return ctx


# --- Deal Grid (Table) ---

class DealListView(ModuleRequiredMixin, BrokerageFilterMixin, ListView):
    model = Deal
    template_name = 'crm/deal_list.html'
    context_object_name = 'deals'
    paginate_by = 20
    required_module = 'crm'

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
        ctx['pipelines'] = Pipeline.objects.filter(
            brokerage=self.request.user.brokerage,
            is_active=True,
        )
        return ctx


# --- Deal CRUD ---

class DealCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'
    success_url = reverse_lazy('crm:deal_list')
    required_module = 'crm'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'broker':
            form.fields['broker'].initial = self.request.user
            form.fields['broker'].widget = form.fields['broker'].hidden_widget()
        # Default pipeline and first stage
        default_pipeline = Pipeline.objects.filter(
            brokerage=self.request.user.brokerage,
            is_default=True,
            is_active=True,
        ).first()
        if default_pipeline and not form.initial.get('pipeline'):
            form.fields['pipeline'].initial = default_pipeline.pk
            first_stage = default_pipeline.stages.order_by('order').first()
            if first_stage:
                form.fields['stage'].initial = first_stage.pk
        return form

    def form_valid(self, form):
        if self.request.user.role == 'broker':
            form.instance.broker = self.request.user
        messages.success(self.request, 'Negociação criada com sucesso.')
        return super().form_valid(form)


class DealUpdateView(ModuleRequiredMixin, BrokerageFormMixin, BrokerageFilterMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'
    required_module = 'crm'

    def get_success_url(self):
        return reverse('crm:deal_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Negociação atualizada com sucesso.')
        return super().form_valid(form)


class DealDetailView(ModuleRequiredMixin, BrokerageFilterMixin, DetailView):
    model = Deal
    template_name = 'crm/deal_detail.html'
    context_object_name = 'deal'
    required_module = 'crm'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'client', 'broker', 'pipeline', 'stage',
            'insurance_type', 'insurer', 'proposal', 'policy',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['activities'] = self.object.activities.select_related('performed_by')
        ctx['activity_form'] = DealActivityForm(user=self.request.user)
        from ai_agent.models import EntitySummary
        ctx['ai_summary'] = EntitySummary.objects.filter(
            brokerage=self.request.user.brokerage,
            entity_type='deal', entity_id=self.object.pk,
        ).first()
        return ctx


class DealDeleteView(ModuleRequiredMixin, BrokerageFilterMixin, DeleteView):
    model = Deal
    template_name = 'partials/_confirm_delete.html'
    success_url = reverse_lazy('crm:deal_list')
    required_module = 'crm'

    def form_valid(self, form):
        messages.success(self.request, 'Negociação excluída com sucesso.')
        return super().form_valid(form)


# --- Move Stage (AJAX) ---

class DealMoveStageView(ModuleRequiredMixin, View):
    """AJAX endpoint to move a deal to a different stage."""
    required_module = 'crm'

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            stage_id = data.get('stage_id')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Dados inválidos.'}, status=400)

        deal = get_object_or_404(Deal, pk=pk, brokerage=request.user.brokerage)

        # Broker can only move own deals
        if request.user.role == 'broker' and deal.broker != request.user:
            return JsonResponse({'error': 'Sem permissão.'}, status=403)

        stage = get_object_or_404(
            PipelineStage,
            pk=stage_id,
            pipeline=deal.pipeline,
            brokerage=request.user.brokerage,
        )
        old_stage = deal.stage

        deal.stage = stage
        deal.save(update_fields=['stage', 'updated_at'])

        # Create activity log for stage change
        DealActivity.objects.create(
            brokerage=deal.brokerage,
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

class DealActivityCreateView(ModuleRequiredMixin, BrokerageFormMixin, CreateView):
    model = DealActivity
    form_class = DealActivityForm
    required_module = 'crm'

    def form_valid(self, form):
        form.instance.deal = get_object_or_404(
            Deal,
            pk=self.kwargs['pk'],
            brokerage=self.request.user.brokerage,
        )
        form.instance.brokerage = form.instance.deal.brokerage
        form.instance.performed_by = self.request.user
        messages.success(self.request, 'Atividade adicionada com sucesso.')
        form.save()
        return redirect('crm:deal_detail', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao adicionar atividade.')
        return redirect('crm:deal_detail', pk=self.kwargs['pk'])


# --- Pipeline Management ---

class PipelineManageView(ModuleRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'crm/pipeline_manage.html'
    required_module = 'crm'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pipelines'] = Pipeline.objects.filter(
            brokerage=self.request.user.brokerage,
        ).prefetch_related('stages')
        ctx['pipeline_form'] = PipelineForm(user=self.request.user)
        ctx['stage_form'] = PipelineStageForm(user=self.request.user)
        return ctx


class PipelineCreateView(ModuleRequiredMixin, BrokerageFormMixin, ManagerRequiredMixin, CreateView):
    model = Pipeline
    form_class = PipelineForm
    success_url = reverse_lazy('crm:pipeline_manage')
    required_module = 'crm'

    def form_valid(self, form):
        messages.success(self.request, 'Pipeline criado com sucesso.')
        pipeline = form.save(commit=False)
        pipeline.brokerage = self.request.user.brokerage
        pipeline.save()

        # Create default stages
        default_stages = [
            ('Prospecção', 0, '#6c757d', False, False),
            ('Primeiro Contato', 1, '#0d6efd', False, False),
            ('Cotação', 2, '#ffc107', False, False),
            ('Proposta Enviada', 3, '#fd7e14', False, False),
            ('Negociação', 4, '#6610f2', False, False),
            ('Fechamento', 5, '#198754', True, False),
            ('Perdido', 6, '#dc3545', False, True),
        ]
        for name, order, color, is_won, is_lost in default_stages:
            PipelineStage.objects.create(
                brokerage=pipeline.brokerage,
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


class PipelineStageCreateView(ModuleRequiredMixin, ManagerRequiredMixin, View):
    required_module = 'crm'

    def post(self, request, pipeline_pk):
        pipeline = get_object_or_404(Pipeline, pk=pipeline_pk, brokerage=request.user.brokerage)
        form = PipelineStageForm(request.POST, user=request.user)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.pipeline = pipeline
            stage.brokerage = pipeline.brokerage
            stage.save()
            messages.success(request, f'Etapa "{stage.name}" adicionada ao pipeline.')
        else:
            messages.error(request, 'Erro ao criar etapa.')
        return redirect('crm:pipeline_manage')


class PipelineStageDeleteView(ModuleRequiredMixin, ManagerRequiredMixin, View):
    required_module = 'crm'

    def post(self, request, pk):
        stage = get_object_or_404(PipelineStage, pk=pk, brokerage=request.user.brokerage)
        if stage.deals.exists():
            messages.error(request, 'Não é possível excluir uma etapa com negociações vinculadas.')
        else:
            stage.delete()
            messages.success(request, 'Etapa excluída com sucesso.')
        return redirect('crm:pipeline_manage')
