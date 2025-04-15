from django.urls import path
from .views import register
from .views import account_setup
from payapp.views import home


urlpatterns = [
    path('', home, name='home'),
    path("register/", register, name="register"),
    path('account-setup/', account_setup, name='account_setup'),

]
