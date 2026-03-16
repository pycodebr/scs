from django.urls import path

from .views import SubscriptionOverviewView

app_name = 'billing'

urlpatterns = [
    path('', SubscriptionOverviewView.as_view(), name='overview'),
]
