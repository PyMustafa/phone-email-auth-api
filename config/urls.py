"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from dj_rest_auth.registration.views import VerifyEmailView, ResendEmailVerificationView
from dj_rest_auth.views import PasswordChangeView, PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api-v1/user/', include('users.urls', namespace='users_api')),
    path('api-v1/rest-auth/', include('rest_framework.urls'), name='rest_framework'),

    path('api-v1/resend-email/', ResendEmailVerificationView.as_view(), name='resend_email'),
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$', VerifyEmailView.as_view(), name='account_confirm_email'),
    path('account-email-verification-sent/', TemplateView.as_view(), name='account_email_verification_sent'),

    path('api-v1/password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('api-v1/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('api-v1/password/reset/confirm/<str:uidb64>/<str:token>', 
         PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
]


if getattr(settings, 'REST_USE_JWT', False):

    from rest_framework_simplejwt.views import TokenVerifyView
    from dj_rest_auth.jwt_auth import get_refresh_view

    urlpatterns += [
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        path('token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
    ]
