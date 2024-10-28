from django.contrib import admin
from django.urls import path

from dj_rest_auth.views import LogoutView

from .views import (
    UserRegistrationAPIView,
    UserLoginAPIView,
    SendResendSMSAPIView,
    VerifyPhoneNumberAPIView,
)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('send-sms/', SendResendSMSAPIView.as_view(), name='send_or_resend_sms'),
    path('verify-phone-number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),

    path('logout/', LogoutView.as_view(), name='logout'),
]
