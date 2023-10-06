from django.db import models
from accounts.models import User


class Conversation(models.Model):
    participants = models.ManyToManyField(User)

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    text = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message sent by {self.sender}"
