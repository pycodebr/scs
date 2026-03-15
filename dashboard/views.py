import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from policies.models import Policy, PolicyStatus
from claims.models import Claim, ClaimStatus
from clients.models import Client
from renewals.models import Renewal, RenewalStatus
from crm.models import Deal, PipelineStage


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

        return ctx
