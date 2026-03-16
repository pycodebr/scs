from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


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


class PlatformAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_platform_admin or self.request.user.is_superuser


class BrokerageRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_platform_admin or request.user.is_superuser
        ) and not request.user.brokerage_id:
            raise PermissionDenied('Usuário sem corretora vinculada.')
        return super().dispatch(request, *args, **kwargs)


class BrokerageFilterMixin(BrokerageRequiredMixin):
    brokerage_field = 'brokerage'
    broker_field = 'broker'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_platform_admin or self.request.user.is_superuser:
            return qs

        qs = qs.filter(**{self.brokerage_field: self.request.user.brokerage})
        if self.request.user.role == 'broker':
            model_fields = {field.name for field in qs.model._meta.fields}
            if self.broker_field in model_fields:
                qs = qs.filter(**{self.broker_field: self.request.user})
        return qs

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Http404 as exc:
            raise PermissionDenied('Registro fora da corretora atual.') from exc


class BrokerageFormMixin(BrokerageRequiredMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.instance
        if hasattr(instance, 'brokerage_id') and not instance.brokerage_id:
            instance.brokerage = self.request.user.brokerage
        return super().form_valid(form)


class ModuleRequiredMixin(BrokerageRequiredMixin, UserPassesTestMixin):
    required_module = ''

    def test_func(self):
        if self.request.user.is_platform_admin or self.request.user.is_superuser:
            return True
        if not self.required_module:
            return True
        return self.request.user.has_module(self.required_module)
