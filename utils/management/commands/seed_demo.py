import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração para o SCS.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove todos os dados antes de semear.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Limpando dados existentes...')
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando seed de dados de demonstração...'))

        users = self._create_users()
        insurance_types = self._create_insurance_types()
        insurers = self._create_insurers()
        clients = self._create_clients(users)
        policies = self._create_policies(clients, insurers, insurance_types, users)
        self._create_claims(policies, users)
        self._create_endorsements(policies, users)
        self._create_renewals(policies, users, insurers)
        self._create_crm_data(clients, users, insurance_types, insurers)

        self.stdout.write(self.style.SUCCESS('\n✅ Seed de dados concluído com sucesso!'))
        self.stdout.write(self.style.WARNING('\nCredenciais de acesso:'))
        self.stdout.write('  Admin:   admin@scs.com / admin123')
        self.stdout.write('  Gerente: gerente@scs.com / gerente123')
        self.stdout.write('  Corretor: carlos@scs.com / corretor123')
        self.stdout.write('  Corretor: ana@scs.com / corretor123')
        self.stdout.write('  Corretor: rafael@scs.com / corretor123')

    def _clear_data(self):
        from crm.models import DealActivity, Deal, PipelineStage, Pipeline
        from renewals.models import Renewal
        from endorsements.models import EndorsementDocument, Endorsement
        from claims.models import ClaimTimeline, ClaimDocument, Claim
        from policies.models import PolicyDocument, PolicyCoverage, Policy, Proposal
        from clients.models import Client
        from insurers.models import InsurerBranch, Insurer
        from coverages.models import CoverageItem, Coverage, InsuranceType

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
        Renewal.objects.all().delete()
        Client.objects.all().delete()
        InsurerBranch.objects.all().delete()
        Insurer.objects.all().delete()
        CoverageItem.objects.all().delete()
        Coverage.objects.all().delete()
        InsuranceType.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('  Dados limpos.'))

    def _create_users(self):
        self.stdout.write('Criando usuários...')
        users = {}

        admin, _ = User.objects.update_or_create(
            email='admin@scs.com',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'SCS',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        admin.set_password('admin123')
        admin.save()
        users['admin'] = admin

        manager, _ = User.objects.update_or_create(
            email='gerente@scs.com',
            defaults={
                'first_name': 'Maria',
                'last_name': 'Oliveira',
                'role': 'manager',
                'is_staff': True,
                'is_active': True,
            },
        )
        manager.set_password('gerente123')
        manager.save()
        users['manager'] = manager

        broker_data = [
            ('carlos@scs.com', 'Carlos', 'Silva'),
            ('ana@scs.com', 'Ana', 'Santos'),
            ('rafael@scs.com', 'Rafael', 'Pereira'),
        ]
        users['brokers'] = []
        for email, first, last in broker_data:
            broker, _ = User.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'role': 'broker',
                    'is_active': True,
                },
            )
            broker.set_password('corretor123')
            broker.save()
            users['brokers'].append(broker)

        self.stdout.write(self.style.SUCCESS(f'  {len(users["brokers"]) + 2} usuários criados.'))
        return users

    def _create_insurance_types(self):
        self.stdout.write('Criando tipos de seguro e coberturas...')
        from coverages.models import InsuranceType, Coverage

        types_data = {
            'Automóvel': [
                'Colisão', 'Roubo e Furto', 'Incêndio', 'Terceiros',
                'Danos Materiais', 'Danos Corporais', 'Assistência 24h', 'Vidros',
            ],
            'Vida Individual': [
                'Morte Natural', 'Morte Acidental', 'Invalidez Permanente',
                'Invalidez Funcional', 'Doenças Graves', 'Diária por Incapacidade',
            ],
            'Residencial': [
                'Incêndio', 'Raio', 'Explosão', 'Roubo e Furto',
                'Danos Elétricos', 'Responsabilidade Civil', 'Vendaval',
            ],
            'Empresarial': [
                'Incêndio', 'Roubo', 'Responsabilidade Civil',
                'Equipamentos', 'Lucros Cessantes', 'Danos Elétricos',
            ],
            'Saúde': [
                'Consultas', 'Exames', 'Internação', 'Cirurgias',
                'Pronto Socorro', 'Obstetrícia',
            ],
            'Viagem': [
                'Despesas Médicas', 'Bagagem', 'Cancelamento de Viagem',
                'Assistência Jurídica', 'Regresso Antecipado',
            ],
            'Responsabilidade Civil': [
                'RC Profissional', 'RC Operações', 'RC Produtos',
                'RC Empregador', 'RC Ambiental',
            ],
            'Transporte': [
                'Carga Nacional', 'Carga Internacional', 'Responsabilidade Civil Transportes',
                'Lucros Esperados', 'Frete',
            ],
        }

        insurance_types = {}
        for type_name, coverages in types_data.items():
            it, _ = InsuranceType.objects.update_or_create(
                name=type_name,
                defaults={'is_active': True},
            )
            insurance_types[type_name] = it
            for cov_name in coverages:
                Coverage.objects.update_or_create(
                    insurance_type=it,
                    name=cov_name,
                    defaults={'is_active': True},
                )

        self.stdout.write(self.style.SUCCESS(f'  {len(insurance_types)} tipos de seguro criados.'))
        return insurance_types

    def _create_insurers(self):
        self.stdout.write('Criando seguradoras...')
        from insurers.models import Insurer

        insurers_data = [
            ('Porto Seguro', '61.198.164/0001-60', '06050', 'atendimento@portoseguro.com.br', '(11) 3366-3000', 'São Paulo', 'SP'),
            ('SulAmérica', '33.000.167/0001-59', '06190', 'contato@sulamerica.com.br', '(21) 3503-4000', 'Rio de Janeiro', 'RJ'),
            ('Bradesco Seguros', '33.055.146/0001-90', '05886', 'seguros@bradesco.com.br', '(11) 3003-1010', 'São Paulo', 'SP'),
            ('Allianz Seguros', '61.573.796/0001-66', '05495', 'contato@allianz.com.br', '(11) 3370-1515', 'São Paulo', 'SP'),
            ('Tokio Marine', '33.164.021/0001-00', '06840', 'atendimento@tokiomarine.com.br', '(11) 3054-7100', 'São Paulo', 'SP'),
            ('HDI Seguros', '29.980.158/0001-57', '05746', 'atendimento@hdi.com.br', '(11) 3054-3500', 'São Paulo', 'SP'),
            ('Mapfre Seguros', '61.074.175/0001-38', '05765', 'contato@mapfre.com.br', '(11) 4004-7500', 'São Paulo', 'SP'),
            ('Liberty Seguros', '61.550.141/0001-72', '05765', 'contato@libertyseguros.com.br', '(11) 3003-2442', 'São Paulo', 'SP'),
        ]
        insurers = []
        for name, cnpj, susep, email, phone, city, state in insurers_data:
            ins, _ = Insurer.objects.update_or_create(
                cnpj=cnpj,
                defaults={
                    'name': name,
                    'susep_code': susep,
                    'email': email,
                    'phone': phone,
                    'city': city,
                    'state': state,
                    'is_active': True,
                },
            )
            insurers.append(ins)

        self.stdout.write(self.style.SUCCESS(f'  {len(insurers)} seguradoras criadas.'))
        return insurers

    def _create_clients(self, users):
        self.stdout.write('Criando clientes...')
        from clients.models import Client

        brokers = users['brokers']
        clients_data = [
            # (name, cpf_cnpj, type, email, phone, city, state, broker_idx)
            ('João Mendes', '123.456.789-01', 'pf', 'joao.mendes@email.com', '(11) 99999-1001', 'São Paulo', 'SP', 0),
            ('Maria Clara Ferreira', '234.567.890-12', 'pf', 'maria.clara@email.com', '(11) 99999-1002', 'São Paulo', 'SP', 0),
            ('Pedro Henrique Alves', '345.678.901-23', 'pf', 'pedro.alves@email.com', '(21) 99999-1003', 'Rio de Janeiro', 'RJ', 0),
            ('Luciana Barbosa', '456.789.012-34', 'pf', 'luciana.barbosa@email.com', '(31) 99999-1004', 'Belo Horizonte', 'MG', 1),
            ('Roberto Costa Neto', '567.890.123-45', 'pf', 'roberto.costa@email.com', '(41) 99999-1005', 'Curitiba', 'PR', 1),
            ('Fernanda Dias', '678.901.234-56', 'pf', 'fernanda.dias@email.com', '(51) 99999-1006', 'Porto Alegre', 'RS', 1),
            ('André Luiz Martins', '789.012.345-67', 'pf', 'andre.martins@email.com', '(61) 99999-1007', 'Brasília', 'DF', 2),
            ('Camila Rocha', '890.123.456-78', 'pf', 'camila.rocha@email.com', '(71) 99999-1008', 'Salvador', 'BA', 2),
            ('Gustavo Lopes', '901.234.567-89', 'pf', 'gustavo.lopes@email.com', '(85) 99999-1009', 'Fortaleza', 'CE', 2),
            ('Patrícia Souza Lima', '012.345.678-90', 'pf', 'patricia.souza@email.com', '(11) 99999-1010', 'Santos', 'SP', 0),
            ('Felipe Augusto Silva', '111.222.333-44', 'pf', 'felipe.augusto@email.com', '(11) 99999-1011', 'Campinas', 'SP', 1),
            ('Bianca Vieira', '222.333.444-55', 'pf', 'bianca.vieira@email.com', '(21) 99999-1012', 'Niterói', 'RJ', 2),
            ('Tech Solutions LTDA', '12.345.678/0001-00', 'pj', 'contato@techsolutions.com.br', '(11) 3000-0001', 'São Paulo', 'SP', 0),
            ('Comércio Nacional S.A.', '23.456.789/0001-11', 'pj', 'contato@comercionacional.com.br', '(11) 3000-0002', 'São Paulo', 'SP', 0),
            ('Transportes Rápidos LTDA', '34.567.890/0001-22', 'pj', 'contato@transportesrapidos.com.br', '(21) 3000-0003', 'Rio de Janeiro', 'RJ', 1),
            ('Construtora Horizonte', '45.678.901/0001-33', 'pj', 'contato@construtora.com.br', '(31) 3000-0004', 'Belo Horizonte', 'MG', 1),
            ('Restaurante Sabor & Arte', '56.789.012/0001-44', 'pj', 'contato@saborarte.com.br', '(41) 3000-0005', 'Curitiba', 'PR', 2),
            ('Clínica Vida Plena', '67.890.123/0001-55', 'pj', 'contato@vidaplena.com.br', '(51) 3000-0006', 'Porto Alegre', 'RS', 0),
            ('Indústria Metalmax', '78.901.234/0001-66', 'pj', 'contato@metalmax.com.br', '(11) 3000-0007', 'Guarulhos', 'SP', 1),
            ('Escola Futuro Brilhante', '89.012.345/0001-77', 'pj', 'contato@futurobrilhante.com.br', '(71) 3000-0008', 'Salvador', 'BA', 2),
        ]

        clients = []
        for name, cpf_cnpj, ctype, email, phone, city, state, broker_idx in clients_data:
            client, _ = Client.objects.update_or_create(
                cpf_cnpj=cpf_cnpj,
                defaults={
                    'name': name,
                    'client_type': ctype,
                    'email': email,
                    'phone': phone,
                    'city': city,
                    'state': state,
                    'broker': brokers[broker_idx],
                    'is_active': True,
                },
            )
            clients.append(client)

        self.stdout.write(self.style.SUCCESS(f'  {len(clients)} clientes criados.'))
        return clients

    def _create_policies(self, clients, insurers, insurance_types, users):
        self.stdout.write('Criando propostas e apólices...')
        from policies.models import Proposal, Policy, ProposalStatus, PolicyStatus, PaymentMethod

        brokers = users['brokers']
        today = date.today()
        types_list = list(insurance_types.values())
        policies = []
        proposal_count = 0

        # Generate policies spanning last 12 months
        for i, client in enumerate(clients):
            broker = brokers[i % len(brokers)]
            insurer = insurers[i % len(insurers)]
            ins_type = types_list[i % len(types_list)]

            # Create proposal
            months_back = random.randint(1, 12)
            sub_date = today - timedelta(days=months_back * 30 + random.randint(5, 25))
            premium = Decimal(str(random.randint(800, 25000)))
            commission_rate = Decimal(str(random.randint(10, 25)))

            proposal, _ = Proposal.objects.update_or_create(
                proposal_number=f'PROP-{2026}{i + 1:04d}',
                defaults={
                    'client': client,
                    'insurer': insurer,
                    'insurance_type': ins_type,
                    'broker': broker,
                    'status': ProposalStatus.APPROVED,
                    'submission_date': sub_date,
                    'response_date': sub_date + timedelta(days=random.randint(3, 10)),
                    'premium_amount': premium,
                },
            )
            proposal_count += 1

            # Create policy from proposal
            start_date = sub_date + timedelta(days=random.randint(5, 15))
            end_date = start_date + timedelta(days=365)

            # Determine status based on dates
            if end_date < today:
                status = PolicyStatus.EXPIRED
            elif i >= 17:
                status = PolicyStatus.CANCELLED
            else:
                status = PolicyStatus.ACTIVE

            commission_amount = premium * commission_rate / 100
            insured_amount = premium * Decimal(str(random.randint(10, 50)))
            payment_methods = [pm[0] for pm in PaymentMethod.choices]

            policy, _ = Policy.objects.update_or_create(
                policy_number=f'APL-{2026}{i + 1:04d}',
                defaults={
                    'proposal': proposal,
                    'client': client,
                    'insurer': insurer,
                    'insurance_type': ins_type,
                    'broker': broker,
                    'status': status,
                    'start_date': start_date,
                    'end_date': end_date,
                    'premium_amount': premium,
                    'insured_amount': insured_amount,
                    'commission_rate': commission_rate,
                    'commission_amount': commission_amount,
                    'installments': random.choice([1, 3, 6, 12]),
                    'payment_method': random.choice(payment_methods),
                },
            )
            policies.append(policy)

        # Extra rejected proposals (no policy)
        for i in range(5):
            sub_date = today - timedelta(days=random.randint(30, 180))
            Proposal.objects.update_or_create(
                proposal_number=f'PROP-REJ-{2026}{i + 1:04d}',
                defaults={
                    'client': random.choice(clients),
                    'insurer': random.choice(insurers),
                    'insurance_type': random.choice(types_list),
                    'broker': random.choice(brokers),
                    'status': ProposalStatus.REJECTED,
                    'submission_date': sub_date,
                    'response_date': sub_date + timedelta(days=random.randint(5, 15)),
                    'premium_amount': Decimal(str(random.randint(1000, 15000))),
                    'rejection_reason': 'Risco fora do apetite da seguradora.',
                },
            )
            proposal_count += 1

        # Pending proposals
        for i in range(3):
            sub_date = today - timedelta(days=random.randint(1, 15))
            Proposal.objects.update_or_create(
                proposal_number=f'PROP-PEN-{2026}{i + 1:04d}',
                defaults={
                    'client': random.choice(clients),
                    'insurer': random.choice(insurers),
                    'insurance_type': random.choice(types_list),
                    'broker': random.choice(brokers),
                    'status': random.choice([ProposalStatus.SUBMITTED, ProposalStatus.UNDER_ANALYSIS]),
                    'submission_date': sub_date,
                    'premium_amount': Decimal(str(random.randint(1000, 20000))),
                },
            )
            proposal_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {proposal_count} propostas e {len(policies)} apólices criadas.'))
        return policies

    def _create_claims(self, policies, users):
        self.stdout.write('Criando sinistros...')
        from claims.models import Claim, ClaimStatus

        today = date.today()
        active_policies = [p for p in policies if p.status == 'active']
        claims_count = 0

        statuses = [
            ClaimStatus.OPEN, ClaimStatus.UNDER_ANALYSIS,
            ClaimStatus.DOCUMENTATION_PENDING, ClaimStatus.APPROVED,
            ClaimStatus.PAID, ClaimStatus.DENIED,
        ]

        descriptions = [
            'Colisão traseira em cruzamento. Danos no para-choque e lataria traseira.',
            'Sinistro por alagamento. Veículo submerso em enchente.',
            'Roubo do veículo no estacionamento do shopping.',
            'Incêndio no imóvel causado por curto-circuito.',
            'Queda de árvore sobre o telhado da residência após tempestade.',
            'Furto de equipamentos eletrônicos do escritório.',
            'Acidente de trabalho com afastamento do funcionário.',
            'Danos por vandalismo na fachada do estabelecimento.',
        ]

        for i in range(min(8, len(active_policies))):
            policy = active_policies[i]
            status = statuses[i % len(statuses)]
            occurrence = today - timedelta(days=random.randint(5, 120))
            notification = occurrence + timedelta(days=random.randint(1, 5))
            claimed = Decimal(str(random.randint(2000, 50000)))
            approved = None
            resolution_date = None

            if status in (ClaimStatus.APPROVED, ClaimStatus.PAID):
                approved = claimed * Decimal(str(random.uniform(0.5, 1.0)))
                approved = approved.quantize(Decimal('0.01'))
                resolution_date = occurrence + timedelta(days=random.randint(30, 90))
            elif status == ClaimStatus.DENIED:
                approved = Decimal('0')
                resolution_date = occurrence + timedelta(days=random.randint(15, 60))

            Claim.objects.update_or_create(
                claim_number=f'SIN-{2026}{i + 1:04d}',
                defaults={
                    'policy': policy,
                    'client': policy.client,
                    'status': status,
                    'occurrence_date': occurrence,
                    'notification_date': notification,
                    'description': descriptions[i % len(descriptions)],
                    'location': f'{policy.client.city}/{policy.client.state}',
                    'claimed_amount': claimed,
                    'approved_amount': approved,
                    'resolution_date': resolution_date,
                    'broker': policy.broker,
                },
            )
            claims_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {claims_count} sinistros criados.'))

    def _create_endorsements(self, policies, users):
        self.stdout.write('Criando endossos...')
        from endorsements.models import Endorsement, EndorsementType, EndorsementStatus

        today = date.today()
        active_policies = [p for p in policies if p.status == 'active']
        endorsement_count = 0

        types = [et[0] for et in EndorsementType.choices]
        statuses = [es[0] for es in EndorsementStatus.choices]

        descriptions_map = {
            'inclusion': 'Inclusão de novo item/condutor na apólice.',
            'exclusion': 'Exclusão de cobertura adicional.',
            'modification': 'Alteração de dados cadastrais do segurado.',
            'cancellation': 'Cancelamento parcial da apólice por solicitação do cliente.',
            'transfer': 'Transferência de titularidade da apólice.',
        }

        for i in range(min(6, len(active_policies))):
            policy = active_policies[i]
            etype = types[i % len(types)]
            request_date = today - timedelta(days=random.randint(5, 90))
            effective_date = request_date + timedelta(days=random.randint(1, 15))
            premium_diff = Decimal(str(random.randint(-500, 800)))

            Endorsement.objects.update_or_create(
                endorsement_number=f'END-{2026}{i + 1:04d}',
                defaults={
                    'policy': policy,
                    'endorsement_type': etype,
                    'status': statuses[min(i, len(statuses) - 1)],
                    'request_date': request_date,
                    'effective_date': effective_date,
                    'description': descriptions_map.get(etype, 'Endosso de alteração.'),
                    'premium_difference': premium_diff,
                    'requested_by': policy.broker,
                },
            )
            endorsement_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {endorsement_count} endossos criados.'))

    def _create_renewals(self, policies, users, insurers):
        self.stdout.write('Criando renovações...')
        from renewals.models import Renewal, RenewalStatus

        today = date.today()
        renewal_count = 0

        # For active policies expiring within 60 days
        active_policies = [p for p in policies if p.status == 'active']

        statuses = [
            RenewalStatus.PENDING, RenewalStatus.CONTACTED,
            RenewalStatus.QUOTE_SENT, RenewalStatus.PENDING,
            RenewalStatus.RENEWED, RenewalStatus.NOT_RENEWED,
        ]

        for i, policy in enumerate(active_policies[:10]):
            due_date = policy.end_date - timedelta(days=random.randint(5, 30))
            status = statuses[i % len(statuses)]
            contact_date = None
            new_premium = None

            if status in (RenewalStatus.CONTACTED, RenewalStatus.QUOTE_SENT, RenewalStatus.RENEWED):
                contact_date = today - timedelta(days=random.randint(1, 20))
            if status in (RenewalStatus.QUOTE_SENT, RenewalStatus.RENEWED):
                new_premium = policy.premium_amount * Decimal(str(random.uniform(0.9, 1.15)))
                new_premium = new_premium.quantize(Decimal('0.01'))

            Renewal.objects.update_or_create(
                policy=policy,
                defaults={
                    'status': status,
                    'due_date': due_date,
                    'contact_date': contact_date,
                    'new_premium': new_premium,
                    'new_insurer': random.choice(insurers) if random.random() > 0.6 else None,
                    'broker': policy.broker,
                    'notes': 'Renovação gerada automaticamente pelo seed.' if i % 3 == 0 else '',
                },
            )
            renewal_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {renewal_count} renovações criadas.'))

    def _create_crm_data(self, clients, users, insurance_types, insurers):
        self.stdout.write('Criando dados do CRM (pipeline, deals, atividades)...')
        from crm.models import Pipeline, PipelineStage, Deal, DealActivity, DealPriority, DealSource

        brokers = users['brokers']
        types_list = list(insurance_types.values())
        today = date.today()

        # Pipeline: Novos Negócios (default)
        pipeline, _ = Pipeline.objects.update_or_create(
            name='Novos Negócios',
            defaults={'is_default': True, 'is_active': True},
        )
        # Remove existing stages for idempotency
        PipelineStage.objects.filter(pipeline=pipeline).delete()

        stages_data = [
            ('Prospecção', 0, '#6c757d', False, False),
            ('Primeiro Contato', 1, '#0d6efd', False, False),
            ('Cotação', 2, '#ffc107', False, False),
            ('Proposta Enviada', 3, '#fd7e14', False, False),
            ('Negociação', 4, '#6610f2', False, False),
            ('Fechamento', 5, '#198754', True, False),
            ('Perdido', 6, '#dc3545', False, True),
        ]
        stages = []
        for name, order, color, is_won, is_lost in stages_data:
            stage = PipelineStage.objects.create(
                pipeline=pipeline,
                name=name,
                order=order,
                color=color,
                is_won=is_won,
                is_lost=is_lost,
            )
            stages.append(stage)

        # Second pipeline: Renovações
        pipeline2, _ = Pipeline.objects.update_or_create(
            name='Renovações',
            defaults={'is_default': False, 'is_active': True},
        )
        PipelineStage.objects.filter(pipeline=pipeline2).delete()
        for name, order, color, is_won, is_lost in [
            ('Identificada', 0, '#6c757d', False, False),
            ('Contato Realizado', 1, '#0d6efd', False, False),
            ('Cotação em Análise', 2, '#ffc107', False, False),
            ('Proposta Aceita', 3, '#198754', True, False),
            ('Não Renovada', 4, '#dc3545', False, True),
        ]:
            PipelineStage.objects.create(
                pipeline=pipeline2,
                name=name,
                order=order,
                color=color,
                is_won=is_won,
                is_lost=is_lost,
            )

        # Create deals in main pipeline
        priorities = [p[0] for p in DealPriority.choices]
        sources = [s[0] for s in DealSource.choices]

        deal_data = [
            ('Seguro Auto - João Mendes', 0, 3200, 'medium', 0, 0),
            ('Seguro Residencial - Maria Clara', 1, 1800, 'low', 1, 0),
            ('Seguro Empresarial - Tech Solutions', 2, 15000, 'high', 12, 0),
            ('Seguro Vida - Pedro Alves', 1, 4500, 'medium', 2, 1),
            ('Seguro Auto - Luciana Barbosa', 3, 5200, 'urgent', 3, 1),
            ('Seguro Saúde - Clínica Vida Plena', 4, 28000, 'high', 17, 1),
            ('Seguro Viagem - Roberto Costa', 0, 900, 'low', 4, 2),
            ('Seguro Empresarial - Comércio Nacional', 2, 22000, 'high', 13, 2),
            ('Seguro RC - Construtora Horizonte', 3, 18000, 'urgent', 15, 0),
            ('Seguro Auto - André Martins', 1, 2800, 'medium', 6, 2),
            ('Seguro Transporte - Transp. Rápidos', 4, 35000, 'high', 14, 1),
            ('Seguro Residencial - Camila Rocha', 0, 1500, 'low', 7, 0),
            ('Seguro Auto - Gustavo Lopes', 2, 4100, 'medium', 8, 2),
            ('Seguro Empresarial - Metalmax', 5, 42000, 'high', 18, 1),  # Won
            ('Seguro Vida - Patrícia Souza', 6, 3800, 'low', 9, 0),  # Lost
        ]

        deals = []
        for title, stage_idx, value, priority, client_idx, broker_idx in deal_data:
            deal, _ = Deal.objects.update_or_create(
                title=title,
                defaults={
                    'client': clients[client_idx],
                    'broker': brokers[broker_idx],
                    'pipeline': pipeline,
                    'stage': stages[stage_idx],
                    'insurance_type': random.choice(types_list),
                    'insurer': random.choice(insurers) if random.random() > 0.3 else None,
                    'expected_value': Decimal(str(value)),
                    'expected_close_date': today + timedelta(days=random.randint(5, 60)),
                    'priority': priority,
                    'source': random.choice(sources),
                },
            )
            deals.append(deal)

        # Create activities for each deal
        activity_types = ['note', 'call', 'email', 'meeting', 'task']
        activity_titles = {
            'note': ['Registrado interesse do cliente', 'Atualização de dados', 'Observação sobre perfil de risco'],
            'call': ['Ligação de apresentação', 'Follow-up telefônico', 'Ligação para negociação'],
            'email': ['Email com proposta enviada', 'Resposta ao email do cliente', 'Email de follow-up'],
            'meeting': ['Reunião de apresentação', 'Reunião para fechar proposta', 'Visita ao cliente'],
            'task': ['Preparar cotação', 'Revisar documentação', 'Emitir proposta'],
        }

        for deal in deals:
            num_activities = random.randint(1, 4)
            for j in range(num_activities):
                atype = random.choice(activity_types)
                DealActivity.objects.create(
                    deal=deal,
                    activity_type=atype,
                    title=random.choice(activity_titles[atype]),
                    description=f'Atividade referente à negociação {deal.title}.',
                    performed_by=deal.broker,
                    is_completed=random.random() > 0.4,
                )

        self.stdout.write(self.style.SUCCESS(f'  2 pipelines, {len(deals)} negociações e atividades criadas.'))
