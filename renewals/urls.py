from django.urls import path

from . import views

app_name = 'renewals'

urlpatterns = [
    path('', views.RenewalListView.as_view(), name='renewal_list'),
    path('create/', views.RenewalCreateView.as_view(), name='renewal_create'),
    path('<int:pk>/', views.RenewalDetailView.as_view(), name='renewal_detail'),
    path('<int:pk>/edit/', views.RenewalUpdateView.as_view(), name='renewal_update'),
    path('<int:pk>/renew/', views.RenewalRenewView.as_view(), name='renewal_renew'),
]
