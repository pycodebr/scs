from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'admin'


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('admin', 'manager')


class BrokerFilterMixin:
    """Filtra queryset para mostrar apenas dados do corretor logado (se broker)."""
    broker_field = 'broker'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'broker':
            return qs.filter(**{self.broker_field: self.request.user})
        return qs
