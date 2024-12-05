from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from alltime11 import constants
from common_api.models import Reward

User = get_user_model()


class RewardSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all()
    )

    class Meta:
        model = Reward
        fields = [
            "reward_type", "discount_percentage", "discount_amount", "max_discount_amount", "max_redeem_count",
            "start_date", "end_date", "is_active", "user_id", "status", "id", "code", "redeem_count"
        ]

        extra_kwargs = {
            "status": {"read_only": True},
            "code": {"read_only": True},
            "redeem_count": {"read_only": True}
        }

    def validate(self, attrs):
        reward_type = attrs.get("reward_type")
        if reward_type not in {constants.RC_WALLET, constants.RC_SIGNUP, constants.RC_CONTEST}:
            raise serializers.ValidationError(f"reward_type can be one of {constants.RC_WALLET}, {constants.RC_SIGNUP},"
                                              f"{constants.RC_CONTEST}")

        start_date = attrs.get("start_date")
        if start_date.date() < timezone.now().date():
            raise serializers.ValidationError("start_date must not be less than today")

        if attrs.get("user").is_superuser or attrs.get("user").is_staff:
            raise serializers.ValidationError("can't generate reward token for admin user")

        data = super().validate(attrs)
        return data
