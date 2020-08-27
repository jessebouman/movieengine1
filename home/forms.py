# -*- coding: utf-8 -*-
from django import forms

class Contact(forms.Form):
    first_name = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'First'
                            }
                    ),
            label='Name',
            required=True
            )

    last_name = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'Last'
                            }
                    ),
            label='',
            required=False
            )

    email = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control',
                            'type': 'email',
                            }
                    ),
            label=f'Email',
            required=True)

    message = forms.CharField(
            widget=forms.Textarea(
                    attrs={'class': 'form-control'}
                    ),
            label='Message',
            required=True)