"""Agent tools for querying system data."""
from datetime import date, timedelta

from langchain_core.tools import tool

from django.db.models import Sum, Count, Q

from .permissions import get_filtered_queryset


def _fmt_decimal(value) -> str:
    """Format Decimal to a readable BRL currency string."""
    if value is None:
        return 'R$ 0,00'
    return f'R$ {float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_date(d) -> str:
    """Format date to dd/mm/yyyy string."""
    if d is None:
        return '-'
    return d.strftime('%d/%m/%Y')


def build_tools_for_user(user):
    """Build agent tools with the user bound via closure.

    This ensures the user is never exposed to the LLM schema and that
    all queries are filtered by the user's role.
    """

    @tool
    def search_clients(query: str = '') -> str:
        """Busca clientes vinculados ao usuário logado. Aceita filtro por nome, CPF/CNPJ ou email."""
        from clients.models import Client
        qs = get_filtered_queryset(user, Client)
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(cpf_cnpj__icontains=query) |
                Q(email__icontains=query)
            )
        qs = qs[:20]
        if not qs:
            return 'Nenhum cliente encontrado.'
        results = []
        for c in qs:
            results.append(
                f'- {c.name} | CPF/CNPJ: {c.cpf_cnpj} | Email: {c.email} | '
                f'Tel: {c.phone} | Ativo: {"Sim" if c.is_active else "Não"} | '
                f'Corretor: {c.broker.get_full_name()}'
            )
        return f'Clientes encontrados ({len(results)}):\n' + '\n'.join(results)

    @tool
    def search_policies(query: str = '', status: str = '') -> str:
        """Busca apólices vinculadas ao usuário logado. Filtros: query (número ou cliente), status (active/expired/cancelled/pending)."""
        from policies.models import Policy
        qs = get_filtered_queryset(user, Policy).select_related('client', 'insurer', 'insurance_type')
        if query:
            qs = qs.filter(
                Q(policy_number__icontains=query) |
                Q(client__name__icontains=query)
            )
        if status:
            qs = qs.filter(status=status)
        qs = qs[:20]
        if not qs:
            return 'Nenhuma apólice encontrada.'
        results = []
        for p in qs:
            results.append(
                f'- {p.policy_number} | Cliente: {p.client.name} | '
                f'Seguradora: {p.insurer.name} | Ramo: {p.insurance_type.name} | '
                f'Status: {p.get_status_display()} | '
                f'Vigência: {_fmt_date(p.start_date)} a {_fmt_date(p.end_date)} | '
                f'Prêmio: {_fmt_decimal(p.premium_amount)} | '
                f'Comissão: {_fmt_decimal(p.commission_amount)}'
            )
        return f'Apólices encontradas ({len(results)}):\n' + '\n'.join(results)

    @tool
    def search_proposals(query: str = '', status: str = '') -> str:
        """Busca propostas vinculadas ao usuário logado. Filtros: query (número ou cliente), status (draft/submitted/under_analysis/approved/rejected/cancelled)."""
        from policies.models import Proposal
        qs = get_filtered_queryset(user, Proposal).select_related('client', 'insurer', 'insurance_type')
        if query:
            qs = qs.filter(
                Q(proposal_number__icontains=query) |
                Q(client__name__icontains=query)
            )
        if status:
            qs = qs.filter(status=status)
        qs = qs[:20]
        if not qs:
            return 'Nenhuma proposta encontrada.'
        results = []
        for p in qs:
            results.append(
                f'- {p.proposal_number} | Cliente: {p.client.name} | '
                f'Seguradora: {p.insurer.name} | Ramo: {p.insurance_type.name} | '
                f'Status: {p.get_status_display()} | '
                f'Prêmio: {_fmt_decimal(p.premium_amount)} | '
                f'Envio: {_fmt_date(p.submission_date)}'
            )
        return f'Propostas encontradas ({len(results)}):\n' + '\n'.join(results)

    @tool
    def search_claims(query: str = '', status: str = '') -> str:
        """Busca sinistros vinculados ao usuário logado. Filtros: query (número ou cliente), status (open/under_analysis/approved/denied/paid/closed)."""
        from claims.models import Claim
        qs = get_filtered_queryset(user, Claim).select_related('client', 'policy')
        if query:
            qs = qs.filter(
                Q(claim_number__icontains=query) |
                Q(client__name__icontains=query)
            )
        if status:
            qs = qs.filter(status=status)
        qs = qs[:20]
        if not qs:
            return 'Nenhum sinistro encontrado.'
        results = []
        for c in qs:
            results.append(
                f'- {c.claim_number} | Cliente: {c.client.name} | '
                f'Apólice: {c.policy.policy_number} | '
                f'Status: {c.get_status_display()} | '
                f'Valor Reclamado: {_fmt_decimal(c.claimed_amount)} | '
                f'Valor Aprovado: {_fmt_decimal(c.approved_amount)} | '
                f'Data Ocorrência: {_fmt_date(c.occurrence_date)}'
            )
        return f'Sinistros encontrados ({len(results)}):\n' + '\n'.join(results)

    @tool
    def search_deals(query: str = '', status: str = '') -> str:
        """Busca negócios/deals do CRM vinculados ao usuário logado. Filtros: query (título ou cliente), status (open/won/lost)."""
        from crm.models import Deal
        qs = get_filtered_queryset(user, Deal).select_related('client', 'stage', 'pipeline')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(client__name__icontains=query)
            )
        if status == 'open':
            qs = qs.filter(stage__is_won=False, stage__is_lost=False)
        elif status == 'won':
            qs = qs.filter(stage__is_won=True)
        elif status == 'lost':
            qs = qs.filter(stage__is_lost=True)
        qs = qs[:20]
        if not qs:
            return 'Nenhum negócio encontrado.'
        results = []
        for d in qs:
            results.append(
                f'- {d.title} | Cliente: {d.client.name} | '
                f'Etapa: {d.stage.name} | Pipeline: {d.pipeline.name} | '
                f'Prioridade: {d.get_priority_display()} | '
                f'Valor: {_fmt_decimal(d.expected_value)} | '
                f'Previsão: {_fmt_date(d.expected_close_date)}'
            )
        return f'Negócios encontrados ({len(results)}):\n' + '\n'.join(results)

    @tool
    def search_renewals(status: str = '') -> str:
        """Busca renovações vinculadas ao usuário logado. Filtros: status (pending/contacted/quote_sent/renewed/not_renewed/cancelled)."""
        from renewals.models import Renewal
        qs = get_filtered_queryset(user, Renewal).select_related(
            'policy', 'policy__client', 'policy__insurer'
        )
        if status:
            qs = qs.filter(status=status)
        qs = qs[:20]
        if not qs:
            return 'Nenhuma renovação encontrada.'
        results = []
        for r in qs:
            urgency = ''
            if r.is_overdue:
                urgency = ' [VENCIDA]'
            elif r.is_urgent:
                urgency = ' [URGENTE]'
            results.append(
                f'- Apólice: {r.policy.policy_number} | Cliente: {r.policy.client.name} | '
                f'Seguradora: {r.policy.insurer.name} | '
                f'Status: {r.get_status_display()}{urgency} | '
                f'Vencimento: {_fmt_date(r.due_date)} | '
                f'Prêmio Atual: {_fmt_decimal(r.policy.premium_amount)} | '
                f'Novo Prêmio: {_fmt_decimal(r.new_premium)}'
            )
        return f'Renovações encontradas ({len(results)}):\n' + '\n'.join(results)

    @tool
    def get_summary_metrics() -> str:
        """Retorna métricas agregadas dos dados do usuário logado: totais, contagens, valores."""
        from policies.models import Policy, PolicyStatus
        from claims.models import Claim, ClaimStatus
        from clients.models import Client
        from renewals.models import Renewal, RenewalStatus
        from crm.models import Deal

        today = date.today()
        policies = get_filtered_queryset(user, Policy)
        active_policies = policies.filter(status=PolicyStatus.ACTIVE)
        clients = get_filtered_queryset(user, Client)
        claims = get_filtered_queryset(user, Claim)
        renewals = get_filtered_queryset(user, Renewal)
        deals = get_filtered_queryset(user, Deal)

        total_premium = active_policies.aggregate(t=Sum('premium_amount'))['t'] or 0
        total_commission = active_policies.aggregate(t=Sum('commission_amount'))['t'] or 0
        open_claims = claims.filter(
            status__in=[ClaimStatus.OPEN, ClaimStatus.UNDER_ANALYSIS, ClaimStatus.DOCUMENTATION_PENDING]
        ).count()
        claimed_amount = claims.filter(
            status__in=[ClaimStatus.OPEN, ClaimStatus.UNDER_ANALYSIS]
        ).aggregate(t=Sum('claimed_amount'))['t'] or 0
        pending_renewals = renewals.filter(
            status__in=[RenewalStatus.PENDING, RenewalStatus.CONTACTED, RenewalStatus.QUOTE_SENT],
            due_date__lte=today + timedelta(days=30),
        ).count()
        overdue_renewals = renewals.filter(
            status__in=[RenewalStatus.PENDING, RenewalStatus.CONTACTED, RenewalStatus.QUOTE_SENT],
            due_date__lt=today,
        ).count()

        open_deals = deals.filter(stage__is_won=False, stage__is_lost=False)
        money_on_table = open_deals.aggregate(t=Sum('expected_value'))['t'] or 0
        won_deals = deals.filter(stage__is_won=True)
        won_value = won_deals.aggregate(t=Sum('expected_value'))['t'] or 0
        lost_deals = deals.filter(stage__is_lost=True)
        total_deals = deals.count()
        conversion_rate = round((won_deals.count() / total_deals * 100) if total_deals > 0 else 0, 1)

        return f"""Métricas Resumo:
- Apólices ativas: {active_policies.count()}
- Prêmio total em carteira: {_fmt_decimal(total_premium)}
- Comissão total em carteira: {_fmt_decimal(total_commission)}
- Clientes ativos: {clients.filter(is_active=True).count()}
- Sinistros abertos: {open_claims}
- Valor reclamado (abertos): {_fmt_decimal(claimed_amount)}
- Renovações pendentes (30 dias): {pending_renewals}
- Renovações vencidas: {overdue_renewals}
- Negócios em andamento: {open_deals.count()}
- Dinheiro na mesa (valor esperado): {_fmt_decimal(money_on_table)}
- Negócios ganhos: {won_deals.count()} ({_fmt_decimal(won_value)})
- Negócios perdidos: {lost_deals.count()}
- Taxa de conversão CRM: {conversion_rate}%
- Total de clientes: {clients.count()}
- Total de apólices: {policies.count()}"""

    return [
        search_clients,
        search_policies,
        search_proposals,
        search_claims,
        search_deals,
        search_renewals,
        get_summary_metrics,
    ]
