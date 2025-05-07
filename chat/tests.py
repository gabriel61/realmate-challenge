from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from datetime import datetime
from .models import Conversation, Message


class WebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.webhook_url = reverse('webhook')

        # Conversa para tests que precisam de um ID existente
        self.conversation = Conversation.objects.create(
            id=uuid.uuid4(),
            status=Conversation.Status.OPEN,
            created_at=datetime.fromisoformat("2025-02-21T10:20:41.349308")
        )

    # Teste 1: Criação True
    def test_create_new_conversation_success(self):
        new_id = uuid.uuid4()
        data = {
            "type": "NEW_CONVERSATION",
            "timestamp": "2025-02-21T10:20:41.349308",
            "data": {"id": str(new_id)}
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Conversation.objects.filter(id=new_id).exists())

    # Teste 2: ID duplicado
    def test_create_duplicate_conversation(self):
        data = {
            "type": "NEW_CONVERSATION",
            "timestamp": "2025-02-21T10:20:41.349308",
            "data": {"id": str(self.conversation.id)}
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", response.data['error'].lower())

    # Teste 3: Add mensagem a conversa aberta
    def test_add_message_to_open_conversation(self):
        message_id = uuid.uuid4()
        data = {
            "type": "NEW_MESSAGE",
            "timestamp": "2025-02-21T10:20:42.349308",
            "data": {
                "id": str(message_id),
                "direction": "RECEIVED",
                "content": "Olá, tudo bem?",
                "conversation_id": str(self.conversation.id)
            }
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)

    # Teste 4: Add mensagem a conversa fechada
    def test_add_message_to_closed_conversation(self):
        self.conversation.status = Conversation.Status.CLOSED
        self.conversation.save()

        data = {
            "type": "NEW_MESSAGE",
            "timestamp": "2025-02-21T10:20:42.349308",
            "data": {
                "id": str(uuid.uuid4()),
                "direction": "RECEIVED",
                "content": "Mensagem inválida",
                "conversation_id": str(self.conversation.id)
            }
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Teste 5: Fechar conversa
    def test_close_existing_conversation(self):
        data = {
            "type": "CLOSE_CONVERSATION",
            "timestamp": "2025-02-21T10:20:45.349308",
            "data": {"id": str(self.conversation.id)}
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.conversation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.conversation.status, Conversation.Status.CLOSED)

    # Teste 6: Fechar conversa inexistente
    def test_close_nonexistent_conversation(self):
        fake_id = uuid.uuid4()
        data = {
            "type": "CLOSE_CONVERSATION",
            "timestamp": "2025-02-21T10:20:45.349308",
            "data": {"id": str(fake_id)}
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Teste 7: Detalhes da conversa com mensagens
    def test_conversation_detail_with_messages(self):
        # Criar 2 mensagens
        Message.objects.bulk_create([
            Message(
                id=uuid.uuid4(),
                conversation=self.conversation,
                direction=Message.Direction.RECEIVED,
                content="Mensagem 1",
                timestamp=datetime.fromisoformat("2025-02-21T10:20:42.349308")
            ),
            Message(
                id=uuid.uuid4(),
                conversation=self.conversation,
                direction=Message.Direction.SENT,
                content="Mensagem 2",
                timestamp=datetime.fromisoformat("2025-02-21T10:20:44.349308")
            )
        ])

        url = reverse('conversation-detail', kwargs={'id': str(self.conversation.id)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 2)
        self.assertEqual(response.data['status'], 'OPEN')

    # Teste 8: Detalhes de conversa inexistente
    def test_nonexistent_conversation_detail(self):
        fake_id = uuid.uuid4()
        url = reverse('conversation-detail', kwargs={'id': str(fake_id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Teste 9: Campo de direção inválido
    def test_invalid_message_direction(self):
        data = {
            "type": "NEW_MESSAGE",
            "timestamp": "2025-02-21T10:20:42.349308",
            "data": {
                "id": str(uuid.uuid4()),
                "direction": "INVALID",
                "content": "Mensagem inválida",
                "conversation_id": str(self.conversation.id)
            }
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("direction", response.data['error'].lower())

    # Teste 10: Formato de UUID inválido
    def test_invalid_uuid_format(self):
        data = {
            "type": "NEW_CONVERSATION",
            "timestamp": "2025-02-21T10:20:41.349308",
            "data": {"id": "invalid-uuid"}
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Teste 11: Campos obrigatórios faltando
    def test_missing_required_fields(self):
        data = {
            "type": "NEW_MESSAGE",
            "timestamp": "2025-02-21T10:20:42.349308",
            "data": {
                "id": str(uuid.uuid4()),
                # direction
                "content": "Mensagem incompleta",
                "conversation_id": str(self.conversation.id)
            }
        }

        response = self.client.post(self.webhook_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)