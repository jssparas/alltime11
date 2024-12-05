from django.conf import settings
from rest_framework import serializers

from alltime11 import constants, validators
from users.models import User
from cricket.models import UserTeamContest
from cricket.models import UserTeam
from users.validators import validate_pincode, validate_state_code


class UserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(max_length=6, validators=[validate_pincode])
    state_code = serializers.CharField(max_length=5, validators=[validate_state_code])
    country = serializers.CharField(max_length=2, validators=[validators.validate_country_code])

    class Meta:
        model = User
        exclude = ["password", "last_login", "is_superuser", "groups", "user_permissions"]

        extra_kwargs = {
            "phone_number": {"read_only": True},
            "username": {"read_only": True},
            "is_active": {"read_only": True if settings.ENVIRONMENT == "prod" else False},
            "is_blocked": {"read_only": True},
            "is_email_verified": {"read_only": True},
            "uid": {"read_only": True},
            "referral_code": {"read_only": True},
            "via_referral_code": {"read_only": True},
            "image_url": {"read_only": True}
        }

    def validate_email(self, value):
        if self.instance.is_email_verified and value:
            raise serializers.ValidationError("Cannot update email as existing email is already verified")
        return value

    def validate(self, attrs):
        state_code = attrs.get("state_code") or self.instance.state_code
        country = attrs.get("country") or self.instance.country
        if state_code and country and state_code not in constants.country_code_to_states.get(country, {}):
            raise serializers.ValidationError("combination of state and country is not valid")
        data = super().validate(attrs)
        return data


class UserGetSerializer(serializers.Serializer):
    total_contest = serializers.SerializerMethodField()
    total_matches = serializers.SerializerMethodField()
    primary_wallet = serializers.SerializerMethodField()
    win_wallet = serializers.SerializerMethodField()
    ref_wallet = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    aadhaar_verified = serializers.SerializerMethodField()
    pan_verified = serializers.SerializerMethodField()
    bank_verified = serializers.SerializerMethodField()
    recent_15_transactions = serializers.SerializerMethodField()
    recent_ten_teams = serializers.SerializerMethodField()
    recent_ten_contests = serializers.SerializerMethodField()

    def get_total_contest(self, obj):
        return UserTeamContest.objects.filter(user_id=obj.id).count()

    def get_total_matches(self, obj):
        return UserTeam.objects.filter(user_id=obj.id).count()

    def get_primary_wallet(self, obj):
        return 0

    def get_win_wallet(self, obj):
        return 0

    def get_ref_wallet(self, obj):
        return 0

    def get_account_status(self, obj):
        if obj.is_blocked:
            return "Blocked"
        elif obj.is_active:
            return "Active"
        else:
            return "InActive"

    def get_aadhaar_verified(self, obj):
        return None

    def get_pan_verified(self, obj):
        return None

    def get_bank_verified(self, obj):
        return None

    def get_recent_15_transactions(self, obj):
        return []

    def get_recent_ten_teams(self, obj):
        return []

    def get_recent_ten_contests(self, obj):
        return []