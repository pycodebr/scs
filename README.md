# 🛡️ SCS — Sistema de Corretora de Seguros

Sistema completo de gestão para corretoras de seguros, desenvolvido em Django. Abrange desde o cadastro de clientes e seguradoras até o CRM de vendas, controle de sinistros, renovações, endossos e relatórios gerenciais.

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução Local](#-instalação-e-execução-local)
- [Seed de Dados Demo](#-seed-de-dados-demo)
- [Usuários e Senhas de Teste](#-usuários-e-senhas-de-teste)
- [Papéis e Permissões](#-papéis-e-permissões)
- [Licença](#-licença)

---

## ✨ Funcionalidades

### Cadastros
- **Clientes** — Pessoas Físicas e Jurídicas com dados completos (endereço, contato, documentos)
- **Seguradoras** — Cadastro com código SUSEP, ramos e contatos
- **Coberturas** — Tipos de seguro, coberturas e itens de cobertura

### Operações
- **Propostas** — Ciclo completo: rascunho → enviada → em análise → aprovada/recusada
- **Apólices** — Gestão de vigência, prêmios, parcelas, comissões e documentos
- **Sinistros** — Abertura, acompanhamento, timeline de eventos e documentação
- **Endossos** — Inclusão, exclusão, alteração, cancelamento e transferência
- **Renovações** — Controle de vencimentos com alertas de urgência e atraso

### Comercial
- **CRM / Kanban** — Pipeline visual com drag-and-drop (SortableJS), filtros por prioridade e corretor
- **Negociações** — CRUD completo com atividades (notas, ligações, emails, reuniões, tarefas)
- **Pipelines** — Gestão de etapas customizáveis com cores e marcação de ganho/perda

### Análise
- **Dashboard** — KPIs, gráficos de produção mensal, distribuição por tipo/seguradora, sinistros
- **Relatórios** — 10 relatórios com filtros, exportação CSV e PDF:
  - Produção por Período
  - Comissões por Corretor
  - Carteira por Seguradora
  - Carteira por Tipo de Seguro
  - Sinistros por Período
  - Sinistralidade (Loss Ratio)
  - Renovações Pendentes
  - Clientes por Corretor
  - Funil CRM
  - Endossos por Período

### Administração
- **Usuários** — CRUD com papéis (Admin, Gerente, Corretor)
- **Perfil** — Edição de dados pessoais e troca de senha

### UI/UX
- Tema DuralUX com design system completo
- Modo Dark/Light com toggle
- Sidebar com navegação ativa e permissões por papel
- Tabelas responsivas, filtros e busca em todas as listas
- Badges de status com cores semânticas

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12+ / Django 6.0 |
| Banco de Dados | SQLite (dev) |
| Frontend | Bootstrap 5 / DuralUX Template |
| Gráficos | Chart.js 4 |
| Drag & Drop | SortableJS |
| PDF Export | xhtml2pdf |
| Form Rendering | django-widget-tweaks |
| Imagens | Pillow |

---

## 📁 Estrutura do Projeto

```
scs/
├── accounts/          # Autenticação, usuários e perfis
├── claims/            # Sinistros e documentos
├── clients/           # Clientes (PF/PJ)
├── core/              # Settings, URLs raiz, WSGI
├── coverages/         # Tipos de seguro e coberturas
├── crm/               # Pipeline, negociações (deals) e atividades
├── dashboard/         # Dashboard com KPIs e gráficos
├── design_system/     # Documentação do design system
├── endorsements/      # Endossos
├── insurers/          # Seguradoras e ramos
├── policies/          # Propostas e apólices
├── renewals/          # Renovações
├── reports/           # Relatórios gerenciais (10 tipos)
├── static/            # CSS, JS, imagens, fontes
├── templates/         # Templates Django (base, partials, por app)
├── utils/             # Mixins, validators, template tags, management commands
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📦 Pré-requisitos

- **Python** 3.12 ou superior
- **pip** (gerenciador de pacotes Python)
- **Git** (opcional, para clonar o repositório)

---

## 🚀 Instalação e Execução Local

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd scs
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto usando o `.env.example` como base:

```bash
cp .env.example .env
```

Edite o `.env` e preencha com suas credenciais:

```env
OPENAI_API_KEY=sua-chave-de-api-da-openai
OPENAI_MODEL=gpt-5.4
```

- `OPENAI_API_KEY` — Chave de API da OpenAI (obrigatória para funcionalidades de IA)
- `OPENAI_MODEL` — Modelo a ser utilizado (padrão: `gpt-5.4`)

### 5. Execute as migrações

```bash
python manage.py migrate
```

### 6. Popule com dados de demonstração (opcional, recomendado)

```bash
python manage.py seed_demo
```

> 💡 Isso cria automaticamente os usuários de teste, seguradoras, clientes, apólices e todos os dados necessários para uma demonstração funcional. Veja a seção [Seed de Dados Demo](#-seed-de-dados-demo) para mais detalhes.

### 7. Gere os insights de IA (opcional, requer `.env` configurado)

```bash
python manage.py generate_insights
```

Este comando gera insights personalizados no dashboard de cada usuário usando IA. Pode ser executado periodicamente para manter os insights atualizados.

```bash
# Gerar apenas para um usuário específico
python manage.py generate_insights --user_id 1
```

### 8. Inicie o servidor de desenvolvimento

```bash
python manage.py runserver
```

### 9. Acesse no navegador

```
http://localhost:8000
```

Você será redirecionado para a tela de login. Use as credenciais da seção [Usuários e Senhas de Teste](#-usuários-e-senhas-de-teste).

---

## 🌱 Seed de Dados Demo

O comando `seed_demo` cria um conjunto completo de dados realistas para demonstração:

```bash
# Primeira execução — cria todos os dados
python manage.py seed_demo

# Re-executar limpando dados anteriores
python manage.py seed_demo --clear
```

### O que é criado

| Entidade | Quantidade | Detalhes |
|----------|-----------|----------|
| Usuários | 5 | 1 Admin, 1 Gerente, 3 Corretores |
| Tipos de Seguro | 8 | Auto, Vida, Residencial, Empresarial, Saúde, Viagem, RC, Transporte |
| Coberturas | ~50 | Distribuídas por tipo de seguro |
| Seguradoras | 8 | Porto Seguro, SulAmérica, Bradesco, Allianz, Tokio Marine, HDI, Mapfre, Liberty |
| Clientes | 20 | 12 Pessoa Física + 8 Pessoa Jurídica |
| Propostas | 28 | 20 aprovadas, 5 rejeitadas, 3 pendentes/em análise |
| Apólices | 20 | Ativas, vencidas e canceladas nos últimos 12 meses |
| Sinistros | 8 | Abertos, em análise, aprovados, pagos e negados |
| Endossos | 6 | Inclusão, exclusão, alteração, cancelamento, transferência |
| Renovações | 10 | Pendentes, contatadas, cotação enviada, renovadas, não renovadas |
| Pipelines CRM | 2 | "Novos Negócios" (7 etapas) e "Renovações" (5 etapas) |
| Negociações | 15 | Distribuídas em todas as etapas do pipeline |
| Atividades | ~40 | Notas, ligações, emails, reuniões e tarefas |

> ⚠️ A flag `--clear` **remove todos os dados** (exceto superusuários) antes de recriar. Use com cuidado em ambientes com dados reais.

---

## 🔑 Usuários e Senhas de Teste

Criados automaticamente pelo `seed_demo`:

| Nome | Email | Senha | Papel |
|------|-------|-------|-------|
| Administrador SCS | `admin@scs.com` | `admin123` | Admin |
| Maria Oliveira | `gerente@scs.com` | `gerente123` | Gerente (Manager) |
| Carlos Silva | `carlos@scs.com` | `corretor123` | Corretor (Broker) |
| Ana Santos | `ana@scs.com` | `corretor123` | Corretor (Broker) |
| Rafael Pereira | `rafael@scs.com` | `corretor123` | Corretor (Broker) |

> 💡 Para testar as diferenças de permissão, faça login como **Admin** (acesso total), depois como **Corretor** (acesso restrito aos próprios dados).

---

## 🔒 Papéis e Permissões

O sistema possui 3 papéis com níveis de acesso distintos:

### Admin
- ✅ Acesso total a todas as funcionalidades
- ✅ Gestão de usuários
- ✅ Todos os relatórios
- ✅ Gestão de pipelines CRM
- ✅ Visualiza dados de todos os corretores

### Gerente (Manager)
- ✅ Acesso a todas as funcionalidades operacionais
- ✅ Gestão de usuários
- ✅ Todos os relatórios
- ✅ Gestão de pipelines CRM
- ✅ Visualiza dados de todos os corretores

### Corretor (Broker)
- ✅ Cadastro e gestão de clientes (apenas os seus)
- ✅ Propostas, apólices, sinistros, endossos e renovações (apenas os seus)
- ✅ CRM Kanban e negociações (apenas as suas)
- ❌ **Sem acesso** a relatórios gerenciais
- ❌ **Sem acesso** a gestão de pipelines
- ❌ **Sem acesso** a gestão de usuários

---

## 📄 Licença

Este projeto é privado e de uso interno.
