from rest_framework import serializers
from phonenumber_field import serializerfields


class OtpSerializer(serializers.Serializer):
    phone_number = serializerfields.PhoneNumberField(max_length=15)
    otp = serializers.CharField(max_length=6, min_length=6, allow_blank=False, required=False)
    via_referral_code = serializers.CharField(max_length=6, min_length=6, allow_blank=False, required=False)
    is_signup = serializers.BooleanField(required=False)
    firebase_token = serializers.CharField(max_length=250, required=False, allow_blank=True)

    def validate_via_referral_code(self, value):
        if not value.startswith('R'):
            raise serializers.ValidationError("invalid referral code")
        return value

    def validate(self, attrs):
        if 'otp' not in attrs and 'is_signup' not in attrs:
            raise serializers.ValidationError("please provide is_signup flag as true/false.")
        data = super().validate(attrs)
        return data
