from django.shortcuts import get_object_or_404
from accounts.models import User
from api.models import Product, Category, Pharmacy, Review, Location, Contact
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


# MODEL SERIALIZERS

# contact
class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

# CATEGORY


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)


# REVIEWS


class ReviewedProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'category', 'img')

# GET (all and by id)


class ReviewGetSerializer(serializers.ModelSerializer):
    reviewee = ReviewedProductSerializer()
    reviewer = UserSerializer()

    class Meta:
        model = Review
        fields = ('id', 'review', 'rate', "reviewer", 'reviewee', 'created_at')

# Post review


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

# Update review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['review', 'rate']

# LOCATION


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('lat', 'lon')


# PHARMACY

# ADD/POST


class UserCustomSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class PharmacyCreateSerializer(serializers.ModelSerializer):
    owned_by = UserCustomSerializer(read_only=True)

    class Meta:
        model = Pharmacy
        fields = '__all__'

# GET


class PharmacyGetSerializer(serializers.ModelSerializer):
    location = LocationSerializer()  # nested serializer for location
    owned_by = UserCustomSerializer()

    class Meta:
        model = Pharmacy
        fields = ('id', 'owned_by', 'pharmacy_name', 'phone_number', 'location', 'working_hours_start', 'working_hours_stop',
                  'owner_name', 'owner_license', 'product_count', 'review_count', 'rating', 'pharm_img')


class PharmacyUpdateSerializer(serializers.ModelSerializer):
    # location = LocationSerializer()  # nested serializer for location

    class Meta:
        model = Pharmacy
        fields = ('pharmacy_name', 'phone_number', 'working_hours_start', 'working_hours_stop',
                  'owner_name', 'pharm_img')


# PRODUCTS

# GET

class ProductGetSerializer(serializers.ModelSerializer):
    owner = PharmacyGetSerializer()
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = ('id', 'name', 'description',
                  'price', 'category', 'owner', 'img')


# ADD/POST


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'img']
        read_only_fields = ['owner']

    def create(self, validated_data):
        # Get the authenticated user (pharmacy owner)
        owner = self.context['request'].user

        # Assuming you have a valid pharmacy_id in the request data
        pharmacy_id = self.context['request'].data.get('owner')

        # Retrieve the pharmacy based on the pharmacy_id
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, owned_by=owner)

        # Create the new product and set the owner to the associated pharmacy
        product = Product.objects.create(owner=pharmacy, **validated_data)
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'img']
