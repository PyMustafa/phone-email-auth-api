from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from phonenumber_field.modelfields import PhoneNumberField

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Create your models here.

user = get_user_model()


class PhoneNumber(models.Model):
    user = models.OneToOneField(user, related_name="phone", on_delete=models.CASCADE)
    Phone_Number = PhoneNumberField(unique=True)
    verification_code = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)
    sent = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.Phone_Number.as_e164)

    def generate_code(self):
        """
        Generate a unique random verification code for the given TOKEN_LENGTH in the settings.

        Returns:
            str: The generated verification code.
        """
        token_length = getattr(settings, "TOKEN_LENGTH", 6)
        return get_random_string(length=token_length, allowed_chars="0123456789")

    def send_verification_code(self):
        """
        Send the verification code to the user's phone number using the Twilio API.
        see https://www.twilio.com/docs/sms/quickstart/python for more information.
        """
        twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_phone_number = settings.TWILIO_PHONE_NUMBER

        self.verification_code = self.generate_code()

        if all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            try:
                client = Client(twilio_account_sid, twilio_auth_token)
                client.messages.create(
                    to=self.Phone_Number,
                    from_=twilio_phone_number,
                    body=f"Your verification code is: {self.verification_code}",
                )
                self.sent = timezone.now()
                self.save()
            except TwilioRestException as e:
                print(e)
        else:
            print("Twilio credentials not found")
