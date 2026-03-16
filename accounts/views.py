from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from utils.mixins import ManagerRequiredMixin, BrokerageFormMixin, BrokerageRequiredMixin

from .forms import LoginForm, UserCreateForm, UserUpdateForm, ProfileForm, CustomPasswordChangeForm

User = get_user_model()


class LoginView(BaseLoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_platform_admin or user.is_superuser) and user.brokerage and not user.brokerage.is_active_for_login:
            messages.error(self.request, 'Sua corretora está inativa.')
            return self.form_invalid(form)
        return super().form_valid(form)


class LogoutView(BaseLogoutView):
    next_page = reverse_lazy('accounts:login')


class UserListView(BrokerageRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        qs = super().get_queryset().filter(
            brokerage=self.request.user.brokerage,
            is_platform_admin=False,
        )
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs.order_by('first_name', 'last_name')


class UserCreateView(BrokerageFormMixin, ManagerRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuário criado com sucesso.')
        return super().form_valid(form)


class UserUpdateView(BrokerageFormMixin, ManagerRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_queryset(self):
        return User.objects.filter(
            brokerage=self.request.user.brokerage,
            is_platform_admin=False,
        )

    def form_valid(self, form):
        messages.success(self.request, 'Usuário atualizado com sucesso.')
        return super().form_valid(form)


class UserDetailView(BrokerageRequiredMixin, ManagerRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'

    def get_queryset(self):
        return User.objects.filter(
            brokerage=self.request.user.brokerage,
            is_platform_admin=False,
        )


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil atualizado com sucesso.')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/password_change.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        login(self.request, self.request.user, backend='accounts.backends.EmailBackend')
        messages.success(self.request, 'Senha alterada com sucesso.')
        return super().form_valid(form)
