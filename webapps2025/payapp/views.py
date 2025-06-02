from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from register.models import Account
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import PaymentForm
from .models import Payment, Notification, PaymentRequest
from django.contrib import messages
from django.contrib.auth.models import User
from decimal import Decimal
from payapp.models import Notification
from .forms import PaymentRequestForm
from django.http import HttpResponseForbidden
# from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests



def home(request):
    if not request.user.is_authenticated:
        return render(request, 'payapp/home.html')    

    try:
        account = request.user.account
        balance = account.balance
        currency = account.get_currency_display()

    except Account.DoesNotExist:
        account = None
        balance = None
        currency = None

    # If the user presses the "Clear All Notifications" button
    if request.method == 'POST' and 'clear_notifications' in request.POST:
        # Update the 'cleared' field for all the user's notifications
        Notification.objects.filter(user=request.user).update(cleared=True)
        messages.success(request, "All notifications cleared.")

    # Get only the notifications that are not cleared (new ones)
    notifications = Notification.objects.filter(user=request.user, cleared=False).select_related('requester').order_by('-created_at')

    prefill_user = None
    for notification in notifications:
        if "payment request" in notification.message:
            if notification.requester:
                prefill_user = notification.requester.username
            else:
                prefill_user = None

    return render(request, 'payapp/home.html', {
        'account': account,
        'balance': balance,
        'currency': currency,
        'notifications': notifications,
        'prefill_user': prefill_user
    })



#conversions api
@csrf_exempt 
def convert_currency(request, currency1, currency2, amount):
    try:
        amount = Decimal(amount)
    except:
        return JsonResponse({'error': 'Invalid amount.'}, status=400)
    
    exchange_rates = {
        'USD': {'EUR': 0.88, 'GBP': 0.76, 'USD': 1.00},
        'EUR': {'USD': 1.13, 'GBP': 0.86, 'EUR': 1.00},
        'GBP': {'USD': 1.32, 'EUR': 1.17, 'GBP': 1.00}
    }

    # valid conversions
    if currency1 not in exchange_rates or currency2 not in exchange_rates[currency1]:
        return JsonResponse({'error': 'Unsupported currency pair.'}, status=400)

    # decimal
    conversion_rate = Decimal(exchange_rates[currency1][currency2])

    #calculate conversion
    converted_amount = amount * conversion_rate

    return JsonResponse({
        'from': currency1,
        'to': currency2,
        'rate': round(conversion_rate, 2),
        'original_amount': round(amount, 2),
        'converted_amount': round(converted_amount, 2)
    })


#get conversion from my api
def get_conversion(from_currency, to_currency, amount):
    response = requests.get(
        f'http://127.0.0.1:8000/conversion/{from_currency}/{to_currency}/{amount}/'
    )
    if response.status_code == 200:
        return Decimal(response.json()['rate'])
    else:
        return None







#payment making
@login_required
def make_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['recipient_username']
            amount = form.cleaned_data['amount']
            message = form.cleaned_data['message']
            
            try:
                # Try to get the recipient account
                recipient = User.objects.get(username=recipient_username)
            except User.DoesNotExist:
                # If the recipient does not exist, show an error message
                messages.error(request, "Recipient does not exist.")
                return redirect('make_payment')

            sender_account = request.user.account
            recipient_account = recipient.account

            # Ensure the sender has enough balance for the payment
            if sender_account.balance < amount:
                messages.error(request, "Insufficient funds.")
                return redirect('make_payment')

            # Get the conversion rate from the sender's currency to the recipient's currency
            exchange_rate = get_conversion(sender_account.currency, recipient_account.currency, amount)
            
            # Check if the conversion rate is valid
            if exchange_rate is None:
                messages.error(request, "Currency conversion failed. Please try again.")
                return redirect('make_payment')

            # Perform the conversion and round the result to 2 decimal places
            converted_amount = (amount * exchange_rate).quantize(Decimal('0.01'))

            # Use atomic transactions to ensure the changes are consistent
            try:
                with transaction.atomic():
                    # Deduct the amount from the sender's account
                    sender_account.balance -= amount
                    # Add the converted amount to the recipient's account
                    recipient_account.balance += converted_amount
                    
                    # Save the changes to both accounts
                    sender_account.save()
                    recipient_account.save()

                    # Create a payment record for this transaction
                    Payment.objects.create(
                        sender=request.user,
                        recipient=recipient,
                        amount=amount,
                        message=message
                    )

                    # Create a notification for the recipient
                    Notification.objects.create(
                        user=recipient,
                        message=f"You received {recipient_account.get_currency_display()[:1]}{converted_amount} from {request.user.username}."
                    )

                    # Create a notification for the sender
                    Notification.objects.create(
                        user=request.user,
                        message=f"Payment of {sender_account.get_currency_display()[:1]}{amount} to {recipient_username} successful."
                    )

                # Show a success message to the user
                messages.success(request, f"Payment of {sender_account.get_currency_display()[:1]}{amount} to {recipient_username} successful!")
                return redirect('home')

            except Exception as e:
                # If any exception occurs during the transaction, show an error
                messages.error(request, f"An error occurred while processing the payment: {str(e)}")
                return redirect('make_payment')

    else:
        # If the request is not POST, just display the form
        form = PaymentForm()

    return render(request, 'payapp/make_payment.html', {'form': form})








#make a request
@login_required
def request_payment(request):
    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['recipient_username']
            amount = form.cleaned_data['amount']
            message = form.cleaned_data['message']  # This should now work if the form is valid

            try:
                recipient = User.objects.get(username=recipient_username)
            except User.DoesNotExist:
                messages.error(request, "Recipient does not exist.")
                return redirect('request_payment')

            # Create the PaymentRequest
            payment_request = PaymentRequest.objects.create(
                requester=request.user,
                recipient=recipient,
                amount=amount,
                message=message,
                status='pending'  # Set status to 'pending' initially
            )

            # Create a Notification for the recipient
            Notification.objects.create(
                user=recipient,
                message=f"You have a payment request from {request.user.username} for {amount} {request.user.account.currency}.",
                related_request=payment_request  # Link the request
            )

            # Create a Notification for the requester (the user who sent the request)
            Notification.objects.create(
                user=request.user,
                message=f"Your payment request to {recipient_username} for {amount} {request.user.account.currency} has been successfully sent.",
                related_request=payment_request  # Link the request
            )

            messages.success(request, f"Payment request sent to {recipient_username}!")
            return redirect('home')

    else:
        form = PaymentRequestForm()

    return render(request, 'payapp/request_payment.html', {'form': form})





@login_required
def accept_payment_request(request, payment_request_id):
    payment_request = get_object_or_404(PaymentRequest, id=payment_request_id, recipient=request.user)

    if payment_request.status != 'pending':
        messages.error(request, "This request is no longer active.")
        return redirect('home')

    return render(request, 'payapp/confirm_accept.html', {'payment_request': payment_request})

@login_required
def confirm_payment_request(request, payment_request_id):
    payment_request = get_object_or_404(PaymentRequest, id=payment_request_id, recipient=request.user)

    if payment_request.status != 'pending':
        messages.error(request, "This request is no longer active.")
        return redirect('home')

    sender_account = request.user.account
    recipient_account = payment_request.requester.account

    if sender_account.balance < payment_request.amount:
        messages.error(request, "Insufficient funds.")
        return redirect('home')

    # Perform transaction
    with transaction.atomic():
        sender_account.balance -= payment_request.amount
        recipient_account.balance += payment_request.amount
        sender_account.save()
        recipient_account.save()

        # Create payment entry
        Payment.objects.create(
            sender=request.user,
            recipient=payment_request.requester,
            amount=payment_request.amount,
            message=payment_request.message
        )

        # Update payment request status
        payment_request.status = 'accepted'
        payment_request.save()

        # Notify requester
        Notification.objects.create(
            user=payment_request.requester,
            message=f"{request.user.username} accepted and paid your request of {payment_request.amount} {sender_account.get_currency_display()}."
        )

        # Notify the recipient (the one accepting the request)
        Notification.objects.create(
            user=request.user,  # The recipient who is accepting the request
            message=f"You accepted {payment_request.requester.username}'s payment request and successfully completed the transaction of {payment_request.amount} {sender_account.get_currency_display()}."
        )

    messages.success(request, "Payment successful.")
    return redirect('home')

@login_required
def decline_payment_request(request, payment_request_id):
    payment_request = get_object_or_404(PaymentRequest, id=payment_request_id, recipient=request.user)

    if payment_request.status != 'pending':
        messages.error(request, "This request is no longer active.")
        return redirect('home')

    payment_request.status = 'declined'
    payment_request.save()

    Notification.objects.create(
        user=payment_request.requester,
        message=f"{request.user.username} declined your payment request for {payment_request.amount}."
    )

    messages.success(request, "Request declined.")
    return redirect('home')


# transaction history
@login_required
def transaction_history(request):
    # Get all payments where the logged-in user is either the sender or recipient
    transactions = Payment.objects.filter(
        sender=request.user
    ) | Payment.objects.filter(
        recipient=request.user
    )
    
    # Order by the most recent transaction
    transactions = transactions.order_by('-id')

    return render(request, 'payapp/transaction_history.html', {'transactions': transactions})





#ADMIN STUFF

# Check if user is an admin
def is_admin(user):
    return user.is_staff  

@login_required
def admin_view_users(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You are not authorized to view this page.")

    users = User.objects.all()
    return render(request, 'payapp/admin_users.html', {'users': users})

@login_required
def admin_view_transactions(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    transactions = Payment.objects.all().order_by('-timestamp')
    return render(request, 'payapp/admin_transactions.html', {'transactions': transactions})


# from django.http import HttpResponse

# def test_admin_view(request):
#     if not is_admin(request.user):
#         return HttpResponseForbidden("You are not authorized to view this page.")
#     return HttpResponse("You found the admin area!")

@login_required
def register_admin(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this page.")

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return render(request, 'payapp/admin_register.html', {'error': 'Username already taken'})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = True 
        user.is_active= True
        user.is_superuser = True
        user.save()

        return redirect('home') 

    return render(request, 'payapp/admin_register.html')

