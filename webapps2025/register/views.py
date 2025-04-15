from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from .forms import AccountSetupForm
from .models import Account
from decimal import Decimal

#register
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('account_setup')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register/register.html', {'form': form})



#account setup
CONVERSION_RATES = {
    'GBP': Decimal('1.0'),
    'USD': Decimal('1.32'),
    'EUR': Decimal('1.17'),
}

def account_setup(request):
    if request.method == 'POST':
        form = AccountSetupForm(request.POST)
        if form.is_valid():
            currency = form.cleaned_data['currency']
            gbp_amount = Decimal('1000.00')
            converted = gbp_amount * CONVERSION_RATES[currency]

            Account.objects.create(
                user=request.user,
                currency=currency,
                balance=converted
            )
            return redirect('home')  # or wherever you want
    else:
        form = AccountSetupForm()

    return render(request, 'register/account_setup.html', {'form': form})
