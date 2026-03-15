from django.urls import path

from . import views

app_name = 'crm'

urlpatterns = [
    # Kanban
    path('kanban/', views.DealKanbanView.as_view(), name='deal_kanban'),
    # Deal CRUD
    path('deals/', views.DealListView.as_view(), name='deal_list'),
    path('deals/create/', views.DealCreateView.as_view(), name='deal_create'),
    path('deals/<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('deals/<int:pk>/edit/', views.DealUpdateView.as_view(), name='deal_update'),
    path('deals/<int:pk>/delete/', views.DealDeleteView.as_view(), name='deal_delete'),
    # Move stage (AJAX)
    path('deals/<int:pk>/move/', views.DealMoveStageView.as_view(), name='deal_move_stage'),
    # Activities
    path('deals/<int:pk>/activities/create/', views.DealActivityCreateView.as_view(), name='deal_activity_create'),
    # Pipeline management
    path('pipelines/', views.PipelineManageView.as_view(), name='pipeline_manage'),
    path('pipelines/create/', views.PipelineCreateView.as_view(), name='pipeline_create'),
    path('pipelines/<int:pipeline_pk>/stages/create/', views.PipelineStageCreateView.as_view(), name='pipeline_stage_create'),
    path('pipelines/stages/<int:pk>/delete/', views.PipelineStageDeleteView.as_view(), name='pipeline_stage_delete'),
]
