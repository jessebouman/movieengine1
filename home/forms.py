# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError

class ActorSearch(forms.Form):
    first_actor = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control pl-3',
                            'style': 'padding-bottom: 24px; padding-top: 32px'
                            }
                    ),
            max_length=100,
            label='',
            required=True
            )

    second_actor = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control pl-3',
                            'style': 'padding-bottom: 24px; padding-top: 32px'
                            }
                    ),
            max_length=100,
            label='',
            required=True
            )

    def clean(self):
        """
        Custom cleaning method to ensure both actors are different values
        """

        # Perform standard cleaning function
        cleaned_data = super().clean()
        a, b = cleaned_data.get('first_actor'), cleaned_data.get('second_actor')

        if a and b: # both must be valid so far
            if a.lower().strip().replace(' ', '') == b.lower().strip().replace(' ', ''): # normalize strings
                raise ValidationError("Inputs must be unique.")