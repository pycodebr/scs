from django.urls import path

from . import views

app_name = 'policies'

urlpatterns = [
    # Proposals
    path('proposals/', views.ProposalListView.as_view(), name='proposal_list'),
    path('proposals/create/', views.ProposalCreateView.as_view(), name='proposal_create'),
    path('proposals/<int:pk>/', views.ProposalDetailView.as_view(), name='proposal_detail'),
    path('proposals/<int:pk>/edit/', views.ProposalUpdateView.as_view(), name='proposal_update'),
    path('proposals/<int:pk>/delete/', views.ProposalDeleteView.as_view(), name='proposal_delete'),
    path('proposals/<int:pk>/convert/', views.ProposalConvertView.as_view(), name='proposal_convert'),
    # Policies
    path('', views.PolicyListView.as_view(), name='policy_list'),
    path('create/', views.PolicyCreateView.as_view(), name='policy_create'),
    path('export/', views.PolicyExportView.as_view(), name='policy_export'),
    path('<int:pk>/', views.PolicyDetailView.as_view(), name='policy_detail'),
    path('<int:pk>/edit/', views.PolicyUpdateView.as_view(), name='policy_update'),
    path('<int:pk>/delete/', views.PolicyDeleteView.as_view(), name='policy_delete'),
    # Policy coverages
    path('<int:pk>/coverages/add/', views.PolicyCoverageCreateView.as_view(), name='policy_coverage_create'),
    path('coverages/<int:pk>/delete/', views.PolicyCoverageDeleteView.as_view(), name='policy_coverage_delete'),
    # Policy documents
    path('<int:pk>/documents/add/', views.PolicyDocumentCreateView.as_view(), name='policy_document_create'),
    path('documents/<int:pk>/delete/', views.PolicyDocumentDeleteView.as_view(), name='policy_document_delete'),
]
