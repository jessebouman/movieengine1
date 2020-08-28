# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('finding/actors=<str:first_actor>,<str:second_actor>', views.result, name='result'),
]

