from django.shortcuts import render, reverse, redirect
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage

import os
import stripe

from scripts.postgres import SELECT, UPDATE

stripe.api_key = os.environ['STRIPE_SECRET'] # Stripe API key should be stored securely in the environment

def cancelled(request):
    """
    View for any cancelled purchases
    """
    return render(request, 'cancelled.html', {})

def success(request):
    """
    View for successful purchases.
    Gets the Stripe session ID from the URL params, checks to ensure the payment was successful,
    updates item information in the database, and sends receipts.
    Returns an error page if the payment was unsuccessful or redirects to the home page if
    the page is accessed without a session_id.
    """
    if 'session_id' in request.GET:
        try:
            # Retrieve session object
            session = stripe.checkout.Session.retrieve(request.GET['session_id'])

            # Retrieve payment intent and check if successful
            payment = stripe.PaymentIntent.retrieve(session['payment_intent'])
        except:
            print('Invalid payment')
            return redirect(reverse('home'))

        # Check if payment was successful
        succeeded = bool(payment['status'] == 'succeeded')
        context = {'succeeded': succeeded}

        if succeeded:
            # Update DB (change price to -1)
            name = session['display_items'][0]['custom']['name']
            UPDATE('item', where=f"name = '{name}'", cols='price', vals='-1')

            # Send email to owner with customer info
            shipping = session['shipping']['address']
            customer_email = payment['charges']['data'][0]['billing_details']['email']
            customer_name = payment['charges']['data'][0]['billing_details']['name']
            receipt = payment['charges']['data'][0]['receipt_url']
            message = f"""
            Product: {name}

            Customer: {customer_name}
            Email: {customer_email}

            Address:
                {shipping['line1']}
                {shipping['line2']}
                {shipping['city']}, {shipping['state']} {shipping['postal_code']}

            Receipt: {receipt}
            """

            email = EmailMessage(
                        subject='[CUSTOMER PURCHASE]',
                        body=message,
                        to=['email@gmail.com'],
                        reply_to=[customer_email]
                    )
            email.send(fail_silently=True)
        else:
            # Retrieve and display product information for the failed purchase
            context.update({'item': SELECT('item', where=f"name = '{session['display_items'][0]['custom']['name']}'")['id']})

        return render(request, 'success.html', context)
    else:
        return redirect(reverse('home'))

@csrf_exempt
def create_checkout_session(request):
    """
    When the "Purchase" button is pressed on the frontend, returns a token with the Stripe session_id
    """
    if request.method == 'GET':
        # Get item information from DB
        item_id = request.GET['item']
        item = SELECT('item', where=f'id = {item_id}')

        domain_url = 'http://localhost:8000/store/' # BUG (replace with production URL)
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                shipping_address_collection={
                        'allowed_countries': ['US']
                        },
                line_items=[
                    {
                        'name': item['name'],
                        'quantity': 1,
                        'currency': 'usd',
                        'amount': str(int(item['price']*100)),
                        'images': [item['photo_primary']] + item['photos']
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_config(request):
    """
    Returns Stripe config information to the frontend
    """
    if request.method == 'GET':
        stripe_config = {'publicKey': os.environ['STRIPE_KEY']}
        return JsonResponse(stripe_config, safe=False)