"""Filtragem de querysets por papel do usuario."""
from django.db.models import QuerySet


def get_filtered_queryset(user, model_class) -> QuerySet:
    """Retorna queryset filtrado pelo tenant e pelo papel do usuário."""
    qs = model_class.objects.all()

    model_fields = {field.name for field in model_class._meta.fields}
    if 'brokerage' in model_fields and user.brokerage_id:
        qs = qs.filter(brokerage=user.brokerage)

    if user.role == 'broker':
        from endorsements.models import Endorsement

        if model_class is Endorsement:
            qs = qs.filter(requested_by=user)
        elif 'broker' in model_fields:
            qs = qs.filter(broker=user)

    return qs
