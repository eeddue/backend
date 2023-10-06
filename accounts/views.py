from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import generics
from .permissions import IsPharmacist, IsCustomer, IsProductOwner, IsCustomerReviewOwner
from django.shortcuts import get_object_or_404
from django.db.models import Q
import random
from django.shortcuts import render
from django.shortcuts import render
from django.http import JsonResponse
from accounts.models import UserRole, User, PaymentPlan, Profile

from accounts.serializer import MyTokenObtainPairSerializer, RegisterSerializer, LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes


# EMAIL
def EmailView(request):
    return render(request, 'email.html')


# AUTHENTICATION

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        role_name = request.data.get('role')
        if not role_name:
            return Response({'role': 'Role is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            role = UserRole.objects.get(name=role_name)
        except UserRole.DoesNotExist:
            return Response({'role': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Assign the selected role to the user
        user.role = role
        user.save()

        # Ensure that a 'free' payment plan exists in your database
        try:
            free_plan = PaymentPlan.objects.get(name='free')
        except PaymentPlan.DoesNotExist:
            return Response({'message': 'Payment plan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a profile already exists for the user
        profile, created = Profile.objects.get_or_create(user=user)

        if role_name == 'Pharmacist':
            profile.payment_plan = free_plan
            profile.role = role_name
            profile.save()

        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = LoginSerializer


# Password RESET
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.send_reset_email()
            return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# confirm password view
class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        # Check if the code is valid and not expired
        try:
            user = User.objects.get(reset_code=code)
        except User.DoesNotExist:
            return Response({'message': 'Invalid reset code.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the code has expired (30 minutes)
        if (
            user.reset_code_created_at
            and timezone.now() - user.reset_code_created_at > timedelta(minutes=30)
        ):
            return Response({'message': 'Reset code has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset the user's password
        user.set_password(new_password)
        user.save()

        # Clear the reset code and reset_code_created_at fields
        user.reset_code = None
        user.reset_code_created_at = None
        user.save()

        return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

# Get All Routes


@api_view(['GET'])
def getRoutes(request):
    routes = [

        # get all routes
        'GET /api',

        # authentication
        '/api/register/',
        '/api/token/',
        '/api/login/',
        '/api/token/refresh/',

        # test if authenticated/logged in
        '/api/test/',

        # products
        'GET /api/products',
        'GET /api/product/:id',
        'POST /api/products/create/',
        'UPDATE /api/product/<int:pk>/update',
        'DELETE /api/product/delete/<int:pk>',

        # pharmacy
        'GET /api/pharmacies',
        'GET /api/pharmacy/:id',
        'POST /api/pharmacies/create',
        'UPDATE /api/pharmacy/<int:pk>/update',
        'DELETE /api/pharmacy/delete/<int:pk>',

        # reviews
        'GET /api/reviews',
        'GET /api/review/:id',
        'POST /api/reviews/create',
        'UPDATE /api/review/<int:pk>/update',
        'DELETE /api/review/delete/<int:pk>',
    ]
    return Response(routes)


# test endpoint after authentication

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def testEndPoint(request):
    if request.method == 'GET':
        data = f"Congratulation {request.user}, your API just responded to GET request"
        return Response({'response': data}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        text = "Hello buddy"
        data = f'Congratulation your API just responded to POST request with text: {text}'
        return Response({'response': data}, status=status.HTTP_200_OK)
    return Response({}, status.HTTP_400_BAD_REQUEST)


def indexPage(request):
    return render(request, 'index.html')
