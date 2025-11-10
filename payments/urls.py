from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('confirm/', views.confirm_payment, name='confirm_payment'),

    # Payout endpoints
    path('payouts/process/', views.process_payouts, name='process_payouts'),
    path('payouts/list/', views.list_payouts, name='list_payouts'),
]
