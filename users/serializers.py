from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.exceptions import (
    NotFound,
    AuthenticationFailed,
    PermissionDenied,
)
from rest_framework.validators import UniqueValidator
from dj_rest_auth.registration.serializers import RegisterSerializer
from phonenumber_field.serializerfields import PhoneNumberField

from .models import PhoneNumber

User = get_user_model()


class UserRegisterSerializer(RegisterSerializer):
    """
    Serializer for user registration using email and/or phone number.

    Extends the dj-rest-auth RegisterSerializer to include phone number registration.
    """

    email = serializers.EmailField(required=False)
    phone_number = PhoneNumberField(
        required=False,
        write_only=True,
        validators=[
            UniqueValidator(
                queryset=PhoneNumber.objects.all(),
                message="A user with this phone number already exists.",
            )
        ],
    )

    def validate(self, validated_data):
        """
        Validate the registration data.

        Ensures that either email or phone number is provided and passwords match.
        """
        email = validated_data.get("email", None)
        phone_number = validated_data.get("phone_number", None)
        
        if not (email or phone_number):
            raise serializers.ValidationError("Either email or phone number is required.")
        
        if validated_data.get("password1") != validated_data.get("password2"):
            raise serializers.ValidationError("Passwords do not match.")
        
        return validated_data
    
    def get_cleaned_data_extra(self):
        """
        Get additional cleaned data for registration.
        """
        return {
            'phone_number': self.validated_data.get("phone_number", '')
        }

    def create_phone_number(self, user, validated_data):
        """
        Create a PhoneNumber instance for the user.
        """
        phone_number = validated_data.get("phone_number")
        if phone_number:
            PhoneNumber.objects.create(
                user=user,
                phone_number=phone_number
            )
            user.phone.save()

    def custom_signup(self, request, user):
        """
        Perform custom signup actions.

        Creates a PhoneNumber instance for the user if a phone number was provided.
        """
        self.create_phone_number(user, self.get_cleaned_data_extra())


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login using email or phone number.
    """

    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def _validate_email_and_phone_number(self, email, phone_number, password):
        """
        Validate the email/phone number and password combination.
        """
        user = None
        if email and password:
            user = authenticate(username=email, password=password)
        elif str(phone_number) and password:
            user = authenticate(username=str(phone_number), password=password)
        else:
            raise serializers.ValidationError("Must include 'email' or 'phone_number' and 'password'.")
        
        return user

    def validate(self, validated_data):
        """
        Validate the login data.

        Checks the provided credentials and ensures the user account is active and verified.
        """
        phone_number = validated_data.get('phone_number')
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = self._validate_email_and_phone_number(email, phone_number, password)

        if not user:
            raise AuthenticationFailed("Invalid login credentials.")
        
        if not user.is_active:
            raise PermissionDenied("User account is disabled.")
        
        if email:
            email_address = user.emailaddress_set.filter(email=user.email, verified=True).exists()
            if not email_address:
                raise serializers.ValidationError("Email address is not verified.")
        else:
            if not user.phone.is_verified:
                raise serializers.ValidationError("Phone number is not verified.")
            
        validated_data["user"] = user
        return validated_data


class PhoneNumberSerializer(serializers.ModelSerializer):
    """
    Serializer for phone number validation.
    """

    phone_number = PhoneNumberField()

    class Meta:
        model = PhoneNumber
        fields = ("phone_number",)

    def validate_phone_number(self, phone_number):
        """
        Validate the phone number.

        Checks if the phone number is registered and not already verified.
        """
        try:
            queryset = User.objects.get(phone__phone_number=phone_number)
            if queryset.phone.is_verified:
                raise serializers.ValidationError("Phone number already verified.")
        
        except User.DoesNotExist:
            raise NotFound("The account is not registered.")

        return phone_number


class VerifyPhoneNumberSerializer(serializers.Serializer):
    """
    Serializer for verifying a phone number with a code.
    """

    phone_number = PhoneNumberField()
    code = serializers.CharField(max_length=getattr(settings, "TOKEN_LENGTH", 6))

    def validate_phone_number(self, phone_number):
        """
        Validate the phone number.

        Checks if the phone number is registered.
        """
        queryset = User.objects.filter(phone__phone_number=phone_number)
        if not queryset.exists():
            raise NotFound("this phone number is not registered.")
        return phone_number
    
    def validate(self, validated_data):
        """
        Validate the phone number and verification code.
        """
        phone_number = str(validated_data.get('phone_number'))
        code = validated_data.get('code')

        queryset = PhoneNumber.objects.get(phone_number=phone_number)
        queryset.check_verification_code(code=code)

        return validated_data