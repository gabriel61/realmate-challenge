from django.db import models
import uuid


class Conversation(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.status}"

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    class Direction(models.TextChoices):
        SENT = 'SENT', 'Sent'
        RECEIVED = 'RECEIVED', 'Received'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices
    )
    content = models.TextField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.direction} - {self.content[:20]}"

    class Meta:
        ordering = ['timestamp']