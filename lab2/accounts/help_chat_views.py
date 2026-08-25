"""Backend for the floating help-chat widget (templates/help_chat/
widget.html): fetch a signed-in account's saved conversation, post a new
question and get a rule-based reply (accounts/faq.py), or reset the
conversation entirely. All three are scoped to request.user — an
employee's and an admin's chat history are both just rows on
HelpChatMessage, kept or cleared independently per account, never shared
between accounts."""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views import View

from .faq import find_answer
from .models import HelpChatMessage

MAX_MESSAGE_LENGTH = 500


class HelpChatHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        messages = request.user.help_chat_messages.values("role", "text", "created_at")
        return JsonResponse({"messages": list(messages)}, encoder=DjangoJSONEncoder)


class HelpChatAskView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        text = str(payload.get("message", "")).strip()[:MAX_MESSAGE_LENGTH]
        if not text:
            return JsonResponse({"error": "Type a question first."}, status=400)

        HelpChatMessage.objects.create(user=request.user, role=HelpChatMessage.Role.USER, text=text)
        answer = find_answer(text, is_staff=request.user.is_staff)
        HelpChatMessage.objects.create(user=request.user, role=HelpChatMessage.Role.BOT, text=answer)

        return JsonResponse({"answer": answer})


class HelpChatResetView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.help_chat_messages.all().delete()
        return JsonResponse({"status": "ok"})
