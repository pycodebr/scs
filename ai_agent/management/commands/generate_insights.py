"""Management command para gerar insights do dashboard via LLM."""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gera insights do dashboard para usuarios ativos via IA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user_id',
            type=int,
            help='ID do usuario especifico (opcional)',
        )

    def handle(self, *args, **options):
        from accounts.models import User
        from ai_agent.models import DashboardInsight
        from ai_agent.agent.core import generate_insight_for_user

        if not getattr(settings, 'OPENAI_API_KEY', ''):
            self.stderr.write(self.style.ERROR(
                'OPENAI_API_KEY nao configurada. Abortando.'
            ))
            return

        user_id = options.get('user_id')
        if user_id:
            users = User.objects.filter(pk=user_id, is_active=True, is_platform_admin=False)
        else:
            users = User.objects.filter(is_active=True, is_platform_admin=False).exclude(brokerage__isnull=True)

        total = users.count()
        self.stdout.write(f'Gerando insights para {total} usuario(s)...')

        success = 0
        for user in users:
            self.stdout.write(f'  -> {user.get_full_name()} ({user.role})...')
            try:
                content = generate_insight_for_user(user)
                if content:
                    DashboardInsight.objects.create(
                        brokerage=user.brokerage,
                        user=user,
                        content=content,
                    )
                    success += 1
                    self.stdout.write(self.style.SUCCESS(f'     OK'))
                else:
                    self.stdout.write(self.style.WARNING(f'     Sem conteudo gerado'))
            except Exception as e:
                logger.exception(f'Erro ao gerar insight para {user}')
                self.stdout.write(self.style.ERROR(f'     Erro: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nConcluido: {success}/{total} insights gerados.'
        ))
