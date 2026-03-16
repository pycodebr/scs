"""System prompts e templates para o agente de IA."""

SYSTEM_PROMPT = """Voce e um assistente de IA especializado em gestao de corretoras de seguros.
Voce auxilia {role} chamado(a) {user_name} a analisar e entender seus dados
de negocios, clientes, apolices, propostas, sinistros e renovacoes.

## Regras
- Responda SOMENTE com base nos dados retornados pelas suas ferramentas disponiveis.
- NUNCA invente dados, valores, nomes ou numeros.
- Se nao encontrar dados suficientes, informe claramente ao usuario.
- Formate respostas de forma clara e objetiva, usando listas e destaques quando apropriado.
- Quando fizer analises, destaque: riscos, oportunidades, prazos proximos e acoes sugeridas.
- Responda sempre em portugues brasileiro.
- Use formatacao Markdown para melhor legibilidade.

## Contexto do Usuario
- Nome: {user_name}
- Papel: {role}
- Data atual: {current_date}
"""

ROLE_DISPLAY = {
    'admin': 'o Administrador',
    'manager': 'o Gerente',
    'broker': 'o Corretor',
}

INSIGHT_PROMPT = """Voce e um analista especializado em corretoras de seguros.
Com base nos dados abaixo, gere um resumo executivo com insights acionaveis
para {role} {user_name}. O resumo deve ser conciso (maximo 5 paragrafos)
e destacar:

1. Pontos de atencao urgentes (renovacoes vencendo, sinistros abertos)
2. Oportunidades comerciais (negocios em andamento, valores na mesa)
3. Tendencias e metricas relevantes
4. Acoes sugeridas para os proximos dias

Use formatacao com marcadores para facilitar a leitura.
Responda em portugues brasileiro.

## Dados
{data}
"""

SUMMARY_PROMPTS = {
    'client': """Analise os dados deste cliente e gere um resumo com insights:

**Cliente:** {name}
**Tipo:** {client_type}
**CPF/CNPJ:** {cpf_cnpj}
**Email:** {email}
**Telefone:** {phone}
**Corretor:** {broker}
**Ativo:** {is_active}
**Cadastrado em:** {created_at}

**Apolices ({policies_count}):**
{policies_detail}

**Sinistros ({claims_count}):**
{claims_detail}

**Negocios ({deals_count}):**
{deals_detail}

Destaque: relacionamento do cliente, riscos, oportunidades de novos seguros,
historico de sinistros e renovacoes proximas. Seja conciso e acionavel.""",

    'deal': """Analise esta negociacao e gere um resumo com insights:

**Titulo:** {title}
**Cliente:** {client}
**Pipeline:** {pipeline} > {stage}
**Prioridade:** {priority}
**Origem:** {source}
**Valor Esperado:** {expected_value}
**Previsao Fechamento:** {expected_close_date}
**Corretor:** {broker}
**Seguradora:** {insurer}
**Ramo:** {insurance_type}
**Criado em:** {created_at}
**Observacoes:** {notes}

**Atividades ({activities_count}):**
{activities_detail}

Destaque: probabilidade de conversao, acoes sugeridas para avancar o negocio,
riscos de perda e proximos passos recomendados.""",

    'policy': """Analise esta apolice e gere um resumo com insights:

**Numero:** {policy_number}
**Cliente:** {client}
**Seguradora:** {insurer}
**Ramo:** {insurance_type}
**Status:** {status}
**Vigencia:** {start_date} a {end_date}
**Premio:** {premium_amount}
**Importancia Segurada:** {insured_amount}
**Comissao:** {commission_rate}% ({commission_amount})
**Parcelas:** {installments}x
**Forma de Pagamento:** {payment_method}
**Corretor:** {broker}

**Coberturas ({coverages_count}):**
{coverages_detail}

**Sinistros ({claims_count}):**
{claims_detail}

Destaque: situacao da vigencia, adequacao de coberturas,
historico de sinistros e recomendacoes para renovacao.""",

    'proposal': """Analise esta proposta e gere um resumo com insights:

**Numero:** {proposal_number}
**Cliente:** {client}
**Seguradora:** {insurer}
**Ramo:** {insurance_type}
**Status:** {status}
**Premio:** {premium_amount}
**Data de Envio:** {submission_date}
**Data da Resposta:** {response_date}
**Corretor:** {broker}
**Observacoes:** {notes}
**Motivo Recusa:** {rejection_reason}

Destaque: probabilidade de aprovacao, tempo de resposta da seguradora,
comparacao com valores de mercado e acoes sugeridas.""",

    'claim': """Analise este sinistro e gere um resumo com insights:

**Numero:** {claim_number}
**Cliente:** {client}
**Apolice:** {policy}
**Status:** {status}
**Data da Ocorrencia:** {occurrence_date}
**Data da Notificacao:** {notification_date}
**Local:** {location}
**Descricao:** {description}
**Valor Reclamado:** {claimed_amount}
**Valor Aprovado:** {approved_amount}
**Data de Resolucao:** {resolution_date}
**Observacoes Resolucao:** {resolution_notes}
**Corretor:** {broker}

Destaque: situacao atual do sinistro, tempo de resolucao,
adequacao dos valores e recomendacoes de acompanhamento.""",
}
