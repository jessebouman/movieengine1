# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns= [
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session),
    path('success/', views.success),
    path('cancelled/', views.cancelled),
]
