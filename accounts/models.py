from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from decimal import Decimal
from django.db.models import Avg
from django.db.models.signals import post_save

#  Create your models here


# payment plan choices
PLANS = [
    ('free', 'Free'),
    ('basic', 'Basic'),
    ('premium', 'Premium'),
    ('platinum', 'Platinum'),
]


class PaymentPlan(models.Model):
    name = models.CharField(max_length=20, choices=PLANS, default='free')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


ROLES = [
    ('Customer', 'Customer'),
    ('Pharmacist', 'Pharmacist'),
]


class UserRole(models.Model):
    name = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return self.name

# User JWT authenticated


class User(AbstractUser):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    # reset password
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_created_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def profile(self):
        profile = Profile.objects.get(user=self)

    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True)

    def is_customer(self):
        return self.role.name == 'Customer'

    def is_pharmacist(self):
        return self.role.name == 'Pharmacist'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=1000)
    bio = models.CharField(max_length=100)
    # image = models.ImageField(upload_to="user_images/",
    #                           default="avatar.jpg", null=True)
    role = models.CharField(max_length=20, default='Customer')
    payment_plan = models.ForeignKey(
        PaymentPlan, on_delete=models.SET_NULL, null=True, blank=True)
    pharmacies_created = models.PositiveIntegerField(default=0)
    products_created = models.PositiveIntegerField(default=0)
    plan_expiration_date = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
