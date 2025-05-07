from django.views.generic import ListView, DetailView
from .models import Conversation

class ConversationListView(ListView):
    model = Conversation
    template_name = 'chat/conversation_list.html'
    context_object_name = 'conversations'
    ordering = ['-created_at']

class FrontConversationDetailView(DetailView):
    model = Conversation
    template_name = 'chat/conversation_detail.html'
    context_object_name = 'conversation'
    slug_field = 'id'
    slug_url_kwarg = 'id'