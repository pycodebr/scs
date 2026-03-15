from django.urls import path

from . import views

app_name = 'coverages'

urlpatterns = [
    path('types/', views.InsuranceTypeListView.as_view(), name='type_list'),
    path('types/create/', views.InsuranceTypeCreateView.as_view(), name='type_create'),
    path('types/<int:pk>/edit/', views.InsuranceTypeUpdateView.as_view(), name='type_update'),
    path('', views.CoverageListView.as_view(), name='coverage_list'),
    path('create/', views.CoverageCreateView.as_view(), name='coverage_create'),
    path('<int:pk>/edit/', views.CoverageUpdateView.as_view(), name='coverage_update'),
    path('<int:coverage_pk>/items/create/', views.CoverageItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.CoverageItemUpdateView.as_view(), name='item_update'),
]
