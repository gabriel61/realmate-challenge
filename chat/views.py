from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from .models import Conversation, Message
from .serializers import ConversationSerializer
import uuid
import logging

logger = logging.getLogger(__name__)


class WebhookView(APIView):
    def post(self, request):
        if not all(key in request.data for key in ['type', 'timestamp', 'data']):
            return Response(
                {"error": "Missing required fields: type, timestamp, data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            timestamp = parse_datetime(request.data['timestamp'])
            if not timestamp:
                raise ValueError
        except (KeyError, ValueError):
            return Response(
                {"error": "Invalid timestamp format. Use ISO 8601"},
                status=status.HTTP_400_BAD_REQUEST
            )

        event_type = request.data['type']
        data = request.data['data']

        handler = getattr(self, f'handle_{event_type.lower()}', None)
        if not handler:
            return Response(
                {"error": f"Unsupported event type: {event_type}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return handler(data, timestamp)

    def handle_new_conversation(self, data, timestamp):
        conversation_id = data.get('id')
        if not conversation_id:
            return Response(
                {"error": "Missing conversation ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return Response(
                {"error": "Invalid conversation ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            Conversation.objects.create(
                id=conv_uuid,
                status=Conversation.Status.OPEN,
                created_at=timestamp
            )
            return Response(
                {"status": "Conversation created"},
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {"error": "Conversation ID already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_new_message(self, data, timestamp):
        required_fields = ['id', 'direction', 'content', 'conversation_id']
        if any(field not in data for field in required_fields):
            return Response(
                {"error": f"Missing required fields: {', '.join(required_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conv_uuid = uuid.UUID(data['conversation_id'])
        except ValueError:
            return Response(
                {"error": "Invalid conversation ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data['direction'] not in Message.Direction.values:
            return Response(
                {"error": f"Invalid direction. Valid values: {', '.join(Message.Direction.values)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conversation = Conversation.objects.get(id=conv_uuid)

            if conversation.status == Conversation.Status.CLOSED:
                return Response(
                    {"error": "Cannot add messages to closed conversation"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Message.objects.create(
                id=uuid.UUID(data['id']),
                conversation=conversation,
                direction=data['direction'],
                content=data['content'],
                timestamp=timestamp
            )
            return Response(
                {"status": "Message created"},
                status=status.HTTP_201_CREATED
            )

        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except IntegrityError:
            return Response(
                {"error": "Message ID already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_close_conversation(self, data, timestamp):
        conversation_id = data.get('id')
        if not conversation_id:
            return Response(
                {"error": "Missing conversation ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conv_uuid = uuid.UUID(conversation_id)
            conversation = Conversation.objects.get(id=conv_uuid)

            if conversation.status == Conversation.Status.CLOSED:
                return Response(
                    {"warning": "Conversation already closed"},
                    status=status.HTTP_200_OK
                )

            conversation.status = Conversation.Status.CLOSED
            conversation.save()
            return Response(
                {"status": "Conversation closed"},
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {"error": "Invalid conversation ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ConversationDetailView(RetrieveAPIView):
    serializer_class = ConversationSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_object(self):
        try:
            return get_object_or_404(
                Conversation.objects.prefetch_related('messages'),
                id=self.kwargs['id']
            )
        except (ValueError, Conversation.DoesNotExist):
            raise Http404("Conversation not found")