from django.urls import path
from .views import WebhookView, ConversationDetailView

urlpatterns = [
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('webhook/conversations/<uuid:id>/', ConversationDetailView.as_view(), name='api-conversation-detail'),
]