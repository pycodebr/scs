"""Filtragem de querysets por papel do usuario."""
from django.db.models import QuerySet


def get_filtered_queryset(user, model_class) -> QuerySet:
    """Retorna queryset filtrado pelo papel do usuario.

    - admin: todos os dados
    - manager: todos os dados
    - broker: apenas dados vinculados ao proprio broker
    """
    qs = model_class.objects.all()

    if user.role == 'broker':
        # Cada model usa 'broker' como FK, exceto Endorsement que usa 'requested_by'
        from endorsements.models import Endorsement
        if model_class is Endorsement:
            qs = qs.filter(requested_by=user)
        else:
            qs = qs.filter(broker=user)

    return qs
