"""Inicializacao do agente LangChain com tools e memoria."""
import logging
from datetime import date

from django.conf import settings

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from .prompts import SYSTEM_PROMPT, ROLE_DISPLAY, INSIGHT_PROMPT, SUMMARY_PROMPTS
from .tools import build_tools_for_user

logger = logging.getLogger(__name__)


def _get_llm():
    """Cria instancia do LLM."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
        max_tokens=2048,
    )


def _build_system_message(user) -> str:
    """Monta o system prompt personalizado para o usuario."""
    role_display = ROLE_DISPLAY.get(user.role, user.get_role_display())
    return SYSTEM_PROMPT.format(
        role=role_display,
        user_name=user.get_full_name(),
        current_date=date.today().strftime('%d/%m/%Y'),
    )


def get_agent_response(user, message: str, history: list[dict] | None = None) -> str:
    """Envia mensagem ao agente e retorna a resposta.

    Args:
        user: Usuario Django autenticado.
        message: Mensagem do usuario.
        history: Lista de dicts {'role': 'user'|'assistant', 'content': str}.

    Returns:
        Resposta do agente como string.
    """
    try:
        llm = _get_llm()
        tools = build_tools_for_user(user)
        llm_with_tools = llm.bind_tools(tools)

        # Montar mensagens com historico
        messages = [SystemMessage(content=_build_system_message(user))]
        if history:
            for msg in history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                else:
                    messages.append(AIMessage(content=msg['content']))
        messages.append(HumanMessage(content=message))

        # Loop de agente: invocar LLM -> executar tools -> invocar LLM novamente
        max_iterations = 8
        for _ in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return response.content or 'Nao consegui gerar uma resposta.'

            # Executar cada tool chamada
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']

                # Encontrar e executar a tool correspondente
                tool_fn = None
                for t in tools:
                    if t.name == tool_name:
                        tool_fn = t
                        break

                if tool_fn:
                    try:
                        result = tool_fn.invoke(tool_args)
                    except Exception as e:
                        logger.exception(f'Erro ao executar tool {tool_name}')
                        result = f'Erro ao executar {tool_name}: {str(e)}'
                else:
                    result = f'Tool {tool_name} nao encontrada.'

                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id'],
                ))

        return 'Limite de iteracoes atingido. Tente reformular sua pergunta.'

    except Exception as e:
        logger.exception('Erro no agente de IA')
        return 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente em instantes.'


def generate_insight_for_user(user) -> str:
    """Gera insight para o dashboard do usuario.

    Coleta metricas e envia ao LLM para gerar resumo executivo.
    """
    try:
        tools = build_tools_for_user(user)
        # Encontrar tools por nome
        tool_map = {t.name: t for t in tools}

        metrics = tool_map['get_summary_metrics'].invoke({})
        renewals = tool_map['search_renewals'].invoke({'status': 'pending'})
        claims = tool_map['search_claims'].invoke({'status': 'open'})

        data = f'{metrics}\n\n## Renovações Pendentes\n{renewals}\n\n## Sinistros Abertos\n{claims}'

        role_display = ROLE_DISPLAY.get(user.role, user.get_role_display())
        prompt = INSIGHT_PROMPT.format(
            role=role_display,
            user_name=user.get_full_name(),
            data=data,
        )

        llm = _get_llm()
        response = llm.invoke([
            SystemMessage(content='Voce e um analista de dados de corretora de seguros.'),
            HumanMessage(content=prompt),
        ])
        return response.content

    except Exception as e:
        logger.exception('Erro ao gerar insight')
        return ''


def generate_entity_summary(user, entity_type: str, entity_id: int) -> str:
    """Gera resumo de uma entidade especifica.

    Args:
        user: Usuario autenticado.
        entity_type: Tipo da entidade (client, deal, policy, proposal, claim).
        entity_id: ID da entidade.

    Returns:
        Resumo gerado pelo LLM.
    """
    try:
        data = _collect_entity_data(user, entity_type, entity_id)
        if not data:
            return 'Registro nao encontrado ou sem permissao de acesso.'

        prompt_template = SUMMARY_PROMPTS.get(entity_type)
        if not prompt_template:
            return 'Tipo de entidade nao suportado.'

        prompt = prompt_template.format(**data)
        llm = _get_llm()
        response = llm.invoke([
            SystemMessage(content='Voce e um analista de dados de corretora de seguros. Gere resumos concisos e acionaveis em portugues brasileiro.'),
            HumanMessage(content=prompt),
        ])
        return response.content

    except Exception as e:
        logger.exception(f'Erro ao gerar resumo de {entity_type}')
        return 'Erro ao gerar resumo. Tente novamente.'


def _collect_entity_data(user, entity_type: str, entity_id: int) -> dict | None:
    """Coleta dados da entidade com dados relacionados."""
    from .permissions import get_filtered_queryset

    if entity_type == 'client':
        from clients.models import Client
        from policies.models import Policy
        from claims.models import Claim
        from crm.models import Deal

        qs = get_filtered_queryset(user, Client)
        client = qs.filter(pk=entity_id).first()
        if not client:
            return None

        policies = Policy.objects.filter(client=client)
        if user.role == 'broker':
            policies = policies.filter(broker=user)
        policies_detail = '\n'.join([
            f'  - {p.policy_number} | {p.insurer.name} | {p.insurance_type.name} | '
            f'{p.get_status_display()} | Vigencia: {p.start_date} a {p.end_date} | '
            f'Premio: R$ {p.premium_amount}'
            for p in policies.select_related('insurer', 'insurance_type')[:10]
        ]) or '  Nenhuma'

        claims = Claim.objects.filter(client=client)
        if user.role == 'broker':
            claims = claims.filter(broker=user)
        claims_detail = '\n'.join([
            f'  - {c.claim_number} | {c.get_status_display()} | '
            f'Reclamado: R$ {c.claimed_amount} | Data: {c.occurrence_date}'
            for c in claims[:10]
        ]) or '  Nenhum'

        deals = Deal.objects.filter(client=client)
        if user.role == 'broker':
            deals = deals.filter(broker=user)
        deals_detail = '\n'.join([
            f'  - {d.title} | {d.stage.name} | Valor: R$ {d.expected_value}'
            for d in deals.select_related('stage')[:10]
        ]) or '  Nenhum'

        return {
            'name': client.name,
            'client_type': client.get_client_type_display(),
            'cpf_cnpj': client.cpf_cnpj,
            'email': client.email,
            'phone': client.phone,
            'broker': client.broker.get_full_name(),
            'is_active': 'Sim' if client.is_active else 'Nao',
            'created_at': client.created_at.strftime('%d/%m/%Y'),
            'policies_count': policies.count(),
            'policies_detail': policies_detail,
            'claims_count': claims.count(),
            'claims_detail': claims_detail,
            'deals_count': deals.count(),
            'deals_detail': deals_detail,
        }

    elif entity_type == 'deal':
        from crm.models import Deal
        qs = get_filtered_queryset(user, Deal)
        deal = qs.select_related(
            'client', 'pipeline', 'stage', 'broker', 'insurer', 'insurance_type'
        ).filter(pk=entity_id).first()
        if not deal:
            return None

        activities = deal.activities.select_related('performed_by').order_by('-created_at')[:10]
        activities_detail = '\n'.join([
            f'  - [{a.get_activity_type_display()}] {a.title} | '
            f'{a.performed_by.get_full_name()} | {a.created_at.strftime("%d/%m/%Y")}'
            + (f' | {a.description[:100]}' if a.description else '')
            for a in activities
        ]) or '  Nenhuma'

        return {
            'title': deal.title,
            'client': deal.client.name,
            'pipeline': deal.pipeline.name,
            'stage': deal.stage.name,
            'priority': deal.get_priority_display(),
            'source': deal.get_source_display(),
            'expected_value': f'R$ {deal.expected_value}',
            'expected_close_date': deal.expected_close_date.strftime('%d/%m/%Y') if deal.expected_close_date else '-',
            'broker': deal.broker.get_full_name(),
            'insurer': deal.insurer.name if deal.insurer else '-',
            'insurance_type': deal.insurance_type.name if deal.insurance_type else '-',
            'created_at': deal.created_at.strftime('%d/%m/%Y'),
            'notes': deal.notes or '-',
            'activities_count': activities.count(),
            'activities_detail': activities_detail,
        }

    elif entity_type == 'policy':
        from policies.models import Policy
        from claims.models import Claim

        qs = get_filtered_queryset(user, Policy)
        policy = qs.select_related(
            'client', 'insurer', 'insurance_type', 'broker'
        ).filter(pk=entity_id).first()
        if not policy:
            return None

        coverages = policy.coverages.select_related('coverage')
        coverages_detail = '\n'.join([
            f'  - {pc.coverage.name} | Segurado: R$ {pc.insured_amount} | '
            f'Franquia: R$ {pc.deductible} | Premio: R$ {pc.premium_amount}'
            for pc in coverages
        ]) or '  Nenhuma'

        claims = Claim.objects.filter(policy=policy)
        if user.role == 'broker':
            claims = claims.filter(broker=user)
        claims_detail = '\n'.join([
            f'  - {c.claim_number} | {c.get_status_display()} | '
            f'Reclamado: R$ {c.claimed_amount}'
            for c in claims[:10]
        ]) or '  Nenhum'

        return {
            'policy_number': policy.policy_number,
            'client': policy.client.name,
            'insurer': policy.insurer.name,
            'insurance_type': policy.insurance_type.name,
            'status': policy.get_status_display(),
            'start_date': policy.start_date.strftime('%d/%m/%Y'),
            'end_date': policy.end_date.strftime('%d/%m/%Y'),
            'premium_amount': f'R$ {policy.premium_amount}',
            'insured_amount': f'R$ {policy.insured_amount}',
            'commission_rate': str(policy.commission_rate),
            'commission_amount': f'R$ {policy.commission_amount}',
            'installments': str(policy.installments),
            'payment_method': policy.get_payment_method_display(),
            'broker': policy.broker.get_full_name(),
            'coverages_count': coverages.count(),
            'coverages_detail': coverages_detail,
            'claims_count': claims.count(),
            'claims_detail': claims_detail,
        }

    elif entity_type == 'proposal':
        from policies.models import Proposal

        qs = get_filtered_queryset(user, Proposal)
        prop = qs.select_related(
            'client', 'insurer', 'insurance_type', 'broker'
        ).filter(pk=entity_id).first()
        if not prop:
            return None

        return {
            'proposal_number': prop.proposal_number,
            'client': prop.client.name,
            'insurer': prop.insurer.name,
            'insurance_type': prop.insurance_type.name,
            'status': prop.get_status_display(),
            'premium_amount': f'R$ {prop.premium_amount}',
            'submission_date': prop.submission_date.strftime('%d/%m/%Y') if prop.submission_date else '-',
            'response_date': prop.response_date.strftime('%d/%m/%Y') if prop.response_date else '-',
            'broker': prop.broker.get_full_name(),
            'notes': prop.notes or '-',
            'rejection_reason': prop.rejection_reason or '-',
        }

    elif entity_type == 'claim':
        from claims.models import Claim

        qs = get_filtered_queryset(user, Claim)
        claim = qs.select_related(
            'client', 'policy', 'broker'
        ).filter(pk=entity_id).first()
        if not claim:
            return None

        return {
            'claim_number': claim.claim_number,
            'client': claim.client.name,
            'policy': claim.policy.policy_number,
            'status': claim.get_status_display(),
            'occurrence_date': claim.occurrence_date.strftime('%d/%m/%Y'),
            'notification_date': claim.notification_date.strftime('%d/%m/%Y'),
            'location': claim.location or '-',
            'description': claim.description[:500] if claim.description else '-',
            'claimed_amount': f'R$ {claim.claimed_amount}',
            'approved_amount': f'R$ {claim.approved_amount}' if claim.approved_amount else '-',
            'resolution_date': claim.resolution_date.strftime('%d/%m/%Y') if claim.resolution_date else '-',
            'resolution_notes': claim.resolution_notes[:300] if claim.resolution_notes else '-',
            'broker': claim.broker.get_full_name(),
        }

    return None
