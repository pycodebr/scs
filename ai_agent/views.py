import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView

from .models import ChatSession, ChatMessage, EntitySummary

logger = logging.getLogger(__name__)


class ChatView(LoginRequiredMixin, TemplateView):
    """Tela principal do chat com o agente de IA."""
    template_name = 'ai_agent/chat.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Listar sessoes do usuario
        ctx['sessions'] = ChatSession.objects.filter(user=user)[:30]

        # Sessao ativa (se passada via URL)
        session_id = self.kwargs.get('session_id')
        if session_id:
            session = get_object_or_404(ChatSession, pk=session_id, user=user)
            ctx['active_session'] = session
            ctx['chat_messages'] = session.messages.all()
        else:
            ctx['active_session'] = None
            ctx['chat_messages'] = []

        return ctx


class ChatCreateSessionView(LoginRequiredMixin, View):
    """Cria nova sessao de chat."""

    def post(self, request):
        session = ChatSession.objects.create(
            user=request.user,
            title='Novo Chat',
        )
        return JsonResponse({
            'session_id': session.pk,
            'title': session.title,
        })


class ChatSendMessageView(LoginRequiredMixin, View):
    """Recebe mensagem do usuario e retorna resposta do agente."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalido.'}, status=400)

        message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not message:
            return JsonResponse({'error': 'Mensagem vazia.'}, status=400)

        user = request.user

        # Obter ou criar sessao
        if session_id:
            session = get_object_or_404(ChatSession, pk=session_id, user=user)
        else:
            session = ChatSession.objects.create(
                user=user,
                title=message[:60] + ('...' if len(message) > 60 else ''),
            )

        # Atualizar titulo na primeira mensagem
        if session.title == 'Novo Chat' and session.messages.count() == 0:
            session.title = message[:60] + ('...' if len(message) > 60 else '')
            session.save(update_fields=['title'])

        # Salvar mensagem do usuario
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=message,
        )

        # Montar historico da conversa
        history = list(
            session.messages
            .exclude(pk=session.messages.last().pk if session.messages.exists() else 0)
            .values('role', 'content')
            .order_by('created_at')
        )
        # Excluir a mensagem recem criada do historico (sera enviada como mensagem atual)
        if history and history[-1]['content'] == message:
            history = history[:-1]

        # Chamar agente
        from .agent.core import get_agent_response
        response_text = get_agent_response(user, message, history)

        # Salvar resposta do agente
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=response_text,
        )

        return JsonResponse({
            'response': response_text,
            'session_id': session.pk,
            'session_title': session.title,
        })


class ChatDeleteSessionView(LoginRequiredMixin, View):
    """Exclui uma sessao de chat."""

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
        session.delete()
        return JsonResponse({'ok': True})


class AISummaryView(LoginRequiredMixin, View):
    """Gera resumo de uma entidade com IA."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalido.'}, status=400)

        entity_type = data.get('entity_type', '')
        entity_id = data.get('entity_id')

        if entity_type not in ('client', 'deal', 'policy', 'proposal', 'claim'):
            return JsonResponse({'error': 'Tipo de entidade invalido.'}, status=400)
        if not entity_id:
            return JsonResponse({'error': 'ID da entidade nao informado.'}, status=400)

        from .agent.core import generate_entity_summary
        summary = generate_entity_summary(request.user, entity_type, int(entity_id))

        EntitySummary.objects.create(
            entity_type=entity_type,
            entity_id=int(entity_id),
            user=request.user,
            content=summary,
        )

        return JsonResponse({'summary': summary})
