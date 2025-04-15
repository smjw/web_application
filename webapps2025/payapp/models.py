from django.db import models, transaction
from django.contrib.auth.models import User
from register.models import Account



#make a payment
class Payment(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_payments')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sender.username} paid {self.recipient.username} {self.amount}"



#paymenr request
class PaymentRequest(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Account.CURRENCY_CHOICES, null=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending')

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} Payment Request"





#notifcaions 
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    cleared = models.BooleanField(default=False)
    related_request = models.ForeignKey('PaymentRequest', on_delete=models.CASCADE, null=True, blank=True)


    #requests for payment
    is_payment_request = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')],
        default='pending'
    )
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_made', null=True, blank=True)