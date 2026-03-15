from django.core.management.base import BaseCommand
from datetime import date, timedelta

from policies.models import Policy, PolicyStatus
from renewals.models import Renewal, RenewalStatus


class Command(BaseCommand):
    help = 'Verifica apolices que entram na janela de renovacao (60 dias) e cria registros de Renewal.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Janela de dias ate o vencimento para criar renovacao (default: 60)',
        )

    def handle(self, *args, **options):
        days = options['days']
        today = date.today()
        window_end = today + timedelta(days=days)

        policies = Policy.objects.filter(
            status=PolicyStatus.ACTIVE,
            end_date__lte=window_end,
            end_date__gte=today,
        ).select_related('broker')

        created_count = 0
        for policy in policies:
            exists = Renewal.objects.filter(
                policy=policy,
                status__in=[
                    RenewalStatus.PENDING,
                    RenewalStatus.CONTACTED,
                    RenewalStatus.QUOTE_SENT,
                    RenewalStatus.RENEWED,
                ],
            ).exists()
            if not exists:
                Renewal.objects.create(
                    policy=policy,
                    status=RenewalStatus.PENDING,
                    due_date=policy.end_date,
                    broker=policy.broker,
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'{created_count} renovacao(oes) criada(s) para apolices vencendo nos proximos {days} dias.')
        )
