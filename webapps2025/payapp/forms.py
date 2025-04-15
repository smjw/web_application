from django import forms
from django.contrib.auth.models import User


class PaymentForm(forms.Form):
    recipient_username = forms.CharField(label="Recipient Username")
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    message = forms.CharField(widget=forms.Textarea, required=False)

    

class PaymentRequestForm(forms.Form):
    recipient_username = forms.CharField(max_length=150, label="Recipient Username")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    message = forms.CharField(widget=forms.Textarea, required=True)

