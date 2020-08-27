from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from . import forms
from .scripts import scripts
from scripts.postgres import SELECT, DELETE
from scripts import search
from cosmo.settings import LOGIN_URL

def logout_view(request):
    """
    Logs out the user
    """
    logout(request)
    return redirect(reverse('landing'))

@login_required(redirect_field_name=LOGIN_URL)
@csrf_exempt
def portal(request):
    """
    View for main admin dashboard.
    By default, displays all products and their information in a table.
    Handles search/sort/filter input to limit the number of products shown
    """
    # Search/sort/filter handler
    if request.method == 'POST' and 'clear' not in request.POST:
        search_form = search.Search(request.POST)
        if search_form.is_valid():
            query = search_form.cleaned_data
            where, order_by = search.handle_search(query)
    else: # Defaults to all products in chronological order (new -> old)
        search_form = search.Search()
        where, order_by = None, 'ORDER BY id DESC'

    # Select items
    try:
        items = SELECT('item', where=where, extra=order_by)
    except:
        items = []
    if not isinstance(items, list):
        items = [items]

    # Item deletion
    if request.method == 'POST' and 'delete' in request.POST:
        print(request.POST, 'DELETE ITEM') # Exact task on delete specific to client

    context = {
            'items': items,
            'search': search_form
            }
    return render(request, 'portal.html', context)

@login_required(redirect_field_name=LOGIN_URL)
def new_item(request):
    """
    View for item creation
    """
    if request.method == 'POST':
        item_form = forms.NewItem(request.POST, request.FILES)
        files = request.FILES.getlist('photos') # get uploaded photos from request
        if item_form.is_valid():
            cleaned = item_form.cleaned_data
            scripts.handle_new_item(cleaned, files) # handle creation in separate script
        return redirect(reverse('portal')) # redirect to dashboard
    else:
       item_form = forms.NewItem()

    return render(request, 'new_item.html', {'form': item_form})

@login_required(redirect_field_name=LOGIN_URL)
@csrf_exempt
def edit_item(request, item_id):
    """
    View to edit or delete an item
    """
    # Select item based on URL param
    item = SELECT('item', where=f'id = {item_id}', _print=False)

    # General content editing
    if request.method == 'POST' and 'edit' in request.POST:
        edit_form = forms.EditItem(request.POST, request.FILES,
                                  title=item['name'],
                                  description=item['description'],
                                  price=item['price']
                                  )
        if edit_form.is_valid():
            cleaned = edit_form.cleaned_data
            scripts.handle_edit_item(item['id'], cleaned) # Handle item metadata edits
            return redirect(reverse('portal'))
    else:
        edit_form = forms.EditItem(
                title=item['name'],
                description=item['description'],
                price=item['price']
                )

    # Secondary photos additions/deletions
    if request.method == "POST" and 'photos' in request.POST:
        add_photos = forms.AddNewPhotos(request.POST, request.FILES)
        files = request.FILES.getlist('photos')
        if add_photos.is_valid():
            scripts.handle_photo_edit(item, request.POST.getlist('deleted_photos'), files)             # Handle photo upload/deletions
            return redirect(reverse('portal'))
    else:
        add_photos = forms.AddNewPhotos()

    # Delete the entire item
    if request.method == "POST" and 'delete' in request.POST:
        DELETE('item', where=f'id = {item_id}')

    context = {
            'item': item,
            'edit': edit_form,
            'add_photos': add_photos,
            }
    return render(request, 'edit_item.html', context)
