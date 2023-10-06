from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from decimal import Decimal
from django.db.models import Avg
from django.db.models.signals import post_save
from accounts.models import User


# CATEGORY
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# LOCATION
class Location(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()

    def __str__(self):
        return f"Lat: {self.lat}, Lon: {self.lon}"


# PHARMACY
class Pharmacy(models.Model):
    email = models.EmailField(unique=True)
    owned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    pharmacy_name = models.CharField(
        max_length=255,
        unique=True,
        error_messages={
            'unique': 'Name already exists.'})
    phone_number = models.CharField(
        max_length=15,
        validators=[
            MinLengthValidator(
                limit_value=10, message="Phone number must have at least 10 characters."),
            MaxLengthValidator(
                limit_value=15, message="Phone number cannot exceed 15 characters.")
        ]
    )
    # location = models.FloatField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE)
    working_hours_start = models.TimeField(default="08:00")
    working_hours_stop = models.TimeField(default="20:00")
    pharm_img = models.ImageField(
        upload_to='pharmacy_images/', default='pharmacy.jpg')
    owner_name = models.CharField(max_length=255)
    owner_id_number = models.CharField(
        max_length=8,
        validators=[
            MinLengthValidator(
                limit_value=7, message="Owner ID must have at least 7 characters."),
            MaxLengthValidator(
                limit_value=8, message="Owner ID cannot exceed 8 characters.")
        ]
    )

    owner_license = models.CharField(max_length=255, unique=True)
    product_count = models.BigIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal(0.0),
        validators=[
            MinValueValidator(limit_value=Decimal(0.0),
                              message="Rating must be at least 0.0."),
            MaxValueValidator(limit_value=Decimal(5.0),
                              message="Rating cannot exceed 5.0.")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # rate

    def calculate_average_rating(self):
        reviews = Review.objects.filter(reviewee__owner=self)
        total_rating = sum(review.rate for review in reviews)
        num_reviews = reviews.count()

        if num_reviews > 0:
            self.rating = Decimal(total_rating / num_reviews)
        else:
            self.rating = Decimal(0.0)

        self.save()

    def __str__(self):
        return self.pharmacy_name

# PRODUCT


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    owner = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='product_images/', default='drug.jpg')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # Update total_product in the Pharmacy model
    def save(self, *args, **kwargs):
        # Call the original save method to save the product
        super(Product, self).save(*args, **kwargs)

        # Update the associated pharmacy's total_products count
        self.owner.product_count = Product.objects.filter(
            owner=self.owner).count()
        self.owner.save()


# REVIEWS

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    reviewee = models.ForeignKey(Product, on_delete=models.CASCADE)
    review = models.TextField()
    rate = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.reviewee.name}"

# CONTACT FORM


class Contact(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    email_subject = models.CharField(max_length=68)
    email_body = models.TextField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email from {self.name}"
