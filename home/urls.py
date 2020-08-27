# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gallery', views.gallery, name='gallery'),
    path('gallery/item/<int:item_id>', views.item_detail, name='item_detail'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
]

