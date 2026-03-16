from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from .models import BrokerageStatus


class BrokerageContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.brokerage = None

        user = getattr(request, 'user', None)
        if user and user.is_authenticated and not (user.is_platform_admin or user.is_superuser):
            request.brokerage = user.brokerage
            if user.brokerage and user.brokerage.status == BrokerageStatus.INACTIVE:
                if request.path not in {reverse('accounts:login'), reverse('accounts:logout')}:
                    messages.error(request, 'Sua corretora está inativa. Contate o suporte.')
                logout(request)
                return redirect('accounts:login')

        return self.get_response(request)
