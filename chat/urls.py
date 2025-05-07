from django.urls import path
from .views import WebhookView, ConversationDetailView
from .views_front import ConversationListView, FrontConversationDetailView

urlpatterns = [
    # Frontend
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<uuid:id>/', FrontConversationDetailView.as_view(), name='conversation-detail'),

    # API
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('webhook/conversations/<uuid:id>/', ConversationDetailView.as_view(), name='api-conversation-detail'),
]