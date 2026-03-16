from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from utils.mixins import BrokerageRequiredMixin

from .models import PaymentRecord, Subscription


class SubscriptionOverviewView(BrokerageRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/subscription_overview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        brokerage = self.request.user.brokerage
        subscription = Subscription.objects.filter(
            brokerage=brokerage,
        ).select_related('plan').order_by('-created_at').first()
        payments = PaymentRecord.objects.filter(
            subscription__brokerage=brokerage,
        ).select_related('subscription', 'subscription__plan')[:20]
        ctx['subscription'] = subscription
        ctx['payments'] = payments
        return ctx
