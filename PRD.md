# PRD — SCS (Sistema de Corretora de Seguros)

**Versão:** 1.0
**Data:** 15/03/2026
**Status:** Draft
**Stack:** Python · Django 6.0 · SQLite · HTML/CSS/JS

---

## 1. Visão Geral do Produto

### 1.1 Objetivo

O SCS é um sistema web de gestão completa para corretoras de seguros, permitindo o controle de todo o ciclo de vida das operações — desde a prospecção de clientes até a gestão de sinistros e renovações. O sistema centraliza informações de clientes, seguradoras, apólices, propostas, sinistros, endossos, coberturas e negociações em um único ambiente com dashboard analítico e painel CRM integrado.

### 1.2 Público-Alvo

- Corretores de seguros (usuários operacionais)
- Gerentes/supervisores de corretora (visão estratégica)
- Administradores do sistema (gestão de acessos e configurações)

### 1.3 Problema que Resolve

Corretoras de seguros frequentemente operam com processos fragmentados — planilhas, e-mails, sistemas isolados — gerando perda de informações, atrasos em renovações, falta de visibilidade sobre sinistros e dificuldade no acompanhamento de negociações. O SCS unifica todos esses processos em uma plataforma coesa.

---

## 2. Princípios Técnicos e Convenções

### 2.1 Stack Tecnológica

| Camada        | Tecnologia                              |
|---------------|----------------------------------------|
| Linguagem     | Python 3.13+                           |
| Framework     | Django 6.0                             |
| Banco de Dados| SQLite (padrão Django)                 |
| Frontend      | Django Templates + HTML/CSS/JS         |
| Design System | `@design_system/design-system.html`    |
| Auth          | Sistema nativo do Django (customizado) |
| Virtual Env   | .venv                                  |

### 2.2 Convenções de Código

- **Idioma do código:** Inglês (models, views, urls, variáveis, funções)
- **Idioma da UI:** Português brasileiro (templates, labels, mensagens, verbose_name)
- **Aspas:** Simples (`'`) sempre que possível
- **Estilo:** PEP 8 rigoroso
- **Views:** Class-Based Views (CBV) como padrão; Function-Based Views apenas quando CBV for contraproducente
- **Signals:** Sempre em arquivo `signals.py` dentro da app correspondente
- **Models:** Todo model deve conter `created_at` e `updated_at`
- **Apps:** Cada domínio/entidade principal isolado em sua própria Django app

### 2.3 Restrições

- **Sem Docker** — desenvolvimento e deploy simplificado
- **Sem testes automatizados** — fora do escopo desta versão
- **Sem APIs REST** — sistema server-rendered com Django Templates
- **Banco único SQLite** — sem necessidade de PostgreSQL/MySQL

### 2.4 Base Model Padrão

Todos os models do projeto devem herdar de um abstract base model com timestamps:

```python
# core/models.py

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

---

## 3. Arquitetura do Projeto

### 3.1 Estrutura de Apps Django

```
scs/
├── core/                    # Projeto Django (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── utils/                  # App central: base models, mixins, utils, templatetags
├── accounts/               # App de autenticação e gestão de usuários
├── clients/                # App de cadastro e gestão de clientes
├── insurers/               # App de cadastro de seguradoras
├── policies/               # App de apólices e propostas de seguro
├── claims/                 # App de gestão de sinistros
├── endorsements/           # App de gestão de endossos
├── coverages/              # App de coberturas e itens de cobertura
├── renewals/               # App de gestão de renovações
├── crm/                    # App de CRM — pipeline de negociações (grid + kanban)
├── reports/                # App de relatórios
├── dashboard/              # App de dashboard e métricas
├── design_system/          # Design system de referência (design-system.html)
├── static/                 # Arquivos estáticos globais (CSS, JS, imagens)
├── templates/              # Templates globais (base.html, partials, includes)
├── media/                  # Uploads de arquivos
├── manage.py
└── requirements.txt
```

### 3.2 Mapa de Dependências entre Apps

```
accounts ← (independente, base de auth)
utils ← (independente, utilitários)
clients ← accounts
insurers ← (independente)
coverages ← insurers
policies ← clients, insurers, coverages, accounts
endorsements ← policies
claims ← policies, clients
renewals ← policies
crm ← clients, policies, accounts
reports ← policies, clients, insurers, claims, renewals
dashboard ← policies, clients, insurers, claims, renewals, crm
```

---

## 4. Módulos e Funcionalidades Detalhadas

---

### 4.1 ACCOUNTS — Autenticação e Gestão de Usuários

**App:** `accounts`

#### 4.1.1 Custom User Model

O sistema usa um model de usuário customizado com login por **email** (não username).

**Model: `User`**

| Campo            | Tipo                    | Descrição                               |
|------------------|------------------------|-----------------------------------------|
| email            | EmailField (unique)    | Email do usuário — usado como login     |
| first_name       | CharField(150)         | Nome                                    |
| last_name        | CharField(150)         | Sobrenome                               |
| cpf              | CharField(14), unique  | CPF do usuário (opcional para admin)    |
| phone            | CharField(20)          | Telefone                                |
| role             | CharField (choices)    | Papel: admin, manager, broker           |
| is_active        | BooleanField           | Usuário ativo                           |
| is_staff         | BooleanField           | Acesso ao admin                         |
| date_joined      | DateTimeField          | Data de cadastro                        |
| avatar           | ImageField (opcional)  | Foto do perfil                          |
| created_at       | DateTimeField          | Timestamp criação                       |
| updated_at       | DateTimeField          | Timestamp atualização                   |

**Choices de Role:**

```python
class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    MANAGER = 'manager', 'Gerente'
    BROKER = 'broker', 'Corretor'
```

**Custom Manager: `UserManager`**

- `create_user(email, password, **extra_fields)` — normaliza email, valida, cria user
- `create_superuser(email, password, **extra_fields)` — cria superuser com is_staff=True

**Custom Backend: `EmailBackend`**

- Autenticação via email + password ao invés de username + password

#### 4.1.2 Funcionalidades

- Login por email e senha
- Logout
- Registro de novos usuários (apenas por admin/manager)
- Edição de perfil (dados pessoais, avatar)
- Alteração de senha
- Listagem de usuários (admin/manager)
- Ativação/desativação de usuários
- Controle de permissões baseado em role (admin, manager, broker)

#### 4.1.3 Permissões por Role

| Funcionalidade              | Admin | Manager | Broker |
|-----------------------------|-------|---------|--------|
| CRUD de usuários            | ✅    | ✅      | ❌     |
| Ver todos os dados          | ✅    | ✅      | ❌     |
| Ver dados próprios          | ✅    | ✅      | ✅     |
| Gerenciar configurações     | ✅    | ❌      | ❌     |
| CRUD de clientes            | ✅    | ✅      | ✅     |
| CRUD de apólices            | ✅    | ✅      | ✅     |
| CRUD de sinistros           | ✅    | ✅      | ✅     |
| Relatórios completos        | ✅    | ✅      | ❌     |
| Dashboard completo          | ✅    | ✅      | Parcial|
| CRM (próprias negociações)  | ✅    | ✅      | ✅     |
| CRM (todas negociações)     | ✅    | ✅      | ❌     |

#### 4.1.4 Views

| View                 | Tipo              | URL                        |
|----------------------|-------------------|----------------------------|
| LoginView            | FormView          | `/accounts/login/`         |
| LogoutView           | RedirectView      | `/accounts/logout/`        |
| UserListView         | ListView          | `/accounts/users/`         |
| UserCreateView       | CreateView        | `/accounts/users/create/`  |
| UserUpdateView       | UpdateView        | `/accounts/users/<pk>/edit/` |
| UserDetailView       | DetailView        | `/accounts/users/<pk>/`    |
| ProfileView          | UpdateView        | `/accounts/profile/`       |
| PasswordChangeView   | FormView          | `/accounts/password/`      |

---

### 4.2 CLIENTS — Cadastro de Clientes

**App:** `clients`

#### 4.2.1 Models

**Model: `Client`**

| Campo               | Tipo                  | Descrição                                |
|---------------------|-----------------------|------------------------------------------|
| client_type         | CharField (choices)   | PF ou PJ                                 |
| name                | CharField(255)        | Nome completo / Razão social             |
| cpf_cnpj            | CharField(18), unique | CPF ou CNPJ                              |
| rg_ie               | CharField(20)         | RG ou Inscrição Estadual (opcional)      |
| birth_date          | DateField (nullable)  | Data de nascimento (PF)                  |
| gender              | CharField (choices)   | Gênero (PF, opcional)                    |
| marital_status      | CharField (choices)   | Estado civil (PF, opcional)              |
| occupation          | CharField(100)        | Profissão/atividade (opcional)           |
| email               | EmailField            | Email principal                          |
| phone               | CharField(20)         | Telefone principal                       |
| secondary_phone     | CharField(20)         | Telefone secundário (opcional)           |
| zip_code            | CharField(10)         | CEP                                      |
| street              | CharField(255)        | Logradouro                               |
| number              | CharField(10)         | Número                                   |
| complement          | CharField(100)        | Complemento (opcional)                   |
| neighborhood        | CharField(100)        | Bairro                                   |
| city                | CharField(100)        | Cidade                                   |
| state               | CharField(2)          | UF                                       |
| notes               | TextField             | Observações (opcional)                   |
| is_active           | BooleanField          | Cliente ativo                            |
| broker              | FK → User             | Corretor responsável                     |
| created_at          | DateTimeField         | Timestamp criação                        |
| updated_at          | DateTimeField         | Timestamp atualização                    |

**Choices de client_type:**

```python
class ClientType(models.TextChoices):
    INDIVIDUAL = 'pf', 'Pessoa Física'
    COMPANY = 'pj', 'Pessoa Jurídica'
```

#### 4.2.2 Funcionalidades

- CRUD completo de clientes (PF e PJ)
- Busca e filtros por nome, CPF/CNPJ, tipo, corretor, status
- Visualização do histórico de apólices do cliente
- Visualização de sinistros vinculados
- Exportação da lista de clientes (CSV)
- Integração com ViaCEP para preenchimento automático de endereço via JS

#### 4.2.3 Views

| View               | Tipo        | URL                          |
|--------------------|-------------|------------------------------|
| ClientListView     | ListView    | `/clients/`                  |
| ClientCreateView   | CreateView  | `/clients/create/`           |
| ClientUpdateView   | UpdateView  | `/clients/<pk>/edit/`        |
| ClientDetailView   | DetailView  | `/clients/<pk>/`             |
| ClientDeleteView   | DeleteView  | `/clients/<pk>/delete/`      |
| ClientExportView   | View (CSV)  | `/clients/export/`           |

---

### 4.3 INSURERS — Cadastro de Seguradoras

**App:** `insurers`

#### 4.3.1 Models

**Model: `Insurer`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| name               | CharField(255)      | Nome da seguradora                      |
| cnpj               | CharField(18), unique| CNPJ                                   |
| susep_code         | CharField(20)       | Código SUSEP (opcional)                 |
| email              | EmailField          | Email de contato                        |
| phone              | CharField(20)       | Telefone                                |
| website            | URLField            | Site (opcional)                         |
| contact_name       | CharField(150)      | Nome do contato principal (opcional)    |
| contact_email      | EmailField          | Email do contato (opcional)             |
| contact_phone      | CharField(20)       | Telefone do contato (opcional)          |
| zip_code           | CharField(10)       | CEP                                     |
| street             | CharField(255)      | Logradouro                              |
| number             | CharField(10)       | Número                                  |
| complement         | CharField(100)      | Complemento (opcional)                  |
| neighborhood       | CharField(100)      | Bairro                                  |
| city               | CharField(100)      | Cidade                                  |
| state              | CharField(2)        | UF                                      |
| logo               | ImageField          | Logo da seguradora (opcional)           |
| is_active          | BooleanField        | Seguradora ativa                        |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `InsurerBranch`** (Ramos de atuação da seguradora)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| insurer            | FK → Insurer        | Seguradora                              |
| name               | CharField(100)      | Nome do ramo (ex: Auto, Vida, Saúde)    |
| susep_branch_code  | CharField(20)       | Código do ramo SUSEP (opcional)         |
| is_active          | BooleanField        | Ramo ativo                              |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.3.2 Funcionalidades

- CRUD completo de seguradoras
- Gestão de ramos por seguradora
- Busca e filtros por nome, CNPJ, ramo
- Visualização de apólices vinculadas por seguradora
- Listagem de contatos da seguradora

#### 4.3.3 Views

| View                 | Tipo        | URL                             |
|----------------------|-------------|---------------------------------|
| InsurerListView      | ListView    | `/insurers/`                    |
| InsurerCreateView    | CreateView  | `/insurers/create/`             |
| InsurerUpdateView    | UpdateView  | `/insurers/<pk>/edit/`          |
| InsurerDetailView    | DetailView  | `/insurers/<pk>/`               |
| InsurerDeleteView    | DeleteView  | `/insurers/<pk>/delete/`        |

---

### 4.4 COVERAGES — Coberturas e Itens

**App:** `coverages`

#### 4.4.1 Models

**Model: `InsuranceType`** (Tipos/ramos de seguro)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| name               | CharField(100)      | Nome (Auto, Vida, Residencial, etc.)    |
| slug               | SlugField (unique)  | Slug para URLs                          |
| description        | TextField           | Descrição (opcional)                    |
| is_active          | BooleanField        | Tipo ativo                              |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `Coverage`** (Coberturas disponíveis)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| insurance_type     | FK → InsuranceType  | Tipo de seguro                          |
| name               | CharField(200)      | Nome da cobertura                       |
| description        | TextField           | Descrição detalhada (opcional)          |
| is_active          | BooleanField        | Cobertura ativa                         |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `CoverageItem`** (Itens dentro de uma cobertura)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| coverage           | FK → Coverage       | Cobertura pai                           |
| name               | CharField(200)      | Nome do item                            |
| description        | TextField           | Descrição (opcional)                    |
| is_active          | BooleanField        | Item ativo                              |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.4.2 Funcionalidades

- CRUD de tipos de seguro
- CRUD de coberturas por tipo de seguro
- CRUD de itens de cobertura
- Relação hierárquica: Tipo de Seguro → Coberturas → Itens
- Filtros e busca

#### 4.4.3 Views

| View                     | Tipo        | URL                                  |
|--------------------------|-------------|--------------------------------------|
| InsuranceTypeListView    | ListView    | `/coverages/types/`                  |
| InsuranceTypeCreateView  | CreateView  | `/coverages/types/create/`           |
| InsuranceTypeUpdateView  | UpdateView  | `/coverages/types/<pk>/edit/`        |
| CoverageListView         | ListView    | `/coverages/`                        |
| CoverageCreateView       | CreateView  | `/coverages/create/`                 |
| CoverageUpdateView       | UpdateView  | `/coverages/<pk>/edit/`              |
| CoverageItemCreateView   | CreateView  | `/coverages/<coverage_pk>/items/create/` |
| CoverageItemUpdateView   | UpdateView  | `/coverages/items/<pk>/edit/`        |

---

### 4.5 POLICIES — Apólices e Propostas de Seguro

**App:** `policies`

#### 4.5.1 Models

**Model: `Proposal`** (Proposta de seguro)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| proposal_number    | CharField(50), unique| Número da proposta                      |
| client             | FK → Client         | Cliente                                 |
| insurer            | FK → Insurer        | Seguradora                              |
| insurance_type     | FK → InsuranceType  | Tipo de seguro                          |
| broker             | FK → User           | Corretor responsável                    |
| status             | CharField (choices)  | Status da proposta                     |
| submission_date    | DateField           | Data de envio da proposta               |
| response_date      | DateField (nullable) | Data da resposta                       |
| premium_amount     | DecimalField(12,2)  | Valor do prêmio proposto                |
| notes              | TextField           | Observações (opcional)                  |
| rejection_reason   | TextField           | Motivo da recusa (se recusada)          |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de status (Proposal):**

```python
class ProposalStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    SUBMITTED = 'submitted', 'Enviada'
    UNDER_ANALYSIS = 'under_analysis', 'Em Análise'
    APPROVED = 'approved', 'Aprovada'
    REJECTED = 'rejected', 'Recusada'
    CANCELLED = 'cancelled', 'Cancelada'
```

**Model: `Policy`** (Apólice de seguro)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| policy_number      | CharField(50), unique| Número da apólice                      |
| proposal           | FK → Proposal (null) | Proposta de origem (opcional)          |
| client             | FK → Client         | Cliente/segurado                        |
| insurer            | FK → Insurer        | Seguradora                              |
| insurance_type     | FK → InsuranceType  | Tipo de seguro                          |
| broker             | FK → User           | Corretor responsável                    |
| status             | CharField (choices)  | Status da apólice                      |
| start_date         | DateField           | Início de vigência                      |
| end_date           | DateField           | Fim de vigência                         |
| premium_amount     | DecimalField(12,2)  | Valor do prêmio                         |
| insured_amount     | DecimalField(14,2)  | Importância segurada total              |
| commission_rate    | DecimalField(5,2)   | Percentual de comissão (%)              |
| commission_amount  | DecimalField(12,2)  | Valor da comissão (R$)                  |
| installments       | PositiveIntegerField | Número de parcelas                      |
| payment_method     | CharField (choices)  | Forma de pagamento                     |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de status (Policy):**

```python
class PolicyStatus(models.TextChoices):
    ACTIVE = 'active', 'Ativa'
    EXPIRED = 'expired', 'Vencida'
    CANCELLED = 'cancelled', 'Cancelada'
    SUSPENDED = 'suspended', 'Suspensa'
    PENDING = 'pending', 'Pendente'
```

**Choices de payment_method:**

```python
class PaymentMethod(models.TextChoices):
    BANK_SLIP = 'bank_slip', 'Boleto Bancário'
    CREDIT_CARD = 'credit_card', 'Cartão de Crédito'
    DEBIT = 'debit', 'Débito em Conta'
    PIX = 'pix', 'PIX'
    INVOICE = 'invoice', 'Fatura'
```

**Model: `PolicyCoverage`** (Coberturas contratadas na apólice)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| policy             | FK → Policy         | Apólice                                 |
| coverage           | FK → Coverage       | Cobertura                               |
| insured_amount     | DecimalField(14,2)  | Valor segurado desta cobertura          |
| deductible         | DecimalField(12,2)  | Valor da franquia                       |
| premium_amount     | DecimalField(12,2)  | Prêmio desta cobertura                  |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `PolicyDocument`** (Documentos anexados à apólice)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| policy             | FK → Policy         | Apólice                                 |
| title              | CharField(200)      | Título do documento                     |
| file               | FileField           | Arquivo                                 |
| document_type      | CharField (choices)  | Tipo (proposta, apólice, CI, outros)   |
| uploaded_by        | FK → User           | Quem fez upload                         |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.5.2 Funcionalidades

- CRUD completo de propostas
- CRUD completo de apólices
- Conversão de proposta aprovada em apólice (com dados pré-preenchidos)
- Vinculação de coberturas contratadas por apólice (inline formset)
- Upload e gestão de documentos por apólice
- Filtros por cliente, seguradora, tipo de seguro, status, corretor, vigência
- Busca por número de apólice/proposta
- Cálculo automático de comissão (rate × premium)
- Indicadores visuais de vigência (ativa, vencendo em 30 dias, vencida)
- Exportação de listagem (CSV)

#### 4.5.3 Views

| View                   | Tipo         | URL                                |
|------------------------|--------------|-------------------------------------|
| ProposalListView       | ListView     | `/policies/proposals/`              |
| ProposalCreateView     | CreateView   | `/policies/proposals/create/`       |
| ProposalUpdateView     | UpdateView   | `/policies/proposals/<pk>/edit/`    |
| ProposalDetailView     | DetailView   | `/policies/proposals/<pk>/`         |
| ProposalConvertView    | FormView     | `/policies/proposals/<pk>/convert/` |
| PolicyListView         | ListView     | `/policies/`                        |
| PolicyCreateView       | CreateView   | `/policies/create/`                 |
| PolicyUpdateView       | UpdateView   | `/policies/<pk>/edit/`              |
| PolicyDetailView       | DetailView   | `/policies/<pk>/`                   |
| PolicyDeleteView       | DeleteView   | `/policies/<pk>/delete/`            |
| PolicyExportView       | View (CSV)   | `/policies/export/`                 |

#### 4.5.4 Signals

```python
# policies/signals.py

# post_save em Proposal: quando status muda para 'approved', notificar/criar log
# post_save em Policy: atualizar contadores no dashboard, verificar renovações
```

---

### 4.6 CLAIMS — Gestão de Sinistros

**App:** `claims`

#### 4.6.1 Models

**Model: `Claim`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| claim_number       | CharField(50), unique| Número do sinistro                      |
| policy             | FK → Policy         | Apólice vinculada                       |
| client             | FK → Client         | Cliente (denormalized para facilitar)   |
| status             | CharField (choices)  | Status do sinistro                      |
| occurrence_date    | DateField           | Data da ocorrência                      |
| notification_date  | DateField           | Data da notificação à seguradora        |
| description        | TextField           | Descrição do sinistro                   |
| location           | CharField(255)      | Local da ocorrência (opcional)          |
| claimed_amount     | DecimalField(14,2)  | Valor reclamado                         |
| approved_amount    | DecimalField(14,2)  | Valor aprovado/pago (nullable)          |
| resolution_date    | DateField (nullable) | Data de resolução                      |
| resolution_notes   | TextField           | Observações da resolução (opcional)     |
| broker             | FK → User           | Corretor responsável                    |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de status (Claim):**

```python
class ClaimStatus(models.TextChoices):
    OPEN = 'open', 'Aberto'
    UNDER_ANALYSIS = 'under_analysis', 'Em Análise'
    DOCUMENTATION_PENDING = 'documentation_pending', 'Pendente de Documentação'
    APPROVED = 'approved', 'Aprovado'
    PARTIALLY_APPROVED = 'partially_approved', 'Parcialmente Aprovado'
    DENIED = 'denied', 'Negado'
    PAID = 'paid', 'Pago'
    CLOSED = 'closed', 'Encerrado'
```

**Model: `ClaimDocument`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| claim              | FK → Claim          | Sinistro                                |
| title              | CharField(200)      | Título                                  |
| file               | FileField           | Arquivo                                 |
| document_type      | CharField (choices)  | Tipo do documento                      |
| uploaded_by        | FK → User           | Quem fez upload                         |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `ClaimTimeline`** (Histórico de movimentações)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| claim              | FK → Claim          | Sinistro                                |
| action             | CharField(200)      | Descrição da ação                       |
| performed_by       | FK → User           | Quem realizou                           |
| old_status         | CharField(30)       | Status anterior (opcional)              |
| new_status         | CharField(30)       | Novo status (opcional)                  |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.6.2 Funcionalidades

- CRUD completo de sinistros
- Timeline/histórico de movimentações por sinistro (automático via signal ao mudar status)
- Upload de documentos por sinistro
- Filtros por apólice, cliente, status, período, corretor
- Busca por número de sinistro
- Acompanhamento visual de status (progress bar ou stepper)
- Resumo financeiro (valor reclamado vs aprovado vs pago)

#### 4.6.3 Views

| View                | Tipo        | URL                           |
|---------------------|-------------|-------------------------------|
| ClaimListView       | ListView    | `/claims/`                    |
| ClaimCreateView     | CreateView  | `/claims/create/`             |
| ClaimUpdateView     | UpdateView  | `/claims/<pk>/edit/`          |
| ClaimDetailView     | DetailView  | `/claims/<pk>/`               |
| ClaimDeleteView     | DeleteView  | `/claims/<pk>/delete/`        |

#### 4.6.4 Signals

```python
# claims/signals.py

# post_save em Claim: ao mudar status, criar entrada em ClaimTimeline automaticamente
```

---

### 4.7 ENDORSEMENTS — Gestão de Endossos

**App:** `endorsements`

#### 4.7.1 Models

**Model: `Endorsement`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| endorsement_number | CharField(50), unique| Número do endosso                      |
| policy             | FK → Policy         | Apólice vinculada                       |
| endorsement_type   | CharField (choices)  | Tipo de endosso                        |
| status             | CharField (choices)  | Status                                  |
| request_date       | DateField           | Data da solicitação                     |
| effective_date     | DateField           | Data de efeito                          |
| description        | TextField           | Descrição das alterações                |
| premium_difference | DecimalField(12,2)  | Diferença de prêmio (+/-)               |
| requested_by       | FK → User           | Corretor que solicitou                  |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de endorsement_type:**

```python
class EndorsementType(models.TextChoices):
    INCLUSION = 'inclusion', 'Inclusão'
    EXCLUSION = 'exclusion', 'Exclusão'
    MODIFICATION = 'modification', 'Alteração'
    CANCELLATION = 'cancellation', 'Cancelamento'
    TRANSFER = 'transfer', 'Transferência'
```

**Choices de status (Endorsement):**

```python
class EndorsementStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    REQUESTED = 'requested', 'Solicitado'
    UNDER_ANALYSIS = 'under_analysis', 'Em Análise'
    APPROVED = 'approved', 'Aprovado'
    REJECTED = 'rejected', 'Rejeitado'
    APPLIED = 'applied', 'Aplicado'
```

**Model: `EndorsementDocument`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| endorsement        | FK → Endorsement    | Endosso                                 |
| title              | CharField(200)      | Título                                  |
| file               | FileField           | Arquivo                                 |
| uploaded_by        | FK → User           | Quem fez upload                         |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.7.2 Funcionalidades

- CRUD completo de endossos vinculados a apólices
- Controle de tipos (inclusão, exclusão, alteração, cancelamento, transferência)
- Upload de documentos do endosso
- Ao aplicar endosso aprovado, atualizar dados da apólice correspondente (via signal)
- Filtros por apólice, tipo, status, período
- Histórico de endossos por apólice

#### 4.7.3 Views

| View                     | Tipo        | URL                                      |
|--------------------------|-------------|------------------------------------------|
| EndorsementListView      | ListView    | `/endorsements/`                         |
| EndorsementCreateView    | CreateView  | `/endorsements/create/`                  |
| EndorsementUpdateView    | UpdateView  | `/endorsements/<pk>/edit/`               |
| EndorsementDetailView    | DetailView  | `/endorsements/<pk>/`                    |
| EndorsementDeleteView    | DeleteView  | `/endorsements/<pk>/delete/`             |

#### 4.7.4 Signals

```python
# endorsements/signals.py

# post_save em Endorsement: quando status muda para 'applied',
# atualizar apólice (premium, coberturas, vigência conforme tipo de endosso)
```

---

### 4.8 RENEWALS — Gestão de Renovações

**App:** `renewals`

#### 4.8.1 Models

**Model: `Renewal`**

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| policy             | FK → Policy         | Apólice original                        |
| renewed_policy     | FK → Policy (null)  | Nova apólice gerada (após renovar)      |
| status             | CharField (choices)  | Status da renovação                     |
| due_date           | DateField           | Data limite para renovação              |
| contact_date       | DateField (nullable) | Data do contato com cliente             |
| new_premium        | DecimalField(12,2)  | Novo valor de prêmio proposto (nullable)|
| new_insurer        | FK → Insurer (null) | Nova seguradora (se trocar)             |
| broker             | FK → User           | Corretor responsável                    |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de status (Renewal):**

```python
class RenewalStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    CONTACTED = 'contacted', 'Cliente Contatado'
    QUOTE_SENT = 'quote_sent', 'Cotação Enviada'
    RENEWED = 'renewed', 'Renovada'
    NOT_RENEWED = 'not_renewed', 'Não Renovada'
    CANCELLED = 'cancelled', 'Cancelada'
```

#### 4.8.2 Funcionalidades

- Listagem de apólices próximas do vencimento (30, 60, 90 dias)
- Criação automática de registros de renovação via management command ou signal (quando apólice entra nos últimos 60 dias de vigência)
- Workflow de renovação: Pendente → Contatado → Cotação Enviada → Renovada/Não Renovada
- Ao renovar, opção de gerar nova apólice com dados pré-preenchidos da anterior
- Dashboard de renovações pendentes
- Filtros por período, status, corretor, seguradora
- Alertas visuais para renovações urgentes

#### 4.8.3 Views

| View                | Tipo        | URL                             |
|---------------------|-------------|----------------------------------|
| RenewalListView     | ListView    | `/renewals/`                     |
| RenewalCreateView   | CreateView  | `/renewals/create/`              |
| RenewalUpdateView   | UpdateView  | `/renewals/<pk>/edit/`           |
| RenewalDetailView   | DetailView  | `/renewals/<pk>/`                |
| RenewalRenewView    | FormView    | `/renewals/<pk>/renew/`          |

#### 4.8.4 Management Command

```python
# renewals/management/commands/check_renewals.py

# Comando para verificar apólices que entram na janela de renovação (60 dias)
# e criar automaticamente registros de Renewal com status 'pending'
# Uso: python manage.py check_renewals
# Pode ser agendado via cron
```

---

### 4.9 CRM — Painel de Negociações

**App:** `crm`

#### 4.9.1 Models

**Model: `Pipeline`** (Funil de vendas)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| name               | CharField(100)      | Nome do pipeline                        |
| is_default         | BooleanField        | Pipeline padrão                         |
| is_active          | BooleanField        | Pipeline ativo                          |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Model: `PipelineStage`** (Etapas do funil)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| pipeline           | FK → Pipeline       | Pipeline                                |
| name               | CharField(100)      | Nome da etapa                           |
| order              | PositiveIntegerField | Ordem de exibição                       |
| color              | CharField(7)        | Cor da etapa (hex)                      |
| is_won             | BooleanField        | Etapa de ganho (fechamento positivo)    |
| is_lost            | BooleanField        | Etapa de perda                          |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Etapas padrão sugeridas (seed):**

1. Prospecção
2. Primeiro Contato
3. Cotação
4. Proposta Enviada
5. Negociação
6. Fechamento (is_won=True)
7. Perdido (is_lost=True)

**Model: `Deal`** (Negociação/Oportunidade)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| title              | CharField(200)      | Título da negociação                    |
| client             | FK → Client         | Cliente                                 |
| broker             | FK → User           | Corretor responsável                    |
| pipeline           | FK → Pipeline       | Pipeline                                |
| stage              | FK → PipelineStage  | Etapa atual                             |
| insurance_type     | FK → InsuranceType  | Tipo de seguro (opcional)               |
| insurer            | FK → Insurer (null) | Seguradora (opcional)                   |
| expected_value     | DecimalField(12,2)  | Valor esperado                          |
| expected_close_date| DateField (nullable) | Data prevista de fechamento            |
| priority           | CharField (choices)  | Prioridade                             |
| source             | CharField (choices)  | Origem da negociação                   |
| proposal           | FK → Proposal (null)| Proposta vinculada (opcional)           |
| policy             | FK → Policy (null)  | Apólice gerada (se fechou)             |
| lost_reason        | TextField           | Motivo da perda (se perdido, opcional)  |
| notes              | TextField           | Observações (opcional)                  |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

**Choices de priority:**

```python
class DealPriority(models.TextChoices):
    LOW = 'low', 'Baixa'
    MEDIUM = 'medium', 'Média'
    HIGH = 'high', 'Alta'
    URGENT = 'urgent', 'Urgente'
```

**Choices de source:**

```python
class DealSource(models.TextChoices):
    REFERRAL = 'referral', 'Indicação'
    WEBSITE = 'website', 'Site'
    PHONE = 'phone', 'Telefone'
    WALK_IN = 'walk_in', 'Presencial'
    SOCIAL_MEDIA = 'social_media', 'Redes Sociais'
    RENEWAL = 'renewal', 'Renovação'
    OTHER = 'other', 'Outro'
```

**Model: `DealActivity`** (Atividades/interações da negociação)

| Campo              | Tipo                 | Descrição                               |
|--------------------|---------------------|-----------------------------------------|
| deal               | FK → Deal           | Negociação                              |
| activity_type      | CharField (choices)  | Tipo: note, call, email, meeting, task |
| title              | CharField(200)      | Título/resumo                           |
| description        | TextField           | Descrição (opcional)                    |
| due_date           | DateTimeField (null) | Data/hora agendada (para tasks)        |
| is_completed       | BooleanField        | Atividade concluída                     |
| performed_by       | FK → User           | Quem registrou                          |
| created_at         | DateTimeField       | Timestamp criação                       |
| updated_at         | DateTimeField       | Timestamp atualização                   |

#### 4.9.2 Funcionalidades

**Visão Kanban:**
- Board visual com colunas representando as etapas do pipeline
- Drag-and-drop de cards entre etapas (via JS)
- Cards exibem: título, cliente, valor, corretor, prioridade (badge colorido)
- Filtros: corretor, prioridade, tipo de seguro, período
- Contador de deals e soma de valores por coluna

**Visão Grid (Tabela):**
- Listagem tabulada de todas as negociações
- Ordenação por colunas (data, valor, status, prioridade)
- Filtros equivalentes ao kanban
- Ações rápidas inline (mudar etapa, editar)

**Detalhamento do Deal:**
- Timeline de atividades
- Registro de interações (notas, ligações, emails, reuniões)
- Vinculação com proposta/apólice
- Histórico de mudanças de etapa

**Gestão do Pipeline:**
- CRUD de pipelines (admin/manager)
- CRUD de etapas (ordenáveis, com cores)
- Múltiplos pipelines possíveis

#### 4.9.3 Views

| View                 | Tipo           | URL                             |
|----------------------|----------------|----------------------------------|
| DealKanbanView       | TemplateView   | `/crm/kanban/`                   |
| DealListView         | ListView       | `/crm/deals/`                    |
| DealCreateView       | CreateView     | `/crm/deals/create/`             |
| DealUpdateView       | UpdateView     | `/crm/deals/<pk>/edit/`          |
| DealDetailView       | DetailView     | `/crm/deals/<pk>/`               |
| DealDeleteView       | DeleteView     | `/crm/deals/<pk>/delete/`        |
| DealMoveStageView    | View (AJAX)    | `/crm/deals/<pk>/move/`          |
| DealActivityCreateView| CreateView    | `/crm/deals/<pk>/activities/create/` |
| PipelineManageView   | TemplateView   | `/crm/pipelines/`               |

#### 4.9.4 JavaScript (Kanban)

O kanban utiliza JavaScript vanilla (ou lib leve como SortableJS) para drag-and-drop. Ao mover um card, faz-se uma requisição AJAX (fetch) para `DealMoveStageView` atualizando a etapa no backend.

---

### 4.10 REPORTS — Relatórios

**App:** `reports`

#### 4.10.1 Relatórios Disponíveis

| Relatório                        | Descrição                                                  | Filtros                                        |
|----------------------------------|------------------------------------------------------------|-------------------------------------------------|
| Produção por Período             | Total de apólices emitidas, prêmios, comissões por período | Data início/fim, corretor, seguradora, ramo    |
| Comissões por Corretor           | Detalhamento de comissões por corretor                     | Período, corretor                               |
| Carteira por Seguradora          | Distribuição de apólices e prêmios por seguradora          | Período, status                                 |
| Carteira por Tipo de Seguro      | Distribuição por ramo/tipo de seguro                       | Período, seguradora                             |
| Sinistros por Período            | Quantidade e valores de sinistros                          | Período, status, seguradora, ramo              |
| Sinistralidade                   | Relação sinistros/prêmios (loss ratio)                     | Período, seguradora, ramo                      |
| Renovações Pendentes             | Apólices a vencer com status de renovação                  | Período, corretor, seguradora                  |
| Clientes por Corretor            | Distribuição de clientes ativos por corretor               | Corretor, status                                |
| CRM — Funil de Vendas            | Análise do pipeline (conversão, tempo por etapa, valores)  | Pipeline, corretor, período                    |
| Endossos por Período             | Endossos realizados por período e tipo                     | Período, tipo, seguradora                      |

#### 4.10.2 Funcionalidades

- Cada relatório possui formulário de filtros
- Exibição em tabela na tela com totalizadores
- Exportação para CSV
- Exportação para PDF (usando ReportLab ou WeasyPrint)
- Gráficos quando aplicável (Chart.js nos templates)

#### 4.10.3 Views

| View                              | Tipo         | URL                                  |
|-----------------------------------|-------------|--------------------------------------|
| ReportIndexView                   | TemplateView| `/reports/`                          |
| ProductionReportView              | FormView    | `/reports/production/`               |
| CommissionReportView              | FormView    | `/reports/commissions/`              |
| InsurerPortfolioReportView        | FormView    | `/reports/insurer-portfolio/`        |
| InsuranceTypePortfolioReportView  | FormView    | `/reports/type-portfolio/`           |
| ClaimsReportView                  | FormView    | `/reports/claims/`                   |
| LossRatioReportView              | FormView    | `/reports/loss-ratio/`               |
| RenewalReportView                 | FormView    | `/reports/renewals/`                 |
| ClientsByBrokerReportView         | FormView    | `/reports/clients-by-broker/`        |
| CRMFunnelReportView              | FormView    | `/reports/crm-funnel/`              |
| EndorsementReportView             | FormView    | `/reports/endorsements/`             |

---

### 4.11 DASHBOARD — Visão Geral e Métricas

**App:** `dashboard`

#### 4.11.1 Métricas e Cards

**KPIs Principais (cards no topo):**

- Total de apólices ativas
- Total de prêmios em carteira (R$)
- Total de comissões do período (R$)
- Total de clientes ativos
- Sinistros abertos
- Renovações pendentes (próximos 30 dias)
- Negociações em andamento (CRM)
- Taxa de conversão do funil CRM (%)

**Gráficos:**

- Produção mensal (barras) — prêmios e comissões nos últimos 12 meses
- Distribuição por tipo de seguro (pizza/donut)
- Distribuição por seguradora (pizza/donut)
- Evolução de sinistros (linha) — últimos 12 meses
- Funil CRM (funil visual) — deals por etapa
- Renovações por mês (barras) — próximos 3 meses
- Top 5 corretores por produção (barras horizontais)
- Sinistralidade por ramo (barras agrupadas)

**Tabelas Resumo:**

- Últimas 10 apólices emitidas
- Próximas 10 renovações
- Últimos 5 sinistros abertos
- Deals recentes do CRM

#### 4.11.2 Funcionalidades

- Filtro global por período (mês/trimestre/ano/custom)
- Filtro por corretor (admin/manager veem todos; broker vê apenas seus dados)
- Atualização dos dados ao aplicar filtros (form submit ou AJAX)
- Todos os gráficos com Chart.js
- Cards com indicadores de variação (↑↓) comparando com período anterior
- Responsivo e aderente ao design system

#### 4.11.3 Views

| View              | Tipo         | URL            |
|-------------------|-------------|----------------|
| DashboardView     | TemplateView| `/dashboard/`  |

A DashboardView agrega queries de múltiplas apps no `get_context_data()`, utilizando annotations e aggregations do Django ORM.

---

## 5. Design System e UI

### 5.1 Referência

O design system do projeto está definido no arquivo `design_system/design-system.html`. Todo o frontend deve respeitar rigorosamente:

- Paleta de cores (primárias, secundárias, neutras, status)
- Tipografia (font-family, sizes, weights)
- Espaçamentos e grid
- Componentes (botões, cards, inputs, tabelas, badges, modais, alertas)
- Layout (sidebar, topbar, content area)

### 5.2 Layout Base

```
┌─────────────────────────────────────────────────┐
│  TOPBAR (logo, busca global, notificações, user)│
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ SIDEBAR  │         CONTENT AREA                 │
│ (menu)   │                                      │
│          │  ┌──────────────────────────────┐    │
│ Dashboard│  │  Page Header (título + ações) │    │
│ Clientes │  ├──────────────────────────────┤    │
│ Segurad. │  │                              │    │
│ Apólices │  │  Page Content                │    │
│ Propostas│  │  (tabelas, forms, cards...)  │    │
│ Sinistros│  │                              │    │
│ Endossos │  └──────────────────────────────┘    │
│ Renov.   │                                      │
│ CRM      │                                      │
│ Relat.   │                                      │
│ Usuários │                                      │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

### 5.3 Templates Hierarchy

```
templates/
├── base.html                    # Layout master (sidebar + topbar + content block)
├── partials/
│   ├── _sidebar.html            # Menu lateral
│   ├── _topbar.html             # Barra superior
│   ├── _pagination.html         # Paginação reutilizável
│   ├── _messages.html           # Django messages (alerts)
│   ├── _confirm_delete.html     # Modal de confirmação de exclusão
│   └── _filters.html            # Componente de filtros genérico
├── accounts/
│   ├── login.html
│   ├── user_list.html
│   ├── user_form.html
│   ├── user_detail.html
│   └── profile.html
├── clients/
│   ├── client_list.html
│   ├── client_form.html
│   └── client_detail.html
├── insurers/
│   ├── insurer_list.html
│   ├── insurer_form.html
│   └── insurer_detail.html
├── coverages/
│   ├── insurance_type_list.html
│   ├── coverage_list.html
│   └── coverage_form.html
├── policies/
│   ├── proposal_list.html
│   ├── proposal_form.html
│   ├── proposal_detail.html
│   ├── policy_list.html
│   ├── policy_form.html
│   └── policy_detail.html
├── claims/
│   ├── claim_list.html
│   ├── claim_form.html
│   └── claim_detail.html
├── endorsements/
│   ├── endorsement_list.html
│   ├── endorsement_form.html
│   └── endorsement_detail.html
├── renewals/
│   ├── renewal_list.html
│   ├── renewal_form.html
│   └── renewal_detail.html
├── crm/
│   ├── deal_kanban.html
│   ├── deal_list.html
│   ├── deal_form.html
│   ├── deal_detail.html
│   └── pipeline_manage.html
├── reports/
│   ├── report_index.html
│   └── report_*.html           # Um template por relatório
└── dashboard/
    └── dashboard.html
```

---

## 6. Integrações e Libs Externas

| Lib/Recurso      | Propósito                                     | Versão        |
|-------------------|----------------------------------------------|---------------|
| Django            | Framework web                                | 6.0           |
| Pillow            | Upload e processamento de imagens (avatares, logos) | latest  |
| ReportLab ou WeasyPrint | Exportação de relatórios em PDF        | latest        |
| ViaCEP            | Consulta de CEP para endereços (fetch JS)    | API pública   |
| django-widget-tweaks | Customização de form widgets nos templates (opcional) | latest |

**TEMPLATES/FRONTEND:** Os templates e componentes do frontend devem respeitar rigorasamente o design system em @design_system/design-system.html.

---

## 7. Segurança e Permissões

### 7.1 Autenticação

- Login obrigatório para todas as páginas (exceto login)
- `LoginRequiredMixin` em todas as CBVs
- Sessão com timeout configurável no settings
- Proteção CSRF em todos os formulários (nativo Django)

### 7.2 Autorização

- Mixins customizados para controle de role:

```python
# core/mixins.py

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('admin', 'manager')


class BrokerFilterMixin:
    """Filtra queryset para mostrar apenas dados do corretor logado (se broker)."""
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'broker':
            return qs.filter(broker=self.request.user)
        return qs
```

### 7.3 Validações

- CPF/CNPJ com validação de formato e dígitos verificadores (utils em `core/validators.py`)
- Campos monetários com DecimalField (nunca FloatField)
- Sanitização de inputs nos formulários
- Proteção contra mass assignment via ModelForm `fields` explícitos

---

## 8. Plano de Desenvolvimento (Fases)

### Fase 1 — Fundação (Semana 1-2)

- [x] Setup do projeto Django
- [x] Configuração de settings (static, media, templates, auth)
- [x] App `utils` (TimeStampedModel, mixins, validators, templatetags)
- [x] App `accounts` (Custom User, login por email, CRUD de usuários, permissões)
- [x] Template base (`base.html`, sidebar, topbar, partials)
- [x] Página de login funcional

### Fase 2 — Cadastros Base (Semana 3-4)

- [x] App `clients` (CRUD completo, filtros, busca, integração ViaCEP)
- [x] App `insurers` (CRUD completo, ramos)
- [x] App `coverages` (tipos de seguro, coberturas, itens)

### Fase 3 — Core do Negócio (Semana 5-7)

- [x] App `policies` (propostas + apólices + coberturas contratadas + documentos)
- [x] Conversão de proposta em apólice
- [x] App `claims` (sinistros + timeline + documentos)
- [x] App `endorsements` (endossos + documentos + aplicação na apólice)

### Fase 4 — Operações Avançadas (Semana 8-9)

- [x] App `renewals` (gestão de renovações + management command)
- [x] App `crm` (pipeline, etapas, deals, atividades, kanban + grid)
- [x] JavaScript do kanban (drag-and-drop, AJAX)

### Fase 5 — Inteligência e Relatórios (Semana 10-11)

- [ ] App `dashboard` (KPIs, gráficos Chart.js, tabelas resumo)
- [ ] App `reports` (todos os 10 relatórios, filtros, exportação CSV/PDF)

### Fase 6 — Polish e Refinamento (Semana 12)

- [ ] Revisão geral de UI/UX conforme design system
- [ ] Ajustes de responsividade
- [ ] Seed data para demonstração
- [ ] Validações finais de permissões

---

## 9. Configurações do Projeto

### 9.1 settings.py — Pontos Relevantes

```python
# scs/settings.py

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### 9.2 URLs Raiz

```python
# scs/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('clients/', include('clients.urls')),
    path('insurers/', include('insurers.urls')),
    path('coverages/', include('coverages.urls')),
    path('policies/', include('policies.urls')),
    path('claims/', include('claims.urls')),
    path('endorsements/', include('endorsements.urls')),
    path('renewals/', include('renewals.urls')),
    path('crm/', include('crm.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 9.3 requirements.txt

```
Django==6.0
Pillow>=10.0
django-widget-tweaks>=1.5
reportlab>=4.0
```

---

## 10. Glossário do Domínio

| Termo              | Definição                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **Apólice**        | Contrato de seguro emitido pela seguradora ao segurado                    |
| **Proposta**       | Documento de solicitação de seguro enviado à seguradora para análise      |
| **Prêmio**         | Valor pago pelo segurado à seguradora pela cobertura do risco             |
| **Sinistro**       | Evento coberto pelo seguro que gera direito à indenização                 |
| **Endosso**        | Documento que altera as condições da apólice durante sua vigência         |
| **Franquia**       | Valor que o segurado paga em caso de sinistro antes da indenização        |
| **Importância Segurada** | Valor máximo de cobertura contratado na apólice                     |
| **Comissão**       | Percentual/valor que o corretor recebe pela intermediação do seguro       |
| **Vigência**       | Período de validade da apólice (data início a data fim)                   |
| **Cobertura**      | Risco específico coberto pelo seguro                                      |
| **Renovação**      | Processo de emissão de nova apólice ao término da vigência da anterior    |
| **SUSEP**          | Superintendência de Seguros Privados — órgão regulador                    |
| **Sinistralidade** | Relação entre sinistros pagos e prêmios recebidos (loss ratio)            |
| **Corretor**       | Profissional habilitado pela SUSEP para intermediar seguros               |

---

## 11. Observações Finais

- O projeto prioriza simplicidade e pragmatismo — usar o máximo possível dos recursos nativos do Django antes de recorrer a libs externas.
- O SQLite é suficiente para operações de uma corretora de pequeno a médio porte. Caso o volume cresça significativamente, a migração para PostgreSQL é trivial com Django.
- O design system é a fonte de verdade para toda decisão visual — nenhum componente deve ser criado sem referência ao `design-system.html`.
- Signals devem ser usados com parcimônia e sempre documentados, mantidos em `signals.py` da app correspondente e registrados no `apps.py` via `ready()`.
- Todo model registrado no Django Admin para facilitar debug e gestão emergencial.
- O ambiente virtual do projeto é .venv e deve ser sempre utilizado.