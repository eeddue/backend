from django.urls import path
from . import views

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from django.urls import path, re_path
from rest_framework import permissions


urlpatterns = [
    # email template test
    path('email/', views.EmailView, name='email-view'),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('password-reset/', views.PasswordResetRequestView.as_view(),
         name='password_reset_request'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
]
