from django.urls import path

from . import views

app_name = 'claims'

urlpatterns = [
    path('', views.ClaimListView.as_view(), name='claim_list'),
    path('create/', views.ClaimCreateView.as_view(), name='claim_create'),
    path('<int:pk>/', views.ClaimDetailView.as_view(), name='claim_detail'),
    path('<int:pk>/edit/', views.ClaimUpdateView.as_view(), name='claim_update'),
    path('<int:pk>/delete/', views.ClaimDeleteView.as_view(), name='claim_delete'),
    # Claim documents
    path('<int:pk>/documents/add/', views.ClaimDocumentCreateView.as_view(), name='claim_document_create'),
    path('documents/<int:pk>/delete/', views.ClaimDocumentDeleteView.as_view(), name='claim_document_delete'),
]
