import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.crypto import get_random_string
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.exceptions import NotAcceptable
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Create your models here.

User = get_user_model()


class PhoneNumber(models.Model):
    user = models.OneToOneField(User, related_name="phone", on_delete=models.CASCADE)
    phone_number = PhoneNumberField(unique=True)
    verification_code = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.phone_number.as_e164)

    def generate_code(self):
        """
        Generate a unique random verification code for the given TOKEN_LENGTH in the settings.
        """
        token_length = getattr(settings, "TOKEN_LENGTH", 6)
        return get_random_string(length=token_length, allowed_chars="0123456789")
    
    def is_code_expired(self):
        """
        Check if the verification code has expired.
        """
        expiration_time = self.sent_at + datetime.timedelta(minutes=getattr(settings, "TOKEN_EXPIRE_MIN", 10))
        return expiration_time <= timezone.now()

    def send_verification_code(self):
        """
        Send the verification code to the user's phone number using the Twilio API.
        see https://www.twilio.com/docs/sms/quickstart/python for more information.
        """
        twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_messaging_service_sid = settings.TWILIO_MSG_SERVICE_SID

        self.verification_code = self.generate_code()

        if all([twilio_account_sid, twilio_auth_token, twilio_messaging_service_sid]):
            try:
                client = Client(twilio_account_sid, twilio_auth_token)
                client.messages.create(
                    to=str(self.phone_number),
                    from_=twilio_messaging_service_sid,
                    body=f"Your verification code is: {self.verification_code}",
                )
                self.sent_at = timezone.now()
                self.save()
            except TwilioRestException as e:
                print(e)
        else:
            print("Twilio credentials not found, check them and try again.")

    def check_verification_code(self, code):
        """
        Verify the provided code against the stored verification code.

        This method checks if the code provided by the user matches the stored verification code,
        whether the code has expired, and if the phone number has already been verified.
        """
        if self.is_verified:
            raise NotAcceptable("The phone number is already verified.")
        
        if code != self.verification_code:
            raise NotAcceptable("The verification code you entered is incorrect.")
        

        if self.is_code_expired():
            raise NotAcceptable("The verification code has expired.")
        
        self.is_verified = True
        self.save()

        return self.is_verified
