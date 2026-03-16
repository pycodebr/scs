# PRD — SCS (Sistema de Corretora de Seguros)

**Versão:** 1.1  
**Data:** 15/03/2026  
**Status:** Draft revisado para SaaS  
**Stack atual:** Python · Django 6.0 · SQLite · HTML/CSS/JS  
**Arquitetura alvo:** SaaS multi-tenant em banco compartilhado com isolamento por corretora

---

## 1. Visão Geral do Produto

### 1.1 Objetivo

O SCS é um sistema web de gestão completa para corretoras de seguros, cobrindo CRM, clientes, seguradoras, propostas, apólices, sinistros, endossos, renovações, relatórios, dashboard e IA aplicada à operação.

Nesta revisão, o produto passa a ser oficialmente definido como **SaaS multi-tenant**, permitindo que múltiplas corretoras utilizem a mesma aplicação, cada uma acessando exclusivamente seus próprios dados. Além da área autenticada, o produto deve contar com:

- landing page pública com posicionamento comercial, copy de vendas e destaque para IA integrada
- catálogo de planos com cobrança por usuário
- jornada de criação de conta self-service
- cadastro da corretora durante o onboarding
- plano free com ativação imediata, sem cartão
- administração sistêmica de corretoras, planos, pagamentos, módulos e ativações

### 1.2 Público-Alvo

- Donos e administradores de corretoras de seguros
- Gerentes e supervisores de corretora
- Corretores operacionais
- Administradores internos da plataforma SCS

### 1.3 Problema que Resolve

Corretoras de seguros frequentemente operam com processos fragmentados, planilhas, e-mails e controles desconectados, gerando perda de informação, atraso em renovações, baixa previsibilidade comercial e pouca inteligência operacional.

Além disso, no contexto SaaS, há um segundo problema de negócio: aquisição, onboarding e ativação de novas corretoras. O SCS precisa resolver tanto a operação interna da corretora quanto a jornada comercial de adesão ao produto.

### 1.4 Posicionamento do Produto

O SCS deve ser apresentado como uma plataforma de gestão inteligente para corretoras, com três pilares claros:

- operação centralizada de ponta a ponta
- inteligência comercial e gerencial
- IA integrada para acelerar análise, decisão e produtividade

---

## 2. Princípios Técnicos e Convenções

### 2.1 Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13+ |
| Framework | Django 6.0 |
| Banco atual | SQLite |
| Banco recomendado para produção SaaS | PostgreSQL |
| Frontend | Django Templates + HTML/CSS/JS |
| Design System | `design_system/design-system.html` |
| Auth | Django nativo com `accounts.User` customizado |
| Ambiente | `.venv` |

### 2.2 Convenções de Código

- Idioma do código: inglês
- Idioma da UI: português brasileiro
- Aspas simples sempre que possível
- Estilo: PEP 8
- Views: CBV por padrão
- Signals: em `signals.py` da app
- Models: todo model concreto com `created_at` e `updated_at`
- Cada domínio relevante deve continuar isolado em sua própria app

### 2.3 Restrições e Decisões

- Sem Docker
- Sem APIs REST nesta fase
- Sistema server-rendered com Django Templates
- Estratégia de multi-tenant: **shared schema / shared database**, com registros marcados por corretora
- `SQLite` pode continuar no desenvolvimento local e transição inicial de modelagem
- Antes de colocar o SaaS em produção, a meta técnica deve ser PostgreSQL

### 2.4 Base Models

Todos os models do projeto devem partir de um modelo com timestamps. Para a nova arquitetura SaaS, os models do domínio da corretora também devem partir de um modelo abstrato com vínculo obrigatório à corretora.

```python
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BrokerageScopedModel(TimeStampedModel):
    brokerage = models.ForeignKey(
        'brokerages.Brokerage',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_set',
    )

    class Meta:
        abstract = True
```

### 2.5 Regras de Isolamento de Dados

- Toda entidade operacional da corretora deve possuir `brokerage_id`
- Toda queryset autenticada deve filtrar por `request.user.brokerage`
- O filtro por corretor continua existindo, mas passa a ser secundário ao filtro por corretora
- Apenas `is_platform_admin=True` ou `is_superuser=True` podem atravessar o isolamento de tenant
- Qualquer exportação CSV/PDF, busca global, dashboard, relatórios, IA e comandos de gestão devem respeitar o escopo da corretora

---

## 3. Arquitetura do Projeto

### 3.1 Estrutura de Apps Django

```text
scs/
├── core/                      # settings, urls, wsgi, asgi
├── utils/                     # base models, validators, mixins, helpers
├── public_pages/              # landing page, planos, signup, onboarding público
├── brokerages/                # corretoras, módulos, contexto de tenant
├── billing/                   # planos, assinaturas, pagamentos
├── accounts/                  # autenticação, usuários, perfil, permissões
├── clients/                   # clientes
├── insurers/                  # seguradoras
├── coverages/                 # ramos, coberturas, itens
├── policies/                  # propostas, apólices, documentos, coberturas
├── claims/                    # sinistros
├── endorsements/              # endossos
├── renewals/                  # renovações
├── crm/                       # negociações, pipeline, kanban
├── dashboard/                 # dashboard operacional
├── reports/                   # relatórios
├── ai_agent/                  # chat e resumos com IA
├── templates/
├── static/
├── media/
├── manage.py
└── requirements.txt
```

### 3.2 Áreas da Aplicação

| Área | Público | Objetivo |
|---|---|---|
| Área pública | Visitantes | Landing page, planos, CTA, criação de conta |
| Área autenticada da corretora | Usuários da corretora | Operação diária da corretora |
| Área administrativa da plataforma | Admin do sistema | Gestão de corretoras, planos, pagamentos, módulos e ativações |

### 3.3 Mapa de Dependências

```text
utils ← base compartilhada
public_pages ← brokerages, billing, accounts
brokerages ← accounts
billing ← brokerages
accounts ← brokerages
clients ← accounts, brokerages
insurers ← brokerages
coverages ← brokerages
policies ← clients, insurers, coverages, accounts, brokerages
claims ← policies, clients, accounts, brokerages
endorsements ← policies, accounts, brokerages
renewals ← policies, insurers, accounts, brokerages
crm ← clients, policies, coverages, insurers, accounts, brokerages
dashboard ← policies, clients, claims, renewals, crm, ai_agent, brokerages
reports ← policies, clients, claims, renewals, crm, brokerages
ai_agent ← accounts, brokerages, policies, clients, claims, crm
```

### 3.4 Estratégia de Multi-Tenant

O modelo adotado deve ser o mais simples possível:

- um único banco
- um único schema
- um `brokerage_id` em todos os registros de negócio
- filtros, permissões e queries garantindo isolamento por corretora

Não haverá banco por tenant nem schema por tenant nesta fase.

### 3.5 Contexto Atual do Código

O código atual é essencialmente single-tenant, com isolamento parcial apenas por `broker` em vários módulos. A Fase 7 deve elevar esse padrão para isolamento real por corretora.

Principais sintomas atuais:

- `User` ainda não possui vínculo obrigatório com corretora
- várias querysets filtram apenas por `broker`
- `DashboardView` agrega dados sem contexto de tenant
- busca global percorre múltiplas apps sem filtro por corretora
- não existem apps públicas de marketing, planos, billing ou administração sistêmica

---

## 4. Módulos e Funcionalidades

### 4.1 BROKERAGES — Núcleo SaaS e Cadastro de Corretoras

**App:** `brokerages`

#### 4.1.1 Model: `Brokerage`

| Campo | Tipo | Regra |
|---|---|---|
| legal_name | CharField(255) | Obrigatório |
| trade_name | CharField(255) | Opcional |
| cnpj | CharField(18) | Obrigatório, único |
| email | EmailField | Opcional |
| phone | CharField(20) | Opcional |
| zip_code | CharField(10) | Opcional |
| street | CharField(255) | Opcional |
| number | CharField(20) | Opcional |
| complement | CharField(100) | Opcional |
| neighborhood | CharField(100) | Opcional |
| city | CharField(100) | Opcional |
| state | CharField(2) | Opcional |
| status | CharField(choices) | `active`, `inactive`, `overdue` |
| notes | TextField | Opcional |
| created_at | DateTimeField | Obrigatório |
| updated_at | DateTimeField | Obrigatório |

#### 4.1.2 Regras

- `cnpj` e `legal_name` são obrigatórios no onboarding
- somente o admin da plataforma pode criar, editar, ativar, inativar ou marcar pagamento em atraso
- a corretora criada no onboarding nasce vinculada ao primeiro usuário administrador daquela conta
- `status=inactive` bloqueia login operacional
- `status=overdue` mantém acesso configurável, mas com alertas e limitação definida pela plataforma

#### 4.1.3 Model: `SystemModule`

Representa módulos comercializáveis ou liberáveis por corretora.

Exemplos:

- `dashboard`
- `reports`
- `crm`
- `ai_agent`
- `claims`
- `endorsements`
- `renewals`

#### 4.1.4 Model: `BrokerageModule`

Tabela de ativação por corretora.

Campos mínimos:

- `brokerage`
- `module`
- `is_enabled`
- `granted_by`
- `created_at`
- `updated_at`

#### 4.1.5 Funcionalidades

- CRUD de corretoras via Django Admin
- ativação e bloqueio da corretora
- gestão de módulos liberados
- visão consolidada de usuários ativos, assinatura atual e pagamentos

---

### 4.2 BILLING — Planos, Assinaturas e Pagamentos

**App:** `billing`

#### 4.2.1 Model: `Plan`

| Campo | Tipo | Regra |
|---|---|---|
| name | CharField(100) | Obrigatório |
| slug | SlugField | Único |
| description | TextField | Opcional |
| is_free | BooleanField | Define plano gratuito |
| monthly_price_per_user | DecimalField | Preço por usuário/mês |
| yearly_price_per_user | DecimalField | Opcional |
| trial_days | PositiveIntegerField | Opcional |
| max_users | PositiveIntegerField | Opcional |
| is_active | BooleanField | Controle comercial |
| highlight_label | CharField(50) | Ex.: Mais popular |
| sort_order | PositiveIntegerField | Ordenação |

#### 4.2.2 Model: `PlanModule`

Relaciona quais módulos fazem parte de cada plano.

#### 4.2.3 Model: `Subscription`

| Campo | Tipo | Regra |
|---|---|---|
| brokerage | FK | Obrigatório |
| plan | FK | Obrigatório |
| status | CharField(choices) | `trial`, `active`, `pending_payment`, `overdue`, `cancelled`, `inactive` |
| billing_cycle | CharField(choices) | `monthly`, `yearly` |
| price_per_user | DecimalField | Snapshot do preço contratado |
| active_user_count | PositiveIntegerField | Total de usuários ativos da corretora |
| started_at | DateField | Obrigatório |
| trial_ends_at | DateField | Opcional |
| next_billing_at | DateField | Opcional |
| cancelled_at | DateField | Opcional |

#### 4.2.4 Model: `PaymentRecord`

| Campo | Tipo | Regra |
|---|---|---|
| subscription | FK | Obrigatório |
| status | CharField(choices) | `pending`, `paid`, `failed`, `refunded`, `overdue` |
| amount | DecimalField | Obrigatório |
| payment_method | CharField(choices) | `credit_card`, `pix`, `boleto`, `manual` |
| reference_code | CharField(100) | Opcional |
| due_date | DateField | Obrigatório |
| paid_at | DateTimeField | Opcional |
| notes | TextField | Opcional |

#### 4.2.5 Regras de Billing

- os preços são exibidos por usuário
- plano free pode ser ativado sem cartão
- plano pago gera assinatura e processo de cobrança
- pagamentos podem começar com registro manual ou checkout hospedado por gateway externo
- o admin da plataforma gerencia status da assinatura e pagamentos
- a corretora enxerga apenas seu próprio plano, histórico e situação atual

---

### 4.3 PUBLIC_PAGES — Landing Page, Planos e Onboarding

**App:** `public_pages`

#### 4.3.1 Landing Page Principal

A landing page deve conter:

- hero principal com proposta de valor
- seções de benefícios do produto
- destaque para IA integrada e gestão inteligente
- visão dos módulos principais
- prova de valor para corretoras
- cards de planos com preço por usuário
- comparativo entre plano free e planos pagos
- FAQ
- CTAs para criar conta e entrar

#### 4.3.2 Jornada de Cadastro

Fluxo mínimo:

1. visitante acessa `/`
2. clica em criar conta
3. informa dados do usuário administrador inicial
4. informa dados da corretora
5. escolhe o plano
6. se plano free, entra direto no sistema
7. se plano pago, segue para etapa de assinatura/cobrança

#### 4.3.3 Dados obrigatórios no onboarding

- nome do usuário responsável
- e-mail
- senha
- CNPJ da corretora
- razão social da corretora
- plano escolhido

#### 4.3.4 Dados opcionais da corretora

- nome fantasia
- telefone
- endereço
- contato financeiro
- observações

#### 4.3.5 Views públicas previstas

| View | Tipo | URL |
|---|---|---|
| LandingPageView | TemplateView | `/` |
| PricingView | TemplateView | `/planos/` |
| SignupView | FormView | `/criar-conta/` |
| SignupSuccessView | TemplateView | `/criar-conta/sucesso/` |
| PublicLoginRedirectView | RedirectView | `/entrar/` |

---

### 4.4 ACCOUNTS — Usuários, Autenticação e Papéis

**App:** `accounts`

#### 4.4.1 Model: `User`

O model atual deve ser estendido para suportar SaaS multi-tenant.

Campos adicionais obrigatórios:

| Campo | Tipo | Regra |
|---|---|---|
| brokerage | FK -> `brokerages.Brokerage` | Obrigatório para usuários da corretora |
| is_platform_admin | BooleanField | Apenas admin interno do SaaS |

Campos já existentes mantidos:

- `email`
- `first_name`
- `last_name`
- `cpf`
- `phone`
- `role`
- `is_active`
- `is_staff`
- `date_joined`
- `avatar`
- `created_at`
- `updated_at`

#### 4.4.2 Papéis

Papéis de tenant:

- `admin` = administrador da corretora
- `manager` = gerente
- `broker` = corretor operacional

Papéis de plataforma:

- `is_platform_admin=True` = administrador do SaaS

#### 4.4.3 Permissões

| Capacidade | Platform Admin | Admin | Manager | Broker |
|---|---|---|---|---|
| Administrar corretoras | ✅ | ❌ | ❌ | ❌ |
| Administrar planos e pagamentos | ✅ | ❌ | ❌ | ❌ |
| Gerenciar módulos da corretora | ✅ | ❌ | ❌ | ❌ |
| Gerenciar usuários da própria corretora | ❌ | ✅ | ✅ | ❌ |
| Ver todos os dados da própria corretora | ❌ | ✅ | ✅ | ❌ |
| Ver apenas próprios dados operacionais | ❌ | ✅ | ✅ | ✅ |
| Acessar relatórios da corretora | ❌ | ✅ | ✅ | ❌ |
| Acessar CRM completo da corretora | ❌ | ✅ | ✅ | ❌ |
| Operar CRM próprio | ❌ | ✅ | ✅ | ✅ |

#### 4.4.4 Funcionalidades

- login por e-mail e senha
- logout
- criação do primeiro usuário via onboarding público
- gestão dos demais usuários por admin/manager da própria corretora
- edição de perfil
- alteração de senha
- ativação e desativação de usuários
- listagem limitada à corretora do usuário autenticado

---

### 4.5 CLIENTS, INSURERS E COVERAGES — Adequação Multi-Tenant

**Apps:** `clients`, `insurers`, `coverages`

#### 4.5.1 Models impactados

| App | Models | Mudança obrigatória |
|---|---|---|
| `clients` | `Client` | adicionar `brokerage` |
| `insurers` | `Insurer`, `InsurerBranch` | adicionar `brokerage` |
| `coverages` | `InsuranceType`, `Coverage`, `CoverageItem` | adicionar `brokerage` |

#### 4.5.2 Regras

- `Client.cpf_cnpj` deixa de ser único global e passa a ser único por corretora
- `Insurer.cnpj` deixa de ser único global e passa a ser único por corretora
- `InsuranceType.slug` e nomes sensíveis devem ser únicos por corretora, não globais
- formulários devem exibir apenas FKs da mesma corretora
- filtros por corretor devem acontecer somente dentro da corretora

---

### 4.6 POLICIES, CLAIMS, ENDORSEMENTS E RENEWALS — Adequação Multi-Tenant

**Apps:** `policies`, `claims`, `endorsements`, `renewals`

#### 4.6.1 Models impactados

| App | Models | Mudança obrigatória |
|---|---|---|
| `policies` | `Proposal`, `Policy`, `PolicyCoverage`, `PolicyDocument` | adicionar `brokerage` |
| `claims` | `Claim`, `ClaimDocument`, `ClaimTimeline` | adicionar `brokerage` |
| `endorsements` | `Endorsement`, `EndorsementDocument` | adicionar `brokerage` |
| `renewals` | `Renewal` | adicionar `brokerage` |

#### 4.6.2 Regras

- números de proposta, apólice e sinistro devem ser únicos por corretora
- toda criação deve herdar `brokerage` do usuário autenticado
- uploads de documentos continuam no storage atual, mas os registros devem ser tenant-scoped
- relatórios, exportações e telas de detalhe precisam validar a corretora antes de carregar o objeto

---

### 4.7 CRM — Pipeline e Negociações por Corretora

**App:** `crm`

#### 4.7.1 Models impactados

- `Pipeline`
- `PipelineStage`
- `Deal`
- `DealActivity`

#### 4.7.2 Regras

- cada corretora possui seus próprios pipelines
- `Pipeline.is_default` deve ser único por corretora
- o kanban deve carregar apenas deals e estágios da corretora atual
- o broker visualiza apenas seus negócios; admin/manager visualizam a corretora inteira

---

### 4.8 DASHBOARD, REPORTS E IA — Contexto Obrigatório de Tenant

**Apps:** `dashboard`, `reports`, `ai_agent`

#### 4.8.1 Dashboard

- todos os KPIs e gráficos devem partir de querysets filtradas por corretora
- o filtro por corretor continua para brokers
- atalhos e cards devem respeitar módulos ativos da corretora

#### 4.8.2 Reports

- todos os relatórios CSV/PDF devem ser filtrados por corretora antes dos demais filtros
- managers e admins enxergam a corretora inteira
- brokers continuam sem acesso aos relatórios gerenciais

#### 4.8.3 IA

Models impactados:

- `ChatSession`
- `ChatMessage`
- `EntitySummary`
- `DashboardInsight`

Regras:

- toda sessão, resumo e insight deve carregar `brokerage`
- prompts e tools devem operar apenas em dados da corretora atual
- a IA nunca deve cruzar dados entre corretoras

---

### 4.9 DJANGO ADMIN — Administração Sistêmica do SaaS

#### 4.9.1 Funcionalidades

- dashboard do SaaS com visão consolidada
- listagem e detalhe de corretoras
- ativação, inativação e marcação de pagamento em atraso
- gestão de planos
- gestão de assinaturas
- gestão de pagamentos
- gestão de módulos por corretora
- visão de uso por corretora: usuários, módulos ativos, plano, status

#### 4.9.2 Diretriz de Implementação

- o admin do sistema deve usar o próprio Django Admin em `/admin/`
- `Brokerage`, `SystemModule`, `BrokerageModule`, `Plan`, `PlanModule`, `Subscription` e `PaymentRecord` devem ser registrados no Django Admin
- a configuração do admin deve incluir `list_display`, `list_filter`, `search_fields`, `autocomplete_fields` e actions para operação eficiente
- status da corretora, assinatura e pagamento devem poder ser administrados diretamente no Django Admin
- o Django Admin é a interface oficial do backoffice SaaS nesta fase

---

## 5. Design System e UI

### 5.1 Fonte de Verdade Visual

O arquivo `design_system/design-system.html` continua sendo a referência visual obrigatória.

As novas telas devem reutilizar especialmente os padrões já demonstrados nas seções:

- **Application Shell**
- **Colors, Surfaces & Semantic States**
- **Form Components**
- **Tables & Data Display**
- **UI Components**
- **Layout & Spacing**

### 5.2 Shells da Aplicação

O produto passa a ter três shells visuais:

| Shell | Uso |
|---|---|
| Public Shell | landing, planos, cadastro |
| Tenant Shell | dashboard e módulos da corretora |
| Django Admin | administração do SaaS |

### 5.3 Diretrizes para a Landing Page

- hero com CTA primário e secundário
- cards de benefícios usando o padrão de cards do design system
- badges semânticos para status de planos e recursos
- seção de pricing em cards comparativos
- FAQ em accordion
- blocos com ênfase visual em IA, automação, insights e produtividade

### 5.4 Hierarquia de Templates

```text
templates/
├── public/
│   ├── base_public.html
│   ├── landing.html
│   ├── pricing.html
│   ├── signup.html
│   └── signup_success.html
├── accounts/
├── clients/
├── insurers/
├── coverages/
├── policies/
├── claims/
├── endorsements/
├── renewals/
├── crm/
├── reports/
└── dashboard/
```

### 5.5 Navegação

A navegação lateral da área autenticada deve passar a ser dinâmica:

- mostrar apenas módulos liberados para a corretora
- esconder relatórios, IA ou CRM se o plano não incluir esses módulos
- manter a seção de usuários apenas para `admin` e `manager`
- incluir acesso a assinatura e plano da corretora para `admin`

---

## 6. Integrações e Libs Externas

| Recurso | Propósito |
|---|---|
| Django | Framework principal |
| Pillow | Upload de avatares e logos |
| xhtml2pdf / ReportLab | Exportação de relatórios |
| ViaCEP | Consulta de endereço |
| django-widget-tweaks | Ajustes de widgets |
| Gateway de pagamento hospedado | Cobrança dos planos pagos |

Observação: o gateway pode começar como integração futura plugável, mas o domínio de billing e os fluxos de assinatura devem nascer prontos para isso.

---

## 7. Segurança e Permissões

### 7.1 Autenticação

- login obrigatório para toda área autenticada
- área pública acessível sem login
- usuários inativos não acessam
- corretoras inativas não acessam
- corretoras em atraso seguem política definida pela plataforma

### 7.2 Autorização

Os mixins atuais precisam evoluir para uma camada explícita de tenant.

```python
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class PlatformAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_platform_admin or self.request.user.is_superuser


class BrokerageRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.brokerage_id:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class BrokerageFilterMixin(BrokerageRequiredMixin):
    brokerage_field = 'brokerage'

    def get_queryset(self):
        qs = super().get_queryset().filter(**{
            self.brokerage_field: self.request.user.brokerage
        })
        if getattr(self.request.user, 'role', None) == 'broker':
            qs = qs.filter(broker=self.request.user)
        return qs
```

### 7.3 Regras Obrigatórias

- nenhum `get_object()` pode carregar objeto sem validar `brokerage`
- nenhum formulário pode listar FKs de outra corretora
- nenhuma exportação pode atravessar tenant
- buscas globais devem filtrar primeiro por corretora
- dashboards e IA devem respeitar módulos ativos e escopo do tenant

### 7.4 Validações

- CPF/CNPJ com validação de formato e dígitos
- monetário sempre com `DecimalField`
- `ModelForm.fields` explícitos
- constraints compostas por corretora quando houver unicidade de negócio

---

## 8. Plano de Desenvolvimento (Fases)

### Fase 1 — Fundação (Semana 1-2)

- [x] Setup do projeto Django
- [x] Configuração de settings
- [x] App `utils`
- [x] App `accounts`
- [x] Layout base e login

### Fase 2 — Cadastros Base (Semana 3-4)

- [x] App `clients`
- [x] App `insurers`
- [x] App `coverages`

### Fase 3 — Core do Negócio (Semana 5-7)

- [x] App `policies`
- [x] Conversão de proposta em apólice
- [x] App `claims`
- [x] App `endorsements`

### Fase 4 — Operações Avançadas (Semana 8-9)

- [x] App `renewals`
- [x] App `crm`
- [x] Kanban com drag-and-drop

### Fase 5 — Inteligência e Relatórios (Semana 10-11)

- [x] App `dashboard`
- [x] App `reports`

### Fase 6 — Polish e Refinamento (Semana 12)

- [x] Revisão geral de UI/UX
- [x] Responsividade
- [x] Seed demo
- [x] Validações finais das permissões atuais

### Fase 7 — SaaS Multi-Tenant, Landing Page e Billing

- [ ] Criar apps `public_pages`, `brokerages` e `billing`
- [ ] Adicionar modelagem de corretora, módulos, planos, assinaturas e pagamentos
- [ ] Adaptar `accounts.User` para vínculo com corretora e papel de admin da plataforma
- [ ] Migrar todas as apps operacionais para `brokerage_id`
- [ ] Trocar o isolamento atual por corretor para isolamento primário por corretora
- [ ] Implementar landing page, pricing e signup público
- [ ] Implementar criação de conta com cadastro da corretora e escolha de plano
- [ ] Ativar plano free sem cartão
- [ ] Implementar administração sistêmica de corretoras, planos, pagamentos e módulos no Django Admin
- [ ] Atualizar navegação e templates para módulos por plano/corretora
- [ ] Revisar dashboard, relatórios, IA, exportações e busca global para escopo multi-tenant

### Plano de Ação — Fase 7

#### 8.1 Modelagem e Banco

- criar `brokerages.Brokerage`
- criar `brokerages.SystemModule`
- criar `brokerages.BrokerageModule`
- criar `billing.Plan`
- criar `billing.PlanModule`
- criar `billing.Subscription`
- criar `billing.PaymentRecord`
- adicionar `brokerage` e `is_platform_admin` em `accounts.User`
- adicionar `brokerage` em todos os models operacionais
- trocar unicidades globais por unicidades compostas com `brokerage`

#### 8.2 Apps Novas

- `public_pages`: landing, planos, cadastro e ativação
- `brokerages`: corretoras, módulos, contexto do tenant
- `billing`: planos, assinaturas, pagamentos

#### 8.3 Apps Existentes a Alterar

- `accounts`: onboarding, papéis, filtro por corretora, gestão de usuários da própria corretora
- `clients`: `brokerage`, filtros, exportação, `broker` limitado à corretora
- `insurers`: `brokerage`, unicidade por corretora
- `coverages`: catálogo por corretora
- `policies`: `brokerage` em propostas, apólices, coberturas e documentos
- `claims`: `brokerage` em sinistros, documentos e timeline
- `endorsements`: `brokerage` em endossos e documentos
- `renewals`: `brokerage` e filtros completos por tenant
- `crm`: pipelines, etapas, negociações e atividades por corretora
- `dashboard`: KPIs e gráficos filtrados por corretora
- `reports`: CSV/PDF filtrados por corretora
- `ai_agent`: sessões, mensagens e insights com escopo de corretora
- `utils`: novos mixins, helpers e validators de tenant
- `core`: middleware, context processors, settings e urls
- `admin.py` das apps novas e existentes: registro e configuração do Django Admin para gestão sistêmica

#### 8.4 Permissões e Middleware

- criar `PlatformAdminRequiredMixin`
- criar `BrokerageRequiredMixin`
- substituir `BrokerFilterMixin` por mixin que filtra primeiro por corretora
- adicionar middleware ou helper central para contexto da corretora
- bloquear acesso quando corretora estiver inativa
- controlar disponibilidade por módulo habilitado

#### 8.5 UI e Templates

- criar `base_public.html`
- revisar `base.html`, `_sidebar.html` e `_topbar.html`
- incluir menu de assinatura/plano para admin da corretora
- esconder itens da sidebar por módulo ativo
- implementar landing page e pricing no padrão do design system
- não criar backoffice customizado para a plataforma nesta fase; usar Django Admin

#### 8.6 Billing e Operação SaaS

- exibir planos por preço por usuário
- calcular usuários ativos da corretora para cobrança
- permitir free plan sem cartão
- registrar pagamentos e refletir em `Subscription.status`
- permitir ao admin da plataforma ativar, bloquear ou marcar inadimplência

#### 8.7 Estratégia de Migração

- como o banco atual e as migrations refletem uma modelagem single-tenant, a estratégia recomendada para a Fase 7 é reinicializar a base estrutural se ainda não houver dados de produção
- opção recomendada: remover migrations antigas das apps de domínio, preservar apenas `__init__.py`, apagar `db.sqlite3`, gerar novas migrations com a modelagem multi-tenant e reaplicar seed
- se houver dados relevantes a preservar, criar scripts de migração assistida antes de resetar

#### 8.8 Critérios de Aceite

- uma corretora não consegue visualizar ou exportar dados de outra
- o plano free ativa acesso sem cartão
- a landing page converte para signup
- o admin da plataforma consegue administrar corretoras, planos, pagamentos e módulos
- relatórios, dashboard e IA retornam apenas dados da corretora atual

---

## 9. Configurações do Projeto

### 9.1 `settings.py` — Pontos Relevantes

```python
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
]

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'widget_tweaks',
    # local
    'utils',
    'public_pages',
    'brokerages',
    'billing',
    'accounts',
    'clients',
    'insurers',
    'coverages',
    'policies',
    'claims',
    'endorsements',
    'renewals',
    'crm',
    'dashboard',
    'reports',
    'ai_agent',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'brokerages.middleware.BrokerageContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 9.2 URLs Raiz

```python
urlpatterns = [
    path('', include('public_pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('insurers/', include('insurers.urls')),
    path('coverages/', include('coverages.urls')),
    path('policies/', include('policies.urls')),
    path('claims/', include('claims.urls')),
    path('endorsements/', include('endorsements.urls')),
    path('renewals/', include('renewals.urls')),
    path('crm/', include('crm.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('reports/', include('reports.urls')),
    path('ai/', include('ai_agent.urls')),
    path('admin/', admin.site.urls),
]
```

### 9.3 Dependências

```text
Django==6.0
Pillow>=10.0
django-widget-tweaks>=1.5
reportlab>=4.0
xhtml2pdf>=0.2
```

---

## 10. Glossário

| Termo | Definição |
|---|---|
| Tenant | Corretora cliente do SaaS |
| Corretora | Organização usuária do sistema |
| Plano | Oferta comercial do SaaS |
| Assinatura | Contratação ativa de um plano por uma corretora |
| Módulo | Parte funcional habilitável do produto |
| Admin da Plataforma | Usuário interno que administra o SaaS |
| Admin da Corretora | Usuário administrador dentro do tenant |
| Apólice | Contrato de seguro emitido |
| Proposta | Solicitação enviada à seguradora |
| Sinistro | Evento coberto com pedido de indenização |
| Endosso | Alteração contratual na apólice |
| Renovação | Nova emissão ao fim da vigência |

---

## 11. Observações Finais

- O estado atual do código é funcional para uma corretora por vez, mas ainda não atende SaaS multi-tenant real.
- A Fase 7 deve ser tratada como uma refatoração estrutural, não como ajuste cosmético.
- O caminho mais pragmático é shared database com `brokerage_id` obrigatório em todo o domínio.
- Para evitar conflito de migrations e inconsistência da modelagem antiga, é aceitável resetar migrations e `db.sqlite3` durante a transição, desde que ainda não existam dados de produção.
- Para produção SaaS, PostgreSQL é a meta técnica recomendada, mesmo que o projeto continue com SQLite no ciclo local e na refatoração inicial.
- O design system continua sendo a fonte de verdade visual, inclusive para landing page, pricing e área administrativa da plataforma.
