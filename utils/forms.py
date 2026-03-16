from django.contrib.auth import get_user_model


class BrokerageScopedFormMixin:
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self._apply_brokerage_scope()

    def _apply_brokerage_scope(self):
        if not self.user:
            return

        user_model = get_user_model()
        brokerage = getattr(self.user, 'brokerage', None)

        for field in self.fields.values():
            queryset = getattr(field, 'queryset', None)
            if queryset is None:
                continue

            model = queryset.model
            if model is user_model:
                field.queryset = queryset.filter(
                    is_active=True,
                    is_platform_admin=False,
                    brokerage=brokerage,
                ).order_by('first_name', 'last_name', 'email')
                continue

            if any(f.name == 'brokerage' for f in model._meta.fields):
                field.queryset = queryset.filter(brokerage=brokerage)

