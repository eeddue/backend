from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializer import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = '__all__'


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True)
    last_message = MessageSerializer()

    class Meta:
        model = Conversation
        fields = '__all__'
