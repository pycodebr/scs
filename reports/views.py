import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, F, Value, CharField
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView, FormView

from xhtml2pdf import pisa

from utils.mixins import ManagerRequiredMixin

from .forms import (
    ProductionFilterForm, CommissionFilterForm, InsurerPortfolioFilterForm,
    InsuranceTypePortfolioFilterForm, ClaimsFilterForm, LossRatioFilterForm,
    RenewalFilterForm, ClientsByBrokerFilterForm, CRMFunnelFilterForm,
    EndorsementFilterForm,
)


class ReportIndexView(ManagerRequiredMixin, TemplateView):
    template_name = 'reports/report_index.html'


class BaseReportView(ManagerRequiredMixin, FormView):
    """Base class for all report views."""
    export_filename = 'relatorio.csv'
    pdf_title = 'Relatório'

    def get_initial(self):
        initial = super().get_initial()
        today = date.today()
        initial.setdefault('start_date', today.replace(day=1))
        initial.setdefault('end_date', today)
        return initial

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if request.GET.get('start_date'):
            form = self.form_class(request.GET)
            if form.is_valid():
                ctx = self.get_context_data(form=form)
                ctx['results'] = self.get_report_data(form.cleaned_data)
                ctx['filters'] = form.cleaned_data
                export = request.GET.get('export')
                if export == 'csv':
                    return self.export_csv(ctx['results'], form.cleaned_data)
                if export == 'pdf':
                    return self.export_pdf(ctx['results'], form.cleaned_data)
                return self.render_to_response(ctx)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_report_data(self, filters):
        return []

    def export_csv(self, results, filters):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.export_filename}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        self.write_csv(writer, results, filters)
        return response

    def write_csv(self, writer, results, filters):
        pass

    def export_pdf(self, results, filters):
        pdf_data = self.get_pdf_data(results, filters)
        period = ''
        if filters.get('start_date') and filters.get('end_date'):
            period = f"{filters['start_date'].strftime('%d/%m/%Y')} a {filters['end_date'].strftime('%d/%m/%Y')}"
        context = {
            'title': pdf_data.get('title', self.pdf_title),
            'period': period,
            'generated_at': date.today().strftime('%d/%m/%Y'),
            'summary': pdf_data.get('summary', []),
            'headers': pdf_data.get('headers', []),
            'rows': pdf_data.get('rows', []),
        }
        html = render_to_string('reports/_report_pdf.html', context)
        response = HttpResponse(content_type='application/pdf')
        pdf_filename = self.export_filename.replace('.csv', '.pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=response, encoding='utf-8')
        return response

    def get_pdf_data(self, results, filters):
        return {'title': self.pdf_title, 'summary': [], 'headers': [], 'rows': []}


class ProductionReportView(BaseReportView):
    template_name = 'reports/report_production.html'
    form_class = ProductionFilterForm
    export_filename = 'producao.csv'
    pdf_title = 'Produção'

    def get_report_data(self, filters):
        from policies.models import Policy
        qs = Policy.objects.filter(
            start_date__gte=filters['start_date'],
            start_date__lte=filters['end_date'],
        ).select_related('client', 'insurer', 'insurance_type', 'broker')
        if filters.get('broker'):
            qs = qs.filter(broker_id=filters['broker'])
        if filters.get('insurer'):
            qs = qs.filter(insurer_id=filters['insurer'])
        return {
            'policies': qs.order_by('-start_date'),
            'totals': qs.aggregate(
                total_premium=Coalesce(Sum('premium_amount'), Decimal('0')),
                total_commission=Coalesce(Sum('commission_amount'), Decimal('0')),
                count=Count('id'),
            ),
        }

    def write_csv(self, writer, results, filters):
        writer.writerow(['Número', 'Cliente', 'Seguradora', 'Tipo', 'Início', 'Fim', 'Prêmio', 'Comissão'])
        for p in results['policies']:
            writer.writerow([
                p.policy_number, p.client.name, p.insurer.name,
                p.insurance_type.name, p.start_date.strftime('%d/%m/%Y'),
                p.end_date.strftime('%d/%m/%Y'), p.premium_amount, p.commission_amount,
            ])

    def get_pdf_data(self, results, filters):
        t = results['totals']
        return {
            'title': 'Produção',
            'summary': [
                {'label': 'Apólices', 'value': t['count']},
                {'label': 'Prêmio Total', 'value': f"R$ {t['total_premium']:.2f}"},
                {'label': 'Comissão Total', 'value': f"R$ {t['total_commission']:.2f}"},
            ],
            'headers': [
                {'label': 'Número'}, {'label': 'Cliente'}, {'label': 'Seguradora'},
                {'label': 'Tipo'}, {'label': 'Início'}, {'label': 'Fim'},
                {'label': 'Prêmio', 'align': 'text-end'}, {'label': 'Comissão', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': p.policy_number}, {'value': p.client.name},
                    {'value': p.insurer.name}, {'value': p.insurance_type.name},
                    {'value': p.start_date.strftime('%d/%m/%Y')},
                    {'value': p.end_date.strftime('%d/%m/%Y')},
                    {'value': f'R$ {p.premium_amount:.2f}', 'align': 'text-end'},
                    {'value': f'R$ {p.commission_amount:.2f}', 'align': 'text-end'},
                ] for p in results['policies']
            ],
        }


class CommissionReportView(BaseReportView):
    template_name = 'reports/report_commissions.html'
    form_class = CommissionFilterForm
    export_filename = 'comissoes.csv'
    pdf_title = 'Comissões'

    def get_report_data(self, filters):
        from policies.models import Policy
        from django.contrib.auth import get_user_model
        User = get_user_model()
        qs = Policy.objects.filter(
            start_date__gte=filters['start_date'],
            start_date__lte=filters['end_date'],
        )
        if filters.get('broker'):
            qs = qs.filter(broker_id=filters['broker'])
        data = (
            qs.values('broker__id', 'broker__first_name', 'broker__last_name')
            .annotate(
                total_premium=Sum('premium_amount'),
                total_commission=Sum('commission_amount'),
                count=Count('id'),
            )
            .order_by('-total_commission')
        )
        grand_total = qs.aggregate(
            total_premium=Coalesce(Sum('premium_amount'), Decimal('0')),
            total_commission=Coalesce(Sum('commission_amount'), Decimal('0')),
        )
        return {'data': data, 'grand_total': grand_total}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Corretor', 'Apólices', 'Prêmio Total', 'Comissão Total'])
        for row in results['data']:
            name = f"{row['broker__first_name']} {row['broker__last_name']}"
            writer.writerow([name, row['count'], row['total_premium'], row['total_commission']])

    def get_pdf_data(self, results, filters):
        gt = results['grand_total']
        return {
            'title': 'Comissões',
            'summary': [
                {'label': 'Prêmio Total', 'value': f"R$ {gt['total_premium']:.2f}"},
                {'label': 'Comissão Total', 'value': f"R$ {gt['total_commission']:.2f}"},
            ],
            'headers': [
                {'label': 'Corretor'}, {'label': 'Apólices', 'align': 'text-center'},
                {'label': 'Prêmio Total', 'align': 'text-end'},
                {'label': 'Comissão Total', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': f"{r['broker__first_name']} {r['broker__last_name']}"},
                    {'value': r['count'], 'align': 'text-center'},
                    {'value': f"R$ {r['total_premium']:.2f}", 'align': 'text-end'},
                    {'value': f"R$ {r['total_commission']:.2f}", 'align': 'text-end'},
                ] for r in results['data']
            ],
        }


class InsurerPortfolioReportView(BaseReportView):
    template_name = 'reports/report_insurer_portfolio.html'
    form_class = InsurerPortfolioFilterForm
    export_filename = 'carteira_seguradora.csv'
    pdf_title = 'Carteira por Seguradora'

    def get_report_data(self, filters):
        from policies.models import Policy
        qs = Policy.objects.filter(
            start_date__gte=filters['start_date'],
            start_date__lte=filters['end_date'],
        )
        if filters.get('status'):
            qs = qs.filter(status=filters['status'])
        data = (
            qs.values('insurer__name')
            .annotate(
                total_premium=Sum('premium_amount'),
                total_insured=Sum('insured_amount'),
                count=Count('id'),
            )
            .order_by('-total_premium')
        )
        return {'data': data}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Seguradora', 'Apólices', 'Prêmio Total', 'Imp. Segurada Total'])
        for row in results['data']:
            writer.writerow([row['insurer__name'], row['count'], row['total_premium'], row['total_insured']])

    def get_pdf_data(self, results, filters):
        return {
            'title': 'Carteira por Seguradora',
            'headers': [
                {'label': 'Seguradora'}, {'label': 'Apólices', 'align': 'text-center'},
                {'label': 'Prêmio Total', 'align': 'text-end'},
                {'label': 'Imp. Segurada Total', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': r['insurer__name']},
                    {'value': r['count'], 'align': 'text-center'},
                    {'value': f"R$ {r['total_premium']:.2f}", 'align': 'text-end'},
                    {'value': f"R$ {r['total_insured']:.2f}", 'align': 'text-end'},
                ] for r in results['data']
            ],
        }


class InsuranceTypePortfolioReportView(BaseReportView):
    template_name = 'reports/report_type_portfolio.html'
    form_class = InsuranceTypePortfolioFilterForm
    export_filename = 'carteira_tipo_seguro.csv'
    pdf_title = 'Carteira por Ramo'

    def get_report_data(self, filters):
        from policies.models import Policy
        qs = Policy.objects.filter(
            start_date__gte=filters['start_date'],
            start_date__lte=filters['end_date'],
        )
        if filters.get('insurer'):
            qs = qs.filter(insurer_id=filters['insurer'])
        data = (
            qs.values('insurance_type__name')
            .annotate(
                total_premium=Sum('premium_amount'),
                count=Count('id'),
            )
            .order_by('-total_premium')
        )
        return {'data': data}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Ramo', 'Apólices', 'Prêmio Total'])
        for row in results['data']:
            writer.writerow([row['insurance_type__name'], row['count'], row['total_premium']])

    def get_pdf_data(self, results, filters):
        return {
            'title': 'Carteira por Ramo',
            'headers': [
                {'label': 'Ramo'}, {'label': 'Apólices', 'align': 'text-center'},
                {'label': 'Prêmio Total', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': r['insurance_type__name']},
                    {'value': r['count'], 'align': 'text-center'},
                    {'value': f"R$ {r['total_premium']:.2f}", 'align': 'text-end'},
                ] for r in results['data']
            ],
        }


class ClaimsReportView(BaseReportView):
    template_name = 'reports/report_claims.html'
    form_class = ClaimsFilterForm
    export_filename = 'sinistros.csv'
    pdf_title = 'Sinistros por Período'

    def get_report_data(self, filters):
        from claims.models import Claim
        qs = Claim.objects.filter(
            occurrence_date__gte=filters['start_date'],
            occurrence_date__lte=filters['end_date'],
        ).select_related('client', 'policy', 'policy__insurer')
        if filters.get('status'):
            qs = qs.filter(status=filters['status'])
        if filters.get('insurer'):
            qs = qs.filter(policy__insurer_id=filters['insurer'])
        totals = qs.aggregate(
            total_claimed=Coalesce(Sum('claimed_amount'), Decimal('0')),
            total_approved=Coalesce(Sum('approved_amount'), Decimal('0')),
            count=Count('id'),
        )
        return {'claims': qs.order_by('-occurrence_date'), 'totals': totals}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Sinistro', 'Cliente', 'Apólice', 'Seguradora', 'Data', 'Status', 'Reclamado', 'Aprovado'])
        for c in results['claims']:
            writer.writerow([
                c.claim_number, c.client.name, c.policy.policy_number,
                c.policy.insurer.name, c.occurrence_date.strftime('%d/%m/%Y'),
                c.get_status_display(), c.claimed_amount, c.approved_amount or 0,
            ])

    def get_pdf_data(self, results, filters):
        t = results['totals']
        return {
            'title': 'Sinistros por Período',
            'summary': [
                {'label': 'Total de Sinistros', 'value': t['count']},
                {'label': 'Valor Reclamado', 'value': f"R$ {t['total_claimed']:.2f}"},
                {'label': 'Valor Aprovado', 'value': f"R$ {t['total_approved']:.2f}"},
            ],
            'headers': [
                {'label': 'Sinistro'}, {'label': 'Cliente'}, {'label': 'Apólice'},
                {'label': 'Seguradora'}, {'label': 'Data'}, {'label': 'Status'},
                {'label': 'Reclamado', 'align': 'text-end'},
                {'label': 'Aprovado', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': c.claim_number}, {'value': c.client.name},
                    {'value': c.policy.policy_number}, {'value': c.policy.insurer.name},
                    {'value': c.occurrence_date.strftime('%d/%m/%Y')},
                    {'value': c.get_status_display()},
                    {'value': f'R$ {c.claimed_amount:.2f}', 'align': 'text-end'},
                    {'value': f'R$ {(c.approved_amount or 0):.2f}', 'align': 'text-end'},
                ] for c in results['claims']
            ],
        }


class LossRatioReportView(BaseReportView):
    template_name = 'reports/report_loss_ratio.html'
    form_class = LossRatioFilterForm
    export_filename = 'sinistralidade.csv'
    pdf_title = 'Sinistralidade'

    def get_report_data(self, filters):
        from policies.models import Policy
        from claims.models import Claim
        p_qs = Policy.objects.filter(
            start_date__gte=filters['start_date'],
            start_date__lte=filters['end_date'],
        )
        c_qs = Claim.objects.filter(
            occurrence_date__gte=filters['start_date'],
            occurrence_date__lte=filters['end_date'],
            status__in=['approved', 'partially_approved', 'paid'],
        )
        if filters.get('insurer'):
            p_qs = p_qs.filter(insurer_id=filters['insurer'])
            c_qs = c_qs.filter(policy__insurer_id=filters['insurer'])

        # By insurer
        premium_by_insurer = dict(
            p_qs.values_list('insurer__name').annotate(t=Sum('premium_amount')).values_list('insurer__name', 't')
        )
        claims_by_insurer = dict(
            c_qs.values_list('policy__insurer__name').annotate(t=Sum('approved_amount')).values_list('policy__insurer__name', 't')
        )
        all_insurers = set(list(premium_by_insurer.keys()) + list(claims_by_insurer.keys()))
        data = []
        for name in sorted(all_insurers):
            premium = premium_by_insurer.get(name) or Decimal('0')
            claims_val = claims_by_insurer.get(name) or Decimal('0')
            ratio = (claims_val / premium * 100) if premium > 0 else Decimal('0')
            data.append({
                'insurer': name,
                'premium': premium,
                'claims': claims_val,
                'ratio': round(ratio, 2),
            })
        data.sort(key=lambda x: x['ratio'], reverse=True)
        return {'data': data}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Seguradora', 'Prêmio', 'Sinistros Aprovados', 'Sinistralidade (%)'])
        for row in results['data']:
            writer.writerow([row['insurer'], row['premium'], row['claims'], row['ratio']])

    def get_pdf_data(self, results, filters):
        return {
            'title': 'Sinistralidade',
            'headers': [
                {'label': 'Seguradora'}, {'label': 'Prêmio', 'align': 'text-end'},
                {'label': 'Sinistros Aprovados', 'align': 'text-end'},
                {'label': 'Sinistralidade', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': r['insurer']},
                    {'value': f"R$ {r['premium']:.2f}", 'align': 'text-end'},
                    {'value': f"R$ {r['claims']:.2f}", 'align': 'text-end'},
                    {'value': f"{r['ratio']}%", 'align': 'text-end'},
                ] for r in results['data']
            ],
        }


class RenewalReportView(BaseReportView):
    template_name = 'reports/report_renewals.html'
    form_class = RenewalFilterForm
    export_filename = 'renovacoes.csv'
    pdf_title = 'Renovações'

    def get_report_data(self, filters):
        from renewals.models import Renewal
        qs = Renewal.objects.filter(
            due_date__gte=filters['start_date'],
            due_date__lte=filters['end_date'],
        ).select_related('policy', 'policy__client', 'policy__insurer', 'broker')
        if filters.get('broker'):
            qs = qs.filter(broker_id=filters['broker'])
        totals = qs.aggregate(count=Count('id'))
        status_summary = qs.values('status').annotate(count=Count('id')).order_by('status')
        return {'renewals': qs.order_by('due_date'), 'totals': totals, 'status_summary': status_summary}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Apólice', 'Cliente', 'Seguradora', 'Vencimento', 'Status', 'Corretor'])
        for r in results['renewals']:
            writer.writerow([
                r.policy.policy_number, r.policy.client.name,
                r.policy.insurer.name, r.due_date.strftime('%d/%m/%Y'),
                r.get_status_display(), r.broker.get_full_name(),
            ])

    def get_pdf_data(self, results, filters):
        summary = [{'label': 'Total de Renovações', 'value': results['totals']['count']}]
        for s in results['status_summary']:
            summary.append({'label': s['status'], 'value': s['count']})
        return {
            'title': 'Renovações',
            'summary': summary,
            'headers': [
                {'label': 'Apólice'}, {'label': 'Cliente'}, {'label': 'Seguradora'},
                {'label': 'Vencimento'}, {'label': 'Status'}, {'label': 'Corretor'},
            ],
            'rows': [
                [
                    {'value': r.policy.policy_number}, {'value': r.policy.client.name},
                    {'value': r.policy.insurer.name},
                    {'value': r.due_date.strftime('%d/%m/%Y')},
                    {'value': r.get_status_display()},
                    {'value': r.broker.get_full_name()},
                ] for r in results['renewals']
            ],
        }


class ClientsByBrokerReportView(ManagerRequiredMixin, FormView):
    template_name = 'reports/report_clients_by_broker.html'
    form_class = ClientsByBrokerFilterForm

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        ctx = self.get_context_data(form=form)
        if request.GET.get('submit'):
            form = self.form_class(request.GET)
            if form.is_valid():
                ctx['form'] = form
                ctx['results'] = self.get_report_data(form.cleaned_data)
                export = request.GET.get('export')
                if export == 'csv':
                    return self.export_csv(ctx['results'])
                if export == 'pdf':
                    return self.export_pdf(ctx['results'])
        return self.render_to_response(ctx)

    def get_report_data(self, filters):
        from django.contrib.auth import get_user_model
        from clients.models import Client
        User = get_user_model()
        qs = Client.objects.all()
        if filters.get('broker'):
            qs = qs.filter(broker_id=filters['broker'])
        if filters.get('status') == 'active':
            qs = qs.filter(is_active=True)
        elif filters.get('status') == 'inactive':
            qs = qs.filter(is_active=False)
        data = (
            qs.values('broker__id', 'broker__first_name', 'broker__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return {'data': data, 'total': qs.count()}

    def export_csv(self, results):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clientes_por_corretor.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Corretor', 'Clientes'])
        for row in results['data']:
            name = f"{row['broker__first_name']} {row['broker__last_name']}"
            writer.writerow([name, row['count']])
        return response

    def export_pdf(self, results):
        context = {
            'title': 'Clientes por Corretor',
            'period': '',
            'generated_at': date.today().strftime('%d/%m/%Y'),
            'summary': [{'label': 'Total de Clientes', 'value': results['total']}],
            'headers': [
                {'label': 'Corretor'}, {'label': 'Clientes', 'align': 'text-center'},
            ],
            'rows': [
                [
                    {'value': f"{r['broker__first_name']} {r['broker__last_name']}"},
                    {'value': r['count'], 'align': 'text-center'},
                ] for r in results['data']
            ],
        }
        html = render_to_string('reports/_report_pdf.html', context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="clientes_por_corretor.pdf"'
        pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=response, encoding='utf-8')
        return response


class CRMFunnelReportView(BaseReportView):
    template_name = 'reports/report_crm_funnel.html'
    form_class = CRMFunnelFilterForm
    export_filename = 'funil_crm.csv'
    pdf_title = 'Funil CRM'

    def get_report_data(self, filters):
        from crm.models import Deal, PipelineStage
        qs = Deal.objects.filter(
            created_at__date__gte=filters['start_date'],
            created_at__date__lte=filters['end_date'],
        )
        if filters.get('broker'):
            qs = qs.filter(broker_id=filters['broker'])
        if filters.get('pipeline'):
            qs = qs.filter(pipeline_id=filters['pipeline'])
        data = (
            qs.values('stage__name', 'stage__order')
            .annotate(
                count=Count('id'),
                total_value=Coalesce(Sum('expected_value'), Decimal('0')),
            )
            .order_by('stage__order')
        )
        return {'data': data, 'total': qs.count()}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Etapa', 'Deals', 'Valor Total'])
        for row in results['data']:
            writer.writerow([row['stage__name'], row['count'], row['total_value']])

    def get_pdf_data(self, results, filters):
        return {
            'title': 'Funil CRM',
            'summary': [{'label': 'Total de Deals', 'value': results['total']}],
            'headers': [
                {'label': 'Etapa'}, {'label': 'Deals', 'align': 'text-center'},
                {'label': 'Valor Total', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': r['stage__name']},
                    {'value': r['count'], 'align': 'text-center'},
                    {'value': f"R$ {r['total_value']:.2f}", 'align': 'text-end'},
                ] for r in results['data']
            ],
        }


class EndorsementReportView(BaseReportView):
    template_name = 'reports/report_endorsements.html'
    form_class = EndorsementFilterForm
    export_filename = 'endossos.csv'
    pdf_title = 'Endossos'

    def get_report_data(self, filters):
        from endorsements.models import Endorsement
        qs = Endorsement.objects.filter(
            request_date__gte=filters['start_date'],
            request_date__lte=filters['end_date'],
        ).select_related('policy', 'policy__client', 'requested_by')
        if filters.get('endorsement_type'):
            qs = qs.filter(endorsement_type=filters['endorsement_type'])
        totals = qs.aggregate(
            count=Count('id'),
            total_diff=Coalesce(Sum('premium_difference'), Decimal('0')),
        )
        type_summary = (
            qs.values('endorsement_type')
            .annotate(count=Count('id'), total_diff=Sum('premium_difference'))
            .order_by('endorsement_type')
        )
        return {'endorsements': qs.order_by('-request_date'), 'totals': totals, 'type_summary': type_summary}

    def write_csv(self, writer, results, filters):
        writer.writerow(['Endosso', 'Apólice', 'Cliente', 'Tipo', 'Status', 'Data', 'Dif. Prêmio'])
        for e in results['endorsements']:
            writer.writerow([
                e.endorsement_number, e.policy.policy_number,
                e.policy.client.name, e.get_endorsement_type_display(),
                e.get_status_display(), e.request_date.strftime('%d/%m/%Y'),
                e.premium_difference,
            ])

    def get_pdf_data(self, results, filters):
        t = results['totals']
        return {
            'title': 'Endossos',
            'summary': [
                {'label': 'Total de Endossos', 'value': t['count']},
                {'label': 'Diferença de Prêmio', 'value': f"R$ {t['total_diff']:.2f}"},
            ],
            'headers': [
                {'label': 'Endosso'}, {'label': 'Apólice'}, {'label': 'Cliente'},
                {'label': 'Tipo'}, {'label': 'Data'}, {'label': 'Status'},
                {'label': 'Dif. Prêmio', 'align': 'text-end'},
            ],
            'rows': [
                [
                    {'value': e.endorsement_number}, {'value': e.policy.policy_number},
                    {'value': e.policy.client.name}, {'value': e.get_endorsement_type_display()},
                    {'value': e.request_date.strftime('%d/%m/%Y')},
                    {'value': e.get_status_display()},
                    {'value': f'R$ {e.premium_difference:.2f}', 'align': 'text-end'},
                ] for e in results['endorsements']
            ],
        }
