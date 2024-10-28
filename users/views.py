from django.contrib.auth import get_user_model

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView

from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    PhoneNumberSerializer,
    VerifyPhoneNumberSerializer,
)
from .models import PhoneNumber

User = get_user_model()


class SendSMSMixin:
    """
    A mixin that provides functionality to send SMS verification.
    im trying to apply the 'DRY' principle here if u can tell :)
    """

    def send_sms(self, phone_number):
        """
        Validate the phone number and send an SMS verification.
        """
        phone_serializer = PhoneNumberSerializer(data={'phone_number': phone_number})
        if phone_serializer.is_valid():
            user = User.objects.get(phone__phone_number=phone_number)
            sms_verification = PhoneNumber.objects.filter(user=user, is_verified=False).first()
            if sms_verification:
                sms_verification.send_verification_code()
                return True, None
        return False, phone_serializer.errors


class UserRegistrationAPIView(RegisterView, SendSMSMixin):
    """
    API view for user registration with optional SMS verification.
    """
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests for user registration.

        This method overrides the create method to handle user registration
        and optional SMS/email verification sending.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        email = request.data.get('email')
        phone_number = request.data.get('phone_number')

        response_data = {"detail": "User registered successfully."}

        if phone_number:
            sms_sent, errors = self.send_sms(phone_number)
            if sms_sent:
                response_data["detail"] = "Verification SMS sent."
                if email:
                    response_data["detail"] = "Verification e-mail and SMS sent."
            else:
                response_data["detail"] = "User registered, but failed to send SMS."
                if errors:
                    response_data["sms_errors"] = errors

        elif email:
            response_data["detail"] = "Verification e-mail sent."

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class SendResendSMSAPIView(GenericAPIView, SendSMSMixin):
    """
    API view for sending or resending SMS verification.
    """
    serializer_class = PhoneNumberSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to send/resend SMS verification.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = str(serializer.validated_data['phone_number'])
        sms_sent, errors = self.send_sms(phone_number)
        
        if sms_sent:
            return Response({"detail": "Verification SMS sent."}, status=status.HTTP_200_OK)
        return Response({"detail": "Failed to send SMS.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(LoginView):
    """
    API view for user login using email and/or phone number.
    """
    serializer_class = UserLoginSerializer


class VerifyPhoneNumberAPIView(GenericAPIView):
    """
    API view for verifying a phone number.
    """
    serializer_class = VerifyPhoneNumberSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to verify a phone number.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            message = "Phone number verified successfully."
            return Response({"detail": message}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)