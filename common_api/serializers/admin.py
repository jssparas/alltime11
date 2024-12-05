from rest_framework import serializers

from users.models import User
from cricket.models import Match
from alltime11.constants import MATCH_STATUS_STARTED, MATCH_STATUS_COMPLETED, \
    MATCH_STATUS_NOT_STARTED


class DashboardSerializer(serializers.Serializer):
    registered_users = serializers.SerializerMethodField()
    verified_email_users = serializers.SerializerMethodField()
    verified_pan_users = serializers.SerializerMethodField()
    verified_bank_users = serializers.SerializerMethodField()
    pending_kyc_users = serializers.SerializerMethodField()
    pending_bank_doc_users = serializers.SerializerMethodField()
    pending_withdrawals = serializers.SerializerMethodField()
    live_matches = serializers.SerializerMethodField()
    completed_matches = serializers.SerializerMethodField()
    upcoming_matches = serializers.SerializerMethodField()

    def get_registered_users(self, obj):
        return User.objects.filter(is_superuser=False, is_active=True, is_staff=False).count()

    def get_verified_email_users(self, obj):
        return User.objects.filter(is_superuser=False, is_staff=False, is_email_verified=True).count()
    
    def get_verified_pan_users(self, obj):
        return 0

    def get_verified_bank_users(self, obj):
        return 0

    def get_pending_kyc_users(self, obj):
        return 0

    def get_pending_bank_doc_users(self, obj):
        return 0

    def get_pending_withdrawals(self, obj):
        return 0

    def get_live_matches(self, obj):
        return Match.objects.filter(status=MATCH_STATUS_STARTED).count()

    def get_completed_matches(self, obj):
        return Match.objects.filter(status=MATCH_STATUS_COMPLETED).count()

    def get_upcoming_matches(self, obj):
        return Match.objects.filter(status=MATCH_STATUS_NOT_STARTED).count()
