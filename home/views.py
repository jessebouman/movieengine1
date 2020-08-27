from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage

from scripts.postgres import SELECT
from scripts import search
from . import forms

@csrf_exempt
def contact(request):
    """
    Basic contact page that takes a name, email, and message and sends the message as an email
    to the site owner.
    """
    if request.method == 'POST':
        contact_form = forms.Contact(request.POST)
        if contact_form.is_valid():
            cleaned = contact_form.cleaned_data

            message = f"""
            Name: {cleaned['first_name']} {cleaned['last_name']}

            Message:
            {cleaned['message']}

            (Press to reply to automatically reply to sender)
            """

            email = EmailMessage(
                        subject='[Site Visitor Message]',
                        body=message,
                        to=['email@gmail.com'],
                        reply_to=[cleaned['email']]
                    )
            email.send(fail_silently=True)
            return redirect(reverse('contact'))
    else:
      contact_form = forms.Contact()

    context = {
            'form': contact_form
            }
    return render(request, 'contact.html', context)

@csrf_exempt
def gallery(request):
    """
    Returns a view for the main product browsing/viewing page
    By default, shows all products in chronological order (new -> old)
    Handles search/sort/filter input if submitted by user
    """
    # Build search query if the form is filled out, otherwise use defaults
    if request.method == 'POST' and 'clear' not in request.POST:
        search_form = search.Search(request.POST)
        if search_form.is_valid():
            query = search_form.cleaned_data
            where, order_by = search.handle_search(query)
    else:
        search_form = search.Search()
        where, order_by = None, 'ORDER BY id DESC' # Default: select all, order by date (desc)

    # Select items
    try:
        items = SELECT('item', where=where, extra=order_by)
    except:
        items = []
    # If only one item returned, make it a list to avoid edgecases on the frontend template
    if not isinstance(items, list):
        items = [items]

    context = {
            'items': items,
            'search': search_form
            }
    return render(request, 'gallery.html', context)

def item_detail(request, item_id):
    """
    Returns a view of a specific product, based on the URL parameter.
    """
    # Select product based on URL param
    item = SELECT('item', where=f'id = {item_id}', _print=False)

    context = {
            'item': item,
            'photos': [item['photo_primary']] + item['photos']
            }
    return render(request, 'item_detail.html', context)

def home(request):
    """
    Landing (splash) page
    """
    return render(request, 'home.html', {})

def about(request):
    """
    About page
    """
    return render(request, 'about.html', {})