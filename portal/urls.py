# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 19:38:42 2020

@author: sferg
"""
from django.urls import path, include
from . import views

urlpatterns = [
        path('', views.portal, name='portal'),
        path('new', views.new_item, name='new_item'),
        path('edit/<int:item_id>', views.edit_item, name='edit_item'),
]