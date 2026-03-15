from django.urls import path

from . import views

app_name = 'endorsements'

urlpatterns = [
    path('', views.EndorsementListView.as_view(), name='endorsement_list'),
    path('create/', views.EndorsementCreateView.as_view(), name='endorsement_create'),
    path('<int:pk>/', views.EndorsementDetailView.as_view(), name='endorsement_detail'),
    path('<int:pk>/edit/', views.EndorsementUpdateView.as_view(), name='endorsement_update'),
    path('<int:pk>/delete/', views.EndorsementDeleteView.as_view(), name='endorsement_delete'),
    # Endorsement documents
    path('<int:pk>/documents/add/', views.EndorsementDocumentCreateView.as_view(), name='endorsement_document_create'),
    path('documents/<int:pk>/delete/', views.EndorsementDocumentDeleteView.as_view(), name='endorsement_document_delete'),
]
