from django.urls import path
from .views import home
from django.contrib.auth import views as auth_views
from . import views




urlpatterns = [
    path('', home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='payapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('make_payment/', views.make_payment, name='make_payment'),
    path('request_payment/', views.request_payment, name='request_payment'),
    path('request/', views.request_payment, name='request_payment'),
    path('payment_request/<int:payment_request_id>/accept/', views.accept_payment_request, name='accept_payment_request'),
    path('payment_request/<int:payment_request_id>/confirm/', views.confirm_payment_request, name='confirm_payment_request'),
    path('payment_request/<int:payment_request_id>/decline/', views.decline_payment_request, name='decline_payment_request'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
    path('customadmin/users/', views.admin_view_users, name='admin_view_users'),
    path('customadmin/transactions/', views.admin_view_transactions, name='admin_view_transactions'),
    path('customadmin/register/', views.register_admin, name='register_admin'),

    path('conversion/<str:currency1>/<str:currency2>/<str:amount>/', views.convert_currency, name='convert_currency'),


    
]
