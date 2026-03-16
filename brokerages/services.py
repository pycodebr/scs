from .models import BrokerageModule, SystemModule


DEFAULT_MODULES = [
    ('dashboard', 'Dashboard', 'Indicadores e visão geral'),
    ('crm', 'CRM', 'Pipeline, kanban e negociações'),
    ('claims', 'Sinistros', 'Gestão de sinistros'),
    ('endorsements', 'Endossos', 'Gestão de endossos'),
    ('renewals', 'Renovações', 'Gestão de renovações'),
    ('reports', 'Relatórios', 'Relatórios gerenciais'),
    ('ai_agent', 'Assistente IA', 'Resumos e chat inteligente'),
]


def bootstrap_system_modules():
    modules = []
    for index, (slug, name, description) in enumerate(DEFAULT_MODULES):
        module, _ = SystemModule.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'sort_order': index,
                'is_active': True,
            },
        )
        modules.append(module)
    return modules


def sync_brokerage_modules(brokerage, plan, granted_by=None):
    allowed_slugs = set(plan.modules.filter(is_active=True).values_list('slug', flat=True))
    for module in SystemModule.objects.filter(is_active=True):
        BrokerageModule.objects.update_or_create(
            brokerage=brokerage,
            module=module,
            defaults={
                'is_enabled': module.slug in allowed_slugs,
                'granted_by': granted_by,
            },
        )
