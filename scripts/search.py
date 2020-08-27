# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 12:17:52 2020

Script to handle searching, sorting, and filtering of ecommerce items

@author: Spencer Ferguson-Dryden
"""
from django import forms

def handle_search(form, **kwargs):
    """
    Handles search/sort/filter input.

    Parameters
    ----------
    form : dict
        TThe cleaned data from the search/sort/filter form

    Returns
    -------
    where
        a string containing the WHERE clause of the SQL query
    order
        a string containing the ORDER BY clause of the SQL query
    """

    # Construct WHERE clause from search
    search = f"({form['search_by']} ILIKE '%{form['search']}%')" if form['search'] else ''

    # Construct WHERE clause from _filter
    lo = str(float(form['price_filer_lo'])) if form['price_filter_lo'] else None
    hi = str(float(form['price_filter_hi'])) if form['price_filter_hi'] else None
    if lo and hi:
        price_filter = f'(price BETWEEN {lo} AND {hi})'
    elif lo:
        price_filter = f'(price >= {lo})'
    elif hi:
        price_filter = f'(price <= {hi})'
    else:
        price_filter = ''

    # Add for sale/out of stock result option to query
    if price_filter and form['for_sale']:
        price_filter += ' OR (price = -1)'
    elif price_filter and not form['for_sale']:
        price_filter += ' AND (price != -1)'

    if search and price_filter:
        # The user submits a search and a filter query
        where = search + ' AND ' + price_filter
    elif search or price_filter:
        # The user submits either a search or a filter query (exclusive)
        where = search + price_filter
    else:
        # The user submits no search or filter query, only an ORDER BY query
        where = None

    # Construct ORDER BY clause
    order_by = form['sort']
    order_dir = form['sort_order']
    order = f'ORDER BY {order_by} {order_dir}'

    return where, order

class Search(forms.Form):
    """
    SEARCH BY: name, description
    FILTER BY: price (from/to)
    SORT BY: name (A-Z, Z-A), id (new-old, old-new), price (low-hi, hi-low)
    """
    search = forms.CharField(
            widget=forms.TextInput(
                    attrs={
                            'class': 'form-control w-auto',
                            'placeholder': 'Search...'
                            }
                    ),
            required=False
            )
    search_by = forms.ChoiceField(
            widget=forms.Select(
                    attrs={
                            'class': 'form-control w-75',
                            'value': 'name'
                            },
                    ),
            choices=[('name', 'Name'), ('description', 'Description')],
            required=False
            )

    price_filter_lo = forms.DecimalField(
            widget=forms.NumberInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'From'
                            }
                    ),
            label='Price',
            required=False
            )
    price_filter_hi = forms.DecimalField(
            widget=forms.NumberInput(
                    attrs={
                            'class': 'form-control',
                            'placeholder': 'To'
                            }
                    ),
            required=False
            )
    for_sale = forms.BooleanField(
            widget=forms.CheckboxInput(
                    attrs={'class': 'form-check-input'}
                    ),
            label='Include items not for sale?',
            initial=True,
            required=False
            )

    sort = forms.ChoiceField(
            widget=forms.Select(
                    attrs={
                            'class': 'form-control',
                            'value': 'date'
                            }
                    ),
            choices=[('id', 'Date'), ('name', 'Name'), ('price', 'Price')],
            required=False
            )
    sort_order = forms.ChoiceField(
            widget=forms.RadioSelect(
                    attrs={'class': 'form-check-input'}
                    ),
            choices=[('DESC', 'Descending'), ('ASC', 'Ascending')],
            initial='DESC',
            required=False
            )
