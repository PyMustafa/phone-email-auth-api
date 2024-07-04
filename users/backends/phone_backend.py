from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException


User = get_user_model()


class PhoneBackend(ModelBackend):
    """
    Authenticates users based on their phone number and password.

    This class subclasses `ModelBackend` and overrides the `authenticate` method
    to authenticate users based on their phone number and password.

    """

    def authenticate(self, request, username=None, password=None):
        try:
            phone_number = phonenumbers.parse(username, settings.PHONENUMBER_DEFAULT_REGION)
            if not phonenumbers.is_valid_number(phone_number):
                return None
            
            try:  # check if user exists
                user = User.objects.get(phone__phone_number=phone_number)
            except User.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user

        except NumberParseException:
            return None