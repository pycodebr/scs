import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q, F, Avg
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from policies.models import Policy, PolicyStatus, Proposal
from claims.models import Claim, ClaimStatus
from clients.models import Client
from renewals.models import Renewal, RenewalStatus
from crm.models import Deal, Pipeline, PipelineStage
from ai_agent.models import DashboardInsight


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        # Base querysets (broker-filtered)
        policies_qs = Policy.objects.all()
        claims_qs = Claim.objects.all()
        clients_qs = Client.objects.all()
        renewals_qs = Renewal.objects.all()
        deals_qs = Deal.objects.all()

        if user.role == 'broker':
            policies_qs = policies_qs.filter(broker=user)
            claims_qs = claims_qs.filter(broker=user)
            clients_qs = clients_qs.filter(broker=user)
            renewals_qs = renewals_qs.filter(broker=user)
            deals_qs = deals_qs.filter(broker=user)

        # KPI Cards
        active_policies = policies_qs.filter(status=PolicyStatus.ACTIVE)
        ctx['total_active_policies'] = active_policies.count()
        ctx['total_premium'] = active_policies.aggregate(
            total=Sum('premium_amount'))['total'] or Decimal('0')
        ctx['total_commission'] = active_policies.aggregate(
            total=Sum('commission_amount'))['total'] or Decimal('0')
        ctx['total_active_clients'] = clients_qs.filter(is_active=True).count()
        ctx['open_claims'] = claims_qs.filter(
            status__in=[ClaimStatus.OPEN, ClaimStatus.UNDER_ANALYSIS,
                        ClaimStatus.DOCUMENTATION_PENDING]).count()
        ctx['pending_renewals'] = renewals_qs.filter(
            status__in=[RenewalStatus.PENDING, RenewalStatus.CONTACTED,
                        RenewalStatus.QUOTE_SENT],
            due_date__lte=today + timedelta(days=30)).count()
        ctx['active_deals'] = deals_qs.filter(
            stage__is_won=False, stage__is_lost=False).count()

        # CRM conversion rate
        total_deals = deals_qs.count()
        won_deals = deals_qs.filter(stage__is_won=True).count()
        ctx['conversion_rate'] = round(
            (won_deals / total_deals * 100) if total_deals > 0 else 0, 1)

        # Monthly production (last 12 months) for Chart.js
        twelve_months_ago = today.replace(day=1) - timedelta(days=365)
        monthly_data = (
            policies_qs
            .filter(start_date__gte=twelve_months_ago)
            .annotate(month=TruncMonth('start_date'))
            .values('month')
            .annotate(
                premium=Sum('premium_amount'),
                commission=Sum('commission_amount'),
                count=Count('id'),
            )
            .order_by('month')
        )
        months_labels = []
        premium_values = []
        commission_values = []
        for entry in monthly_data:
            months_labels.append(entry['month'].strftime('%b/%y'))
            premium_values.append(float(entry['premium'] or 0))
            commission_values.append(float(entry['commission'] or 0))
        ctx['chart_months'] = json.dumps(months_labels)
        ctx['chart_premiums'] = json.dumps(premium_values)
        ctx['chart_commissions'] = json.dumps(commission_values)

        # Distribution by insurance type (for donut chart)
        type_data = (
            active_policies
            .values('insurance_type__name')
            .annotate(total=Sum('premium_amount'), count=Count('id'))
            .order_by('-total')[:8]
        )
        ctx['chart_type_labels'] = json.dumps(
            [d['insurance_type__name'] or 'N/A' for d in type_data])
        ctx['chart_type_values'] = json.dumps(
            [float(d['total'] or 0) for d in type_data])

        # Distribution by insurer (for donut chart)
        insurer_data = (
            active_policies
            .values('insurer__name')
            .annotate(total=Sum('premium_amount'), count=Count('id'))
            .order_by('-total')[:8]
        )
        ctx['chart_insurer_labels'] = json.dumps(
            [d['insurer__name'] for d in insurer_data])
        ctx['chart_insurer_values'] = json.dumps(
            [float(d['total'] or 0) for d in insurer_data])

        # Claims evolution (last 12 months)
        claims_monthly = (
            claims_qs
            .filter(occurrence_date__gte=twelve_months_ago)
            .annotate(month=TruncMonth('occurrence_date'))
            .values('month')
            .annotate(count=Count('id'), total=Sum('claimed_amount'))
            .order_by('month')
        )
        ctx['chart_claims_labels'] = json.dumps(
            [e['month'].strftime('%b/%y') for e in claims_monthly])
        ctx['chart_claims_values'] = json.dumps(
            [e['count'] for e in claims_monthly])

        # ── CRM Funnel Data ──
        default_pipeline = Pipeline.objects.filter(
            is_default=True, is_active=True).first()
        if not default_pipeline:
            default_pipeline = Pipeline.objects.filter(is_active=True).first()

        funnel_labels = []
        funnel_values = []
        funnel_amounts = []
        funnel_colors = []
        if default_pipeline:
            stages = default_pipeline.stages.all().order_by('order')
            for stage in stages:
                stage_deals = deals_qs.filter(stage=stage)
                count = stage_deals.count()
                amount = stage_deals.aggregate(
                    total=Sum('expected_value'))['total'] or Decimal('0')
                funnel_labels.append(stage.name)
                funnel_values.append(count)
                funnel_amounts.append(float(amount))
                funnel_colors.append(stage.color)
        ctx['funnel_labels'] = json.dumps(funnel_labels)
        ctx['funnel_values'] = json.dumps(funnel_values)
        ctx['funnel_amounts'] = json.dumps(funnel_amounts)
        ctx['funnel_colors'] = json.dumps(funnel_colors)
        ctx['funnel_pipeline_name'] = default_pipeline.name if default_pipeline else ''

        # ── CRM Business Insights ──
        open_deals = deals_qs.filter(stage__is_won=False, stage__is_lost=False)
        lost_deals = deals_qs.filter(stage__is_lost=True)

        # Money on the table (total expected value of open deals)
        ctx['money_on_table'] = open_deals.aggregate(
            total=Sum('expected_value'))['total'] or Decimal('0')

        # Open opportunities count
        ctx['open_opportunities'] = open_deals.count()

        # Won deals value
        won_deals_qs = deals_qs.filter(stage__is_won=True)
        ctx['won_deals_value'] = won_deals_qs.aggregate(
            total=Sum('expected_value'))['total'] or Decimal('0')
        ctx['won_deals_count'] = won_deals_qs.count()

        # Lost deals value
        ctx['lost_deals_value'] = lost_deals.aggregate(
            total=Sum('expected_value'))['total'] or Decimal('0')
        ctx['lost_deals_count'] = lost_deals.count()

        # Deals by priority (for open deals)
        priority_data = (
            open_deals
            .values('priority')
            .annotate(count=Count('id'), total=Sum('expected_value'))
            .order_by('priority')
        )
        priority_map = {'low': 'Baixa', 'medium': 'Média', 'high': 'Alta', 'urgent': 'Urgente'}
        priority_colors = {'low': '#6c757d', 'medium': '#3454d1', 'high': '#fd7e14', 'urgent': '#dc3545'}
        ctx['chart_priority_labels'] = json.dumps(
            [priority_map.get(d['priority'], d['priority']) for d in priority_data])
        ctx['chart_priority_values'] = json.dumps(
            [d['count'] for d in priority_data])
        ctx['chart_priority_colors'] = json.dumps(
            [priority_colors.get(d['priority'], '#6c757d') for d in priority_data])

        # Deals by source
        source_data = (
            deals_qs
            .values('source')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )
        source_map = {
            'referral': 'Indicação', 'website': 'Site', 'phone': 'Telefone',
            'walk_in': 'Presencial', 'social_media': 'Redes Sociais',
            'renewal': 'Renovação', 'other': 'Outro',
        }
        ctx['chart_source_labels'] = json.dumps(
            [source_map.get(d['source'], d['source']) for d in source_data])
        ctx['chart_source_values'] = json.dumps(
            [d['count'] for d in source_data])

        # Renewals next 3 months (for bar chart)
        renewal_months_labels = []
        renewal_months_values = []
        for i in range(3):
            m_start = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
            if i < 2:
                m_end = (m_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            else:
                m_end = (m_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            count = renewals_qs.filter(
                status__in=[RenewalStatus.PENDING, RenewalStatus.CONTACTED,
                            RenewalStatus.QUOTE_SENT],
                due_date__gte=m_start,
                due_date__lte=m_end,
            ).count()
            renewal_months_labels.append(m_start.strftime('%b/%y'))
            renewal_months_values.append(count)
        ctx['chart_renewal_months'] = json.dumps(renewal_months_labels)
        ctx['chart_renewal_values'] = json.dumps(renewal_months_values)

        # Dashboard AI Insight
        ctx['dashboard_insight'] = DashboardInsight.objects.filter(
            user=user
        ).first()

        # Quick shortcuts (respect permissions)
        ctx['user_role'] = user.role

        # Recent tables
        ctx['recent_policies'] = (
            policies_qs
            .select_related('client', 'insurer')
            .order_by('-created_at')[:10]
        )
        ctx['upcoming_renewals'] = (
            renewals_qs
            .filter(status__in=[RenewalStatus.PENDING, RenewalStatus.CONTACTED,
                                RenewalStatus.QUOTE_SENT])
            .select_related('policy', 'policy__client', 'broker')
            .order_by('due_date')[:10]
        )
        ctx['recent_claims'] = (
            claims_qs
            .filter(status__in=[ClaimStatus.OPEN, ClaimStatus.UNDER_ANALYSIS])
            .select_related('client', 'policy')
            .order_by('-created_at')[:5]
        )
        # Recent CRM deals
        ctx['recent_deals'] = (
            open_deals
            .select_related('client', 'stage', 'broker')
            .order_by('-updated_at')[:5]
        )

        return ctx


class GlobalSearchView(LoginRequiredMixin, View):
    """AJAX endpoint for global search autocomplete."""

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 3:
            return JsonResponse({'results': []})

        user = request.user
        results = []
        limit = 5

        # Search clients
        clients_qs = Client.objects.filter(
            Q(name__icontains=q) | Q(cpf_cnpj__icontains=q) | Q(email__icontains=q)
        )
        if user.role == 'broker':
            clients_qs = clients_qs.filter(broker=user)
        for c in clients_qs[:limit]:
            results.append({
                'type': 'Cliente',
                'icon': 'feather-users',
                'label': c.name,
                'detail': c.cpf_cnpj,
                'url': f'/clients/{c.pk}/',
            })

        # Search policies
        policies_qs = Policy.objects.filter(
            Q(policy_number__icontains=q) | Q(client__name__icontains=q)
        ).select_related('client')
        if user.role == 'broker':
            policies_qs = policies_qs.filter(broker=user)
        for p in policies_qs[:limit]:
            results.append({
                'type': 'Apólice',
                'icon': 'feather-file-text',
                'label': p.policy_number,
                'detail': p.client.name,
                'url': f'/policies/{p.pk}/',
            })

        # Search proposals
        proposals_qs = Proposal.objects.filter(
            Q(proposal_number__icontains=q) | Q(client__name__icontains=q)
        ).select_related('client')
        if user.role == 'broker':
            proposals_qs = proposals_qs.filter(broker=user)
        for pr in proposals_qs[:limit]:
            results.append({
                'type': 'Proposta',
                'icon': 'feather-file-plus',
                'label': pr.proposal_number,
                'detail': pr.client.name,
                'url': f'/policies/proposals/{pr.pk}/',
            })

        # Search claims
        claims_qs = Claim.objects.filter(
            Q(claim_number__icontains=q) | Q(client__name__icontains=q)
        ).select_related('client')
        if user.role == 'broker':
            claims_qs = claims_qs.filter(broker=user)
        for cl in claims_qs[:limit]:
            results.append({
                'type': 'Sinistro',
                'icon': 'feather-alert-circle',
                'label': cl.claim_number,
                'detail': cl.client.name,
                'url': f'/claims/{cl.pk}/',
            })

        return JsonResponse({'results': results[:15]})
