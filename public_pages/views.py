from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from django.views.generic import FormView, TemplateView

from billing.models import Plan
from billing.services import bootstrap_catalog, create_subscription_for_signup
from brokerages.models import Brokerage
from utils.mixins import BrokerageRequiredMixin

from .forms import SignupForm


class PublicCatalogMixin:
    def get_active_plans(self):
        bootstrap_catalog()
        return Plan.objects.filter(is_active=True).prefetch_related('modules').order_by('sort_order', 'monthly_price_per_user')


class LandingPageView(PublicCatalogMixin, TemplateView):
    template_name = 'public/landing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['plans'] = self.get_active_plans()
        ctx['highlight_plan'] = next((plan for plan in ctx['plans'] if plan.highlight_label), None)
        return ctx


class PricingView(PublicCatalogMixin, TemplateView):
    template_name = 'public/pricing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['plans'] = self.get_active_plans()
        return ctx


class PublicLoginRedirectView(RedirectView):
    pattern_name = 'accounts:login'


class SignupView(PublicCatalogMixin, FormView):
    template_name = 'public/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('public_pages:signup_success')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['plan_queryset'] = self.get_active_plans()
        if self.request.method == 'GET' and self.request.GET.get('plan'):
            kwargs.setdefault('initial', {})
            kwargs['initial']['plan'] = self.request.GET.get('plan')
        return kwargs

    def form_valid(self, form):
        user_model = get_user_model()
        brokerage = Brokerage.objects.create(
            legal_name=form.cleaned_data['legal_name'],
            trade_name=form.cleaned_data['trade_name'],
            cnpj=form.cleaned_data['cnpj'],
            email=form.cleaned_data['brokerage_email'],
            phone=form.cleaned_data['brokerage_phone'],
            zip_code=form.cleaned_data['zip_code'],
            street=form.cleaned_data['street'],
            number=form.cleaned_data['number'],
            complement=form.cleaned_data['complement'],
            neighborhood=form.cleaned_data['neighborhood'],
            city=form.cleaned_data['city'],
            state=form.cleaned_data['state'],
        )

        user = user_model.objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=form.cleaned_data['phone'],
            role='admin',
            is_active=True,
            is_staff=False,
            brokerage=brokerage,
        )

        create_subscription_for_signup(
            brokerage=brokerage,
            plan=form.cleaned_data['plan'],
            active_user_count=1,
            granted_by=user,
        )

        backend = 'accounts.backends.EmailBackend'
        login(self.request, user, backend=backend)
        messages.success(self.request, 'Conta criada com sucesso.')
        return super().form_valid(form)


class SignupSuccessView(BrokerageRequiredMixin, TemplateView):
    template_name = 'public/signup_success.html'
