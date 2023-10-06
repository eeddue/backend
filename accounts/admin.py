from django.contrib import admin
from accounts.models import User, Profile, UserRole, PaymentPlan
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']


class ProfileAdmin(admin.ModelAdmin):
    list_editable = ['verified']
    list_display = ['user', 'full_name', 'role', 'payment_plan', 'plan_expiration_date',
                    'pharmacies_created', 'products_created', 'verified']


admin.site.register(User, UserAdmin)
admin.site.register(UserRole)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(PaymentPlan)
