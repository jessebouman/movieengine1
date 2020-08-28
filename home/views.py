from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt

from scripts.search import handle_search
from . import forms

@csrf_exempt
def home(request):
    """
    Landing (splash) page
    Displays a form to enter the names of two unique actors
    """

    # Actor search form
    if request.method == 'POST':
        form = forms.ActorSearch(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            return redirect(reverse('result', args=[*list(cleaned.values())]))
    else:
        form = forms.ActorSearch()


    context = {
            'form': form
            }
    return render(request, 'home.html', context)

def result(request, **actors):
    """
    Finds the result of the two actors entered on the homepage
    Displays a loading spinner during search, then redirects to result/no result page

    Parameters
    ----------
    actors : dict
        A dictionary of actors to lookup
    """

    result = handle_search(actors['first_actor'], actors['second_actor'])

    context = {
            'actors': result[1],
            'movies': result[0]
            }
    return render(request, 'result.html', context)