from rest_framework import serializers
from datetime import timedelta  # Import timedelta for date calculations
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from chat.serializers import ConversationSerializer, MessageSerializer
from chat.models import Conversation, Message
from django.conf import settings
from django.core.mail import send_mail
from api.serializer import ContactInfoSerializer
from rest_framework import generics
from accounts.permissions import IsPharmacist, IsCustomer, IsProductOwner, IsCustomerReviewOwner
from django.shortcuts import get_object_or_404
from django.db.models import Q
import random
from django.shortcuts import render
from django.shortcuts import render
from django.http import JsonResponse
from api.models import Product, Pharmacy, Review, Contact
from api.serializer import (CategorySerializer,
                            ReviewedProductSerializer,
                            ReviewGetSerializer,
                            ReviewCreateSerializer,
                            ReviewUpdateSerializer,
                            LocationSerializer,
                            PharmacyGetSerializer,
                            PharmacyCreateSerializer,
                            PharmacyUpdateSerializer,
                            ProductGetSerializer,
                            ProductCreateSerializer,
                            ProductUpdateSerializer,
                            )
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes


# Get All Routes


@api_view(['GET'])
def getRoutes(request):
    routes = [

        # get all routes
        'GET /api',

        # authentication
        '/accounts/register/',
        '/accounts/token/',
        '/accounts/login/',
        '/accounts/token/refresh/',
        '/accounts/password-reset/',
        '/accounts/password-reset-confirm/',

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
        'GET /api/user-pharmacies',
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
    return render(request, 'documentation.html')


"""
CONTACT FORM
"""


@api_view(['POST'])
@permission_classes([AllowAny])
def send_contact_email(request):
    """
    Receive contact information from the frontend, send an email, and save to the database.
    """
    serializer = ContactInfoSerializer(data=request.data)

    if serializer.is_valid():
        feedback = serializer.save()

        # Send feedback to the admin via email
        subject = feedback.email_subject
        message = f"From: {feedback.name}\nEmail: {feedback.email}\n\n{feedback.email_body}"
        from_email = feedback.email
        recipient_list = [settings.EMAIL_HOST_USER]
        send_mail(subject, message, from_email,
                  recipient_list, fail_silently=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
PRODUCTS
"""
# Get all products


@api_view(['GET'])
def productList(request):
    """
    Get serialized product list.
    Optionally filter products based on 'name' 'category' & 'owner' query parameters.
    Products displayed are random.
    """

    # Get query parameters from the request's query string
    query_name = request.GET.get('name')
    query_category = request.GET.get('category')
    query_owner = request.GET.get('owner')

    # Init an empty queryset
    products = Product.objects.all()

    # Check if query_name or query_category were provided and filter the queryset accordingly
    if query_name:
        products = products.filter(Q(name__icontains=query_name))
    if query_category:
        products = products.filter(Q(category__name__icontains=query_category))
    if query_owner:
        products = products.filter(Q(owner=query_owner))

    # Shuffle the products to get a random order
    products = list(products[:20])
    random.shuffle(products)

    # Serialize the filtered and ordered queryset
    serializer = ProductGetSerializer(products, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Get product by id


@api_view(['GET'])
def productDetail(request, pk):
    product = get_object_or_404(Product, id=pk)
    serializer = ProductGetSerializer(product, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


#  Get products owned by the currently authenticated pharmacist

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPharmacist])
def pharmacist_products(request):
    """
    Get products owned by the currently authenticated pharmacist.
    """
    user = request.user
    # Retrieve products owned by the pharmacist
    products = Product.objects.filter(owner__owned_by=user)
    serializer = ProductGetSerializer(products, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Post/Create a product


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [IsPharmacist, IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Check the user's subscription plan and plan expiration date
        if user.profile.payment_plan:
            payment_plan = user.profile.payment_plan.name
            plan_expiration_date = user.profile.plan_expiration_date

            # Check if the plan has expired
            if plan_expiration_date and plan_expiration_date < timezone.now():
                return Response(
                    {'detail': 'Your subscription plan has expired. Please update your plan to create more products.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            max_products_allowed = {
                'free': 10,
                'basic': 30,
                'premium': 70,
                'platinum': None  # Unlimited
            }.get(payment_plan)

            if max_products_allowed is not None:
                products_created = user.profile.products_created
                if products_created >= max_products_allowed:
                    # print('Limit exceeded')
                    raise serializers.ValidationError(
                        f'detail : You have reached the maximum limit of {max_products_allowed} products allowed by your plan. Please update your plan to create more products.'
                    )

        # Get the related pharmacy for the product
        pharmacy_id = self.request.data.get('owner')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, owned_by=user)

        serializer.save()
        user.profile.products_created += 1
        user.profile.save()


# update product
'''
Only a pharmacist who created the product can update their own product
'''


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductUpdateSerializer
    permission_classes = [IsPharmacist, IsProductOwner]

    def get_object(self):
        # Get the review object based on the provided 'pk' (ID)
        pk = self.kwargs.get('pk')
        return get_object_or_404(Product, id=pk)

    def update(self, request, *args, **kwargs):
        # Get the pharmacy object to be updated
        product = self.get_object()

        # Check if the user making the request is a Pharmacist and owns the pharmacy
        if not request.user.is_pharmacist() or request.user != product.owner:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(
            product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'detail': 'Product updated successfully.'}, status=status.HTTP_200_OK)


# delete a product by id
'''
Only a pharmacist who created the product can delete their own product
'''


@api_view(['DELETE'])
@permission_classes([IsPharmacist, IsProductOwner])
def deleteProduct(request, pk):
    """
    Delete a product by ID.
    """
    try:
        product = get_object_or_404(Product, id=pk)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    product.delete()

    return Response({'detail': 'Product deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


"""
# PHARMACY
"""

# get all


@api_view(['GET'])
def getPharmacy(request):
    pharmacy = Pharmacy.objects.all()
    serializer = PharmacyGetSerializer(pharmacy, many=True)
    return Response(serializer.data)


# get for certain logged in user

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPharmacist])
def userPharmacies(request):
    """
    Get pharmacies owned by the currently authenticated user.
    """
    user = request.user
    # Retrieve pharmacies owned by the user
    pharmacies = Pharmacy.objects.filter(owned_by=user)
    serializer = PharmacyGetSerializer(pharmacies, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# get by id


@api_view(['GET'])
def pharmacyDetail(request, pk):
    pharmacy = get_object_or_404(Pharmacy, id=pk)
    serializer = PharmacyGetSerializer(pharmacy, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


# create
'''
Only users who registered as a Pharmacist can create a new pharmacy
'''


class PharmacyCreateView(generics.CreateAPIView):
    queryset = Pharmacy.objects.all()
    serializer_class = PharmacyCreateSerializer
    permission_classes = [IsPharmacist, IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Check the user's subscription plan and plan expiration date
        if user.profile.payment_plan:
            payment_plan = user.profile.payment_plan.name
            plan_expiration_date = user.profile.plan_expiration_date

            # Check if the plan has expired
            if plan_expiration_date and plan_expiration_date < timezone.now():
                return Response(
                    {'detail': 'Your subscription plan has expired. Please update your plan to create more pharmacies.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Define the maximum allowed pharmacies based on the plan
            max_pharmacies_allowed = {
                'free': 1,
                'basic': 2,
                'premium': 10,
                'platinum': None  # Unlimited
            }.get(payment_plan)

            if max_pharmacies_allowed is not None:
                # Check if the user has exceeded the limit
                pharmacies_created = user.profile.pharmacies_created
                if pharmacies_created >= max_pharmacies_allowed:
                    raise serializers.ValidationError(
                        f'detail : You have reached the maximum limit of {max_pharmacies_allowed} pharmacy(s) allowed by your plan. Please update your plan to create more pharmacies.'
                    )

        # Continue with creating the pharmacy and set the user as the owner
        serializer.save(owned_by=user)

        user.profile.pharmacies_created += 1
        user.profile.save()


# class PharmacyCreateView(generics.CreateAPIView):
#     queryset = Pharmacy.objects.all()
#     serializer_class = PharmacyCreateSerializer
#     permission_classes = [IsPharmacist]

#     def perform_create(self, serializer):
#         # Get the currently logged-in user
#         user = self.request.user

#         # Check if the user is authenticated
#         if user.is_authenticated:
#             # Set the user as the owner of the pharmacy
#             serializer.save(owned_by=user)


# update
'''
Only the pharmacy owner and the admin can update Pharmacy details
'''


class PharmacyUpdateView(generics.UpdateAPIView):
    queryset = Pharmacy.objects.all()
    serializer_class = PharmacyUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get the review object based on the provided 'pk' (ID)
        pk = self.kwargs.get('pk')
        return get_object_or_404(Pharmacy, id=pk)

    def update(self, request, *args, **kwargs):
        # Get the pharmacy object to be updated
        pharmacy = self.get_object()

        # Check if the user making the request is a Pharmacist and owns the pharmacy
        if not request.user.is_pharmacist() or request.user != pharmacy.owned_by:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(
            pharmacy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'detail': 'Pharmacy updated successfully.'}, status=status.HTTP_200_OK)


# delete pharmacy
'''
Only the pharmacy owner and the admin can delete a pharmacy
'''


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletePharmacy(request, pk):
    try:
        pharmacy = get_object_or_404(Pharmacy, id=pk)
    except Pharmacy.DoesNotExist:
        return Response({'detail': 'Pharmacy not found.'}, status=status.HTTP_404_NOT_FOUND)

     # Check if the user making the request is a Pharmacist and owns the pharmacy
    if not request.user.is_pharmacist() or request.user != pharmacy.owned_by:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    pharmacy.delete()

    return Response({'detail': 'Pharmacy deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


"""
REVIEWS
"""

# Get all


@api_view(['GET'])
def reviewtList(request):
    """
    Get serialized product list
    """
    reviews = Review.objects.all().order_by('-created_at')
    serializer = ReviewGetSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# get by id
@api_view(['GET'])
def reviewDetail(request, pk):
    review = get_object_or_404(Review, id=pk)
    serializer = ReviewGetSerializer(review, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Post a review
'''
Only authenticated customer can post a review
'''


class ReviewCreateView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated, IsCustomer]


# update
'''
Only users who are Customers and who created the review can update their own review.
'''


class ReviewUpdateView(generics.UpdateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsAuthenticated, IsCustomer, IsCustomerReviewOwner]

    def get_object(self):
        # Get the review object based on the provided 'pk' (ID)
        pk = self.kwargs.get('pk')
        return get_object_or_404(Review, id=pk)

    def put(self, request, *args, **kwargs):
        # Handle PUT requests (full update)
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        # Handle PATCH requests (partial update)
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Ensure that the request method is PUT
        if request.method == 'PUT':
            response = super().update(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                return Response({'detail': 'Review updated successfully.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)


# delete Review
'''
Only users who are Customers and who created the review can delete their own review
'''


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCustomer, IsCustomerReviewOwner])
def deleteReview(request, pk):
    try:
        review = get_object_or_404(Review, id=pk)
    except Review.DoesNotExist:
        return Response({'detail': 'Review not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Delete the product
    review.delete()

    return Response({'detail': 'Review deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


"""
CHATS
"""

# Create a new conversation by a customer


class ConversationCreateView(generics.CreateAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def perform_create(self, serializer):
        # Add the customer to the participants list
        conversation = serializer.save(participants=[self.request.user])

        # Notify the WebSocket consumers about the new conversation
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                'type': 'conversation_created',
                'conversation_id': conversation.id,
            }
        )

# List and create messages within a conversation


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return Message.objects.filter(conversation_id=conversation_id)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = Conversation.objects.get(pk=conversation_id)

        # Ensure that the user sending the message is a participant in the conversation
        if self.request.user in conversation.participants.all():
            message = serializer.save(
                sender=self.request.user, conversation=conversation)

            # Notify the WebSocket consumers about the new message
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'text': message.text,
                        'sender': message.sender.username,
                        'timestamp': message.timestamp.isoformat(),
                    }
                }
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "You are not a participant in this conversation."},
                            status=status.HTTP_403_FORBIDDEN)
