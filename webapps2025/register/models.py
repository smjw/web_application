from django.db import models
from django.contrib.auth.models import User


# accounts model
class Account(models.Model):
    CURRENCY_CHOICES = [
        ('GBP', 'Pounds (£)'),
        ('USD', 'Dollars ($)'),
        ('EUR', 'Euros (€)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username}'s Account"
