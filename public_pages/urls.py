from django.urls import path

from .views import (
    LandingPageView,
    PricingView,
    PublicLoginRedirectView,
    SignupView,
    SignupSuccessView,
)

app_name = 'public_pages'

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('entrar/', PublicLoginRedirectView.as_view(), name='login_redirect'),
    path('planos/', PricingView.as_view(), name='pricing'),
    path('criar-conta/', SignupView.as_view(), name='signup'),
    path('criar-conta/sucesso/', SignupSuccessView.as_view(), name='signup_success'),
]
