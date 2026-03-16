from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from billing.models import (
    BillingCycle,
    BillingPaymentMethod,
    PaymentRecord,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
)
from billing.services import bootstrap_catalog
from brokerages.models import Brokerage, BrokerageStatus
from brokerages.services import sync_brokerage_modules

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração compatíveis com o SaaS multi-tenant.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove os dados existentes antes de semear o ambiente.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Limpando dados existentes...')
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando seed multi-tenant do SCS...'))
        plans = {plan.slug: plan for plan in bootstrap_catalog()}
        brokerage = self._create_brokerage()
        users = self._create_users(brokerage)
        self._create_subscription(brokerage, plans['smart'])
        insurance_types = self._create_insurance_types(brokerage)
        insurers = self._create_insurers(brokerage)
        clients = self._create_clients(brokerage, users)
        policies = self._create_policies(brokerage, users, clients, insurers, insurance_types)
        self._create_claims(brokerage, users, policies)
        self._create_endorsements(brokerage, users, policies)
        self._create_renewals(brokerage, users, policies, insurers)
        self._create_crm_data(brokerage, users, clients, insurers, insurance_types, policies)

        self.stdout.write(self.style.SUCCESS('\nSeed concluído com sucesso.'))
        self.stdout.write(self.style.WARNING('\nCredenciais de acesso:'))
        self.stdout.write('  Plataforma: plataforma@scs.com / admin123')
        self.stdout.write('  Admin tenant: admin@demo-corretora.com / admin123')
        self.stdout.write('  Gerente: gerente@demo-corretora.com / gerente123')
        self.stdout.write('  Corretor: carlos@demo-corretora.com / corretor123')
        self.stdout.write('  Corretor: ana@demo-corretora.com / corretor123')

    def _clear_data(self):
        from ai_agent.models import ChatMessage, ChatSession, DashboardInsight, EntitySummary
        from brokerages.models import BrokerageModule
        from claims.models import Claim, ClaimDocument, ClaimTimeline
        from clients.models import Client
        from coverages.models import Coverage, CoverageItem, InsuranceType
        from crm.models import Deal, DealActivity, Pipeline, PipelineStage
        from endorsements.models import Endorsement, EndorsementDocument
        from insurers.models import Insurer, InsurerBranch
        from policies.models import Policy, PolicyCoverage, PolicyDocument, Proposal
        from renewals.models import Renewal

        DealActivity.objects.all().delete()
        Deal.objects.all().delete()
        PipelineStage.objects.all().delete()
        Pipeline.objects.all().delete()
        Renewal.objects.all().delete()
        EndorsementDocument.objects.all().delete()
        Endorsement.objects.all().delete()
        ClaimTimeline.objects.all().delete()
        ClaimDocument.objects.all().delete()
        Claim.objects.all().delete()
        PolicyDocument.objects.all().delete()
        PolicyCoverage.objects.all().delete()
        Policy.objects.all().delete()
        Proposal.objects.all().delete()
        Client.objects.all().delete()
        InsurerBranch.objects.all().delete()
        Insurer.objects.all().delete()
        CoverageItem.objects.all().delete()
        Coverage.objects.all().delete()
        InsuranceType.objects.all().delete()
        ChatMessage.objects.all().delete()
        ChatSession.objects.all().delete()
        DashboardInsight.objects.all().delete()
        EntitySummary.objects.all().delete()
        PaymentRecord.objects.all().delete()
        Subscription.objects.all().delete()
        BrokerageModule.objects.all().delete()
        User.objects.all().delete()
        Brokerage.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('  Dados removidos.'))

    def _create_brokerage(self):
        brokerage, _ = Brokerage.objects.update_or_create(
            cnpj='12.345.678/0001-90',
            defaults={
                'legal_name': 'Demo Corretora de Seguros LTDA',
                'trade_name': 'Demo Corretora',
                'email': 'contato@demo-corretora.com',
                'phone': '(11) 4000-1020',
                'zip_code': '01310-100',
                'street': 'Avenida Paulista',
                'number': '1000',
                'complement': '11 andar',
                'neighborhood': 'Bela Vista',
                'city': 'Sao Paulo',
                'state': 'SP',
                'status': BrokerageStatus.ACTIVE,
                'notes': 'Tenant de demonstração do SCS.',
            },
        )
        return brokerage

    def _create_users(self, brokerage):
        platform_admin, _ = User.objects.update_or_create(
            email='plataforma@scs.com',
            defaults={
                'first_name': 'Plataforma',
                'last_name': 'SCS',
                'role': 'admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'is_platform_admin': True,
                'brokerage': None,
            },
        )
        platform_admin.set_password('admin123')
        platform_admin.save()

        admin_user, _ = User.objects.update_or_create(
            email='admin@demo-corretora.com',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Tenant',
                'role': 'admin',
                'is_active': True,
                'brokerage': brokerage,
                'phone': '(11) 99999-0001',
            },
        )
        admin_user.set_password('admin123')
        admin_user.save()

        manager_user, _ = User.objects.update_or_create(
            email='gerente@demo-corretora.com',
            defaults={
                'first_name': 'Marina',
                'last_name': 'Oliveira',
                'role': 'manager',
                'is_active': True,
                'brokerage': brokerage,
                'phone': '(11) 99999-0002',
            },
        )
        manager_user.set_password('gerente123')
        manager_user.save()

        brokers = []
        for email, first_name, last_name in (
            ('carlos@demo-corretora.com', 'Carlos', 'Silva'),
            ('ana@demo-corretora.com', 'Ana', 'Souza'),
        ):
            broker, _ = User.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'broker',
                    'is_active': True,
                    'brokerage': brokerage,
                },
            )
            broker.set_password('corretor123')
            broker.save()
            brokers.append(broker)

        self.stdout.write(self.style.SUCCESS('  Usuários da plataforma e da corretora criados.'))
        return {
            'platform_admin': platform_admin,
            'admin': admin_user,
            'manager': manager_user,
            'brokers': brokers,
        }

    def _create_subscription(self, brokerage, plan):
        today = timezone.localdate()
        subscription, _ = Subscription.objects.update_or_create(
            brokerage=brokerage,
            plan=plan,
            defaults={
                'status': SubscriptionStatus.ACTIVE,
                'billing_cycle': BillingCycle.MONTHLY,
                'price_per_user': plan.monthly_price_per_user,
                'active_user_count': brokerage.users.filter(is_active=True).count(),
                'started_at': today - timedelta(days=10),
                'trial_ends_at': None,
                'next_billing_at': today + timedelta(days=20),
                'cancelled_at': None,
            },
        )
        Subscription.objects.filter(brokerage=brokerage).exclude(pk=subscription.pk).delete()
        PaymentRecord.objects.update_or_create(
            subscription=subscription,
            due_date=today - timedelta(days=10),
            defaults={
                'status': PaymentStatus.PAID,
                'amount': plan.monthly_price_per_user * subscription.active_user_count,
                'payment_method': BillingPaymentMethod.MANUAL,
                'paid_at': timezone.now() - timedelta(days=8),
                'reference_code': 'DEMO-PAY-001',
                'notes': 'Pagamento de demonstração registrado manualmente.',
            },
        )
        brokerage.status = BrokerageStatus.ACTIVE
        brokerage.save(update_fields=['status', 'updated_at'])
        sync_brokerage_modules(brokerage, plan, granted_by=brokerage.users.filter(role='admin').first())
        self.stdout.write(self.style.SUCCESS(f'  Assinatura "{plan.name}" configurada para a corretora.'))

    def _create_insurance_types(self, brokerage):
        from coverages.models import Coverage, CoverageItem, InsuranceType

        types_data = {
            'Automovel': ['Colisao', 'Roubo e Furto', 'Assistencia 24h'],
            'Residencial': ['Incendio', 'Danos Eletricos', 'Responsabilidade Civil'],
            'Empresarial': ['Incendio', 'Equipamentos', 'Lucros Cessantes'],
        }

        insurance_types = {}
        for type_name, coverages in types_data.items():
            insurance_type, _ = InsuranceType.objects.update_or_create(
                brokerage=brokerage,
                name=type_name,
                defaults={
                    'description': f'Carteira {type_name.lower()} da corretora demo.',
                    'is_active': True,
                },
            )
            insurance_types[type_name] = insurance_type

            for coverage_name in coverages:
                coverage, _ = Coverage.objects.update_or_create(
                    brokerage=brokerage,
                    insurance_type=insurance_type,
                    name=coverage_name,
                    defaults={
                        'description': f'Cobertura {coverage_name.lower()}.',
                        'is_active': True,
                    },
                )
                CoverageItem.objects.get_or_create(
                    brokerage=brokerage,
                    coverage=coverage,
                    name=f'{coverage_name} basica',
                    defaults={'description': 'Item padrão de demonstração.', 'is_active': True},
                )

        self.stdout.write(self.style.SUCCESS('  Ramos e coberturas criados.'))
        return insurance_types

    def _create_insurers(self, brokerage):
        from insurers.models import Insurer

        insurers = []
        for name, cnpj, email in (
            ('Porto Seguro', '61.198.164/0001-60', 'atendimento@porto-demo.com'),
            ('SulAmerica', '33.000.167/0001-59', 'atendimento@sulamerica-demo.com'),
            ('Allianz', '61.573.796/0001-66', 'atendimento@allianz-demo.com'),
        ):
            insurer, _ = Insurer.objects.update_or_create(
                brokerage=brokerage,
                cnpj=cnpj,
                defaults={
                    'name': name,
                    'email': email,
                    'phone': '(11) 3000-0000',
                    'city': 'Sao Paulo',
                    'state': 'SP',
                    'is_active': True,
                },
            )
            insurers.append(insurer)

        self.stdout.write(self.style.SUCCESS('  Seguradoras criadas.'))
        return insurers

    def _create_clients(self, brokerage, users):
        from clients.models import Client

        brokers = users['brokers']
        client_specs = (
            ('Joao Mendes', '123.456.789-01', 'pf', 'joao@cliente-demo.com', brokers[0]),
            ('Marina Costa', '234.567.890-12', 'pf', 'marina@cliente-demo.com', brokers[1]),
            ('Construtora Horizonte LTDA', '45.678.901/0001-33', 'pj', 'contato@horizonte-demo.com', brokers[0]),
            ('Clinica Vida Plena', '67.890.123/0001-55', 'pj', 'contato@vida-plena-demo.com', brokers[1]),
        )

        clients = []
        for index, (name, cpf_cnpj, client_type, email, broker) in enumerate(client_specs, start=1):
            client, _ = Client.objects.update_or_create(
                brokerage=brokerage,
                cpf_cnpj=cpf_cnpj,
                defaults={
                    'name': name,
                    'client_type': client_type,
                    'email': email,
                    'phone': f'(11) 99999-10{index:02d}',
                    'city': 'Sao Paulo',
                    'state': 'SP',
                    'broker': broker,
                    'is_active': True,
                },
            )
            clients.append(client)

        self.stdout.write(self.style.SUCCESS('  Clientes criados.'))
        return clients

    def _create_policies(self, brokerage, users, clients, insurers, insurance_types):
        from policies.models import Policy, PolicyCoverage, Proposal

        coverages_by_type = {
            insurance_type.name: list(insurance_type.coverages.filter(brokerage=brokerage)[:2])
            for insurance_type in insurance_types.values()
        }
        policies = []

        for index, client in enumerate(clients, start=1):
            if client.client_type == 'pf':
                insurance_type = insurance_types['Automovel']
            elif 'Clinica' in client.name:
                insurance_type = insurance_types['Empresarial']
            else:
                insurance_type = insurance_types['Residencial']

            insurer = insurers[(index - 1) % len(insurers)]
            broker = client.broker
            proposal, _ = Proposal.objects.update_or_create(
                brokerage=brokerage,
                proposal_number=f'PRP-{index:04d}',
                defaults={
                    'client': client,
                    'insurer': insurer,
                    'insurance_type': insurance_type,
                    'broker': broker,
                    'status': 'approved',
                    'submission_date': timezone.localdate() - timedelta(days=30 - index),
                    'response_date': timezone.localdate() - timedelta(days=25 - index),
                    'premium_amount': Decimal('1800.00') + Decimal(index * 250),
                    'notes': 'Proposta aprovada na base de demonstração.',
                },
            )
            policy, _ = Policy.objects.update_or_create(
                brokerage=brokerage,
                policy_number=f'POL-{index:04d}',
                defaults={
                    'proposal': proposal,
                    'client': client,
                    'insurer': insurer,
                    'insurance_type': insurance_type,
                    'broker': broker,
                    'status': 'active',
                    'start_date': timezone.localdate() - timedelta(days=20),
                    'end_date': timezone.localdate() + timedelta(days=120 - (index * 5)),
                    'premium_amount': Decimal('2400.00') + Decimal(index * 300),
                    'insured_amount': Decimal('150000.00') + Decimal(index * 10000),
                    'commission_rate': Decimal('12.50'),
                    'commission_amount': Decimal('300.00') + Decimal(index * 45),
                    'installments': 6,
                    'payment_method': 'pix',
                    'notes': 'Apolice ativa para demonstração.',
                },
            )
            for coverage in coverages_by_type.get(insurance_type.name, []):
                PolicyCoverage.objects.update_or_create(
                    brokerage=brokerage,
                    policy=policy,
                    coverage=coverage,
                    defaults={
                        'insured_amount': Decimal('50000.00'),
                        'deductible': Decimal('1500.00'),
                        'premium_amount': Decimal('250.00'),
                        'notes': 'Cobertura adicionada automaticamente ao seed.',
                    },
                )
            policies.append(policy)

        self.stdout.write(self.style.SUCCESS('  Propostas, apolices e coberturas contratadas criadas.'))
        return policies

    def _create_claims(self, brokerage, users, policies):
        from claims.models import Claim, ClaimTimeline

        for index, policy in enumerate(policies[:2], start=1):
            claim, _ = Claim.objects.update_or_create(
                brokerage=brokerage,
                claim_number=f'SIN-{index:04d}',
                defaults={
                    'policy': policy,
                    'client': policy.client,
                    'status': 'under_analysis',
                    'occurrence_date': timezone.localdate() - timedelta(days=12 * index),
                    'notification_date': timezone.localdate() - timedelta(days=11 * index),
                    'description': 'Evento monitorado pela equipe de sinistros da corretora demo.',
                    'location': 'Sao Paulo/SP',
                    'claimed_amount': Decimal('12000.00') + Decimal(index * 1500),
                    'broker': policy.broker,
                },
            )
            ClaimTimeline.objects.update_or_create(
                brokerage=brokerage,
                claim=claim,
                action='Abertura do sinistro',
                defaults={
                    'performed_by': users['manager'],
                    'old_status': '',
                    'new_status': claim.status,
                    'notes': 'Sinistro aberto automaticamente no seed.',
                },
            )

        self.stdout.write(self.style.SUCCESS('  Sinistros criados.'))

    def _create_endorsements(self, brokerage, users, policies):
        from endorsements.models import Endorsement

        for index, policy in enumerate(policies[:2], start=1):
            Endorsement.objects.update_or_create(
                brokerage=brokerage,
                endorsement_number=f'END-{index:04d}',
                defaults={
                    'policy': policy,
                    'endorsement_type': 'modification',
                    'status': 'approved',
                    'request_date': timezone.localdate() - timedelta(days=8 * index),
                    'effective_date': timezone.localdate() - timedelta(days=7 * index),
                    'description': 'Ajuste de limite e atualização cadastral.',
                    'premium_difference': Decimal('180.00'),
                    'requested_by': users['admin'],
                    'notes': 'Endosso de demonstração.',
                },
            )

        self.stdout.write(self.style.SUCCESS('  Endossos criados.'))

    def _create_renewals(self, brokerage, users, policies, insurers):
        from renewals.models import Renewal

        for index, policy in enumerate(policies[-2:], start=1):
            Renewal.objects.update_or_create(
                brokerage=brokerage,
                policy=policy,
                defaults={
                    'status': 'contacted' if index == 1 else 'pending',
                    'due_date': policy.end_date - timedelta(days=20),
                    'contact_date': timezone.localdate() - timedelta(days=2) if index == 1 else None,
                    'new_premium': policy.premium_amount + Decimal('220.00'),
                    'new_insurer': insurers[index % len(insurers)],
                    'broker': policy.broker,
                    'notes': 'Renovação acompanhada pela corretora demo.',
                },
            )

        self.stdout.write(self.style.SUCCESS('  Renovações criadas.'))

    def _create_crm_data(self, brokerage, users, clients, insurers, insurance_types, policies):
        from crm.models import Deal, DealActivity, Pipeline, PipelineStage

        pipeline, _ = Pipeline.objects.update_or_create(
            brokerage=brokerage,
            name='Pipeline Comercial',
            defaults={'is_default': True, 'is_active': True},
        )
        stage_specs = (
            ('Lead Qualificado', 1, '#0d6efd', False, False),
            ('Proposta Enviada', 2, '#f59e0b', False, False),
            ('Fechado', 3, '#16a34a', True, False),
            ('Perdido', 4, '#dc2626', False, True),
        )
        stages = {}
        for name, order, color, is_won, is_lost in stage_specs:
            stage, _ = PipelineStage.objects.update_or_create(
                brokerage=brokerage,
                pipeline=pipeline,
                name=name,
                defaults={
                    'order': order,
                    'color': color,
                    'is_won': is_won,
                    'is_lost': is_lost,
                },
            )
            stages[name] = stage

        for index, client in enumerate(clients, start=1):
            insurance_type = policies[index - 1].insurance_type
            insurer = insurers[(index - 1) % len(insurers)]
            stage = stages['Fechado'] if index == 1 else stages['Proposta Enviada']
            deal, _ = Deal.objects.update_or_create(
                brokerage=brokerage,
                title=f'Negociacao {client.name}',
                defaults={
                    'client': client,
                    'broker': client.broker,
                    'pipeline': pipeline,
                    'stage': stage,
                    'insurance_type': insurance_type,
                    'insurer': insurer,
                    'expected_value': Decimal('3500.00') + Decimal(index * 400),
                    'expected_close_date': timezone.localdate() + timedelta(days=10 * index),
                    'priority': 'high' if index == 1 else 'medium',
                    'source': 'website' if index % 2 else 'referral',
                    'proposal': policies[index - 1].proposal,
                    'policy': policies[index - 1] if stage.is_won else None,
                    'notes': 'Deal gerado para demonstrar o funil comercial tenant-scoped.',
                },
            )
            DealActivity.objects.update_or_create(
                brokerage=brokerage,
                deal=deal,
                title='Contato inicial realizado',
                defaults={
                    'activity_type': 'call',
                    'description': 'Cliente contatado e oportunidade registrada no CRM.',
                    'due_date': timezone.now() - timedelta(days=1),
                    'is_completed': True,
                    'performed_by': users['manager'],
                },
            )

        self.stdout.write(self.style.SUCCESS('  Pipeline, negociações e atividades de CRM criados.'))
