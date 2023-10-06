from django.conf import settings
from datetime import timedelta
from django.template.loader import render_to_string
import os
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import random
from django.shortcuts import get_object_or_404
from accounts.models import UserRole, User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status
from rest_framework.response import Response


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # These are claims, you can add custom claims
        token['full_name'] = user.profile.full_name
        token['username'] = user.username
        token['email'] = user.email
        token['bio'] = user.profile.bio
        # token['image'] = str(user.profile.image)
        token['verified'] = user.profile.verified
        token['payment_plan'] = user.profile.payment_plan
        # ...
        return token

# register user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    role = serializers.CharField()

    class Meta:
        model = User
        fields = ('email', 'username', 'role', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        # Lowercase the email and username before saving it
        validated_data['email'] = validated_data['email'].lower()
        validated_data['username'] = validated_data['username'].lower()

        # Remove 'role' from validated_data
        role_name = validated_data.pop('role')
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )

        user.set_password(validated_data['password'])
        user.save()

        try:
            role = UserRole.objects.get(name=role_name)
        except UserRole.DoesNotExist:
            # If the role doesn't exist, you may want to handle this case accordingly
            raise serializers.ValidationError({"role": "Invalid role."})

        # Assign the selected role to the user
        user.role = role
        user.save()

        return user


# login
class LoginSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()

    def validate_email(self, value):
        """
        Normalize the email to lowercase during validation.
        """
        return value.lower()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Include these in the token payload
        token['email'] = user.email
        token['full_name'] = user.profile.full_name
        token['username'] = user.username
        token['bio'] = user.profile.bio
        # token['image'] = str(user.profile.image)
        token['role'] = user.role.name
        token['created_at'] = user.date_joined.isoformat()

        # return token
        # print(token)
        return token


# reset password

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def send_reset_email(self):
        email = self.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Check if a reset code already exists and is not expired
            if (
                user.reset_code_created_at
                and timezone.now() - user.reset_code_created_at <= timedelta(minutes=30)
            ):
                raise serializers.ValidationError(
                    'Reset code already sent. Please check your email.')

            # Generate a random 6-digit code
            reset_code = get_random_string(
                length=6, allowed_chars='1234567890')

            # Update the user's reset_code and reset_code_created_at fields
            user.reset_code = reset_code
            user.reset_code_created_at = timezone.now()
            user.save()

            # Render the HTML email template
            subject = 'Password Reset Code'
            context = {'code': reset_code}
            html_message = render_to_string(
                'mail.html', context)

            # Send the reset code via email
            recipient_list = [user.email]
            send_mail(
                subject,
                '',
                settings.EMAIL_HOST_USER,
                recipient_list,
                fail_silently=False,
                html_message=html_message
            )

        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with this email does not exist.')


# confirm code
class PasswordResetConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
