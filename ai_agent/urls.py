from django.urls import path

from . import views

app_name = 'ai_agent'

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/<int:session_id>/', views.ChatView.as_view(), name='chat_session'),
    path('chat/create/', views.ChatCreateSessionView.as_view(), name='chat_create'),
    path('chat/send/', views.ChatSendMessageView.as_view(), name='chat_send'),
    path('chat/delete/<int:session_id>/', views.ChatDeleteSessionView.as_view(), name='chat_delete'),
    path('summary/', views.AISummaryView.as_view(), name='ai_summary'),
]
