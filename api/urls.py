from django.urls import re_path as url, path, include
from . import views

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from django.urls import path, re_path
from rest_framework import permissions


api_patterns = [
    # ...
    path('test/', views.testEndPoint, name='test'),
    path('contact/', views.send_contact_email, name='contact'),

    # products
    path("products/", views.productList, name='product-list'),
    path('product/<str:pk>', views.productDetail, name='product-detail'),
    path('pharmacist-products/', views.pharmacist_products,
         name='pharmacist-products'),
    path('products/create', views.ProductCreateView.as_view()),
    path('product/<int:pk>/update', views.ProductUpdateView.as_view()),
    path('product/delete/<int:pk>',
         views.deleteProduct, name='delete-product'),

    # pharmacies
    path("pharmacies/", views.getPharmacy),
    path('user-pharmacies/', views.userPharmacies, name='user_pharmacies'),
    path("pharmacy/<str:pk>", views.pharmacyDetail, name='pharmacy-detail'),
    path("pharmacies/create", views.PharmacyCreateView.as_view()),
    path("pharmacy/<int:pk>/update", views.PharmacyUpdateView.as_view()),
    path("pharmacy/delete/<str:pk>", views.deletePharmacy, name='delete-pharmacy'),

    # reviews
    path("reviews/", views.reviewtList),
    path('review/<str:pk>', views.reviewDetail, name='detail-detail'),
    path('review/<int:pk>/update',
         views.ReviewUpdateView.as_view(), name='update-review'),
    path('reviews/create/', views.ReviewCreateView.as_view()),
    path('review/delete/<int:pk>', views.deleteReview, name='delete-review'),

    # chat
    path('conversations/', views.ConversationCreateView.as_view(),
         name='conversation-list-create'),
    path('conversations/<int:conversation_id>/messages/',
         views.MessageListCreateView.as_view(), name='message-list-create'),
]


urlpatterns = [
    url(r'^$', views.getRoutes, name='index'),
    url(r'^', include(api_patterns)),
]
