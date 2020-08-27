# -*- coding: utf-8 -*-
from django import forms

class ActorSearch(forms.Form):
    first_actor = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'First actor'
                            }
                    ),
            label='',
            required=True
            )

    second_actor = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'Second actor'
                            }
                    ),
            label='',
            required=False
            )