# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError

def validate_size(value):
    if not isinstance(value, list):
        value = [value]

    for v in value:
        if v.size >= 10485760: # For free tier of Cloudinary, 10MB limit is enforced
            raise ValidationError(
                    message="File is too large (must be less than 20MB)",
                    params={'value': value}
                    )

class NewItem(forms.Form):
    title = forms.CharField(
            widget=forms.TextInput(
                    attrs={'class': 'form-control'}
                    ),
            label='Title',
            required=True
            )
    description = forms.CharField(
            widget=forms.Textarea(
                    attrs={'class': 'form-control'}
                    ),
            label='Description',
            required=True
            )
    price = forms.DecimalField(
            widget=forms.NumberInput(
                    attrs={'class': 'form-control'}
                    ),
            label='Price',
            required=False
            )
    photo_primary = forms.ImageField(
            label='Primary Photo',
            required=True,
            validators=[validate_size]
            )
    photos = forms.ImageField(
            widget=forms.ClearableFileInput(
                    attrs={'multiple': True}
                    ),
            label='Other Photos',
            required=False,
            validators=[validate_size]
            )

class EditItem(forms.Form):
    def __init__(self, *args, **kwargs):
        title, description, price = kwargs.pop('title'), kwargs.pop('description'), kwargs.pop('price')
        super(EditItem, self).__init__(*args, **kwargs)
        self.fields['title'] = forms.CharField(
                widget=forms.TextInput(
                        attrs={
                                'class': 'form-control',
                                'value': title
                                }
                        ),
                label='Title',
                required=True
                )
        self.fields['description'] = forms.CharField(
                widget=forms.Textarea(
                        attrs={
                                'class': 'form-control',
                                'placeholder': description
                                }
                        ),
                label='Description',
                required=False
                )
        self.fields['price'] = forms.DecimalField(
                widget=forms.NumberInput(
                        attrs={
                                'class': 'form-control',
                                'value': '{:.2f}'.format(price)
                                }
                        ),
                label='Price',
                required=True
                )
        self.fields['photo_primary'] = forms.ImageField(
                label='Primary Photo',
                required=False,
                validators=[validate_size]
                )

class AddNewPhotos(forms.Form):
    photos = forms.ImageField(
            widget=forms.ClearableFileInput(
                    attrs={'multiple': True}
                    ),
            label='Add Photos',
            required=False,
            validators=[validate_size]
            )