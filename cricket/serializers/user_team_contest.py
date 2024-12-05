from django.conf import settings
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from alltime11 import constants
from cricket.models import UserTeamContest, Contest, UserTeam
from cricket.tasks import create_head_to_head_contest


class UserTeamContestSerializer(serializers.ModelSerializer):
    # contest = ContestListSerializer(read_only=True)
    contest_id = serializers.PrimaryKeyRelatedField(
        queryset=Contest.objects.all(),
        source="contest",
        write_only=True
    )

    user_team_id = serializers.PrimaryKeyRelatedField(
        queryset=UserTeam.objects.all(),
        source="user_team",
        write_only=True
    )

    class Meta:
        model = UserTeamContest
        fields = ["user_team_id", "contest_id", "rank", "id", "contest", "user_team"]
        extra_kwargs = {
            "id": {"read_only": True},
            "rank": {"read_only": True},
            "contest": {"read_only": True},
            "user_team": {"read_only": True}
        }

    def validate(self, attrs):
        user_team = attrs.get("user_team")
        contest = attrs.get("contest")
        user = self.context['request'].user
        if user != user_team.user:
            raise ValidationError("user_team does not exists")

        if contest.match != user_team.match:
            raise ValidationError("user_team and contest belongs to different match")

        entries_left = contest.entries_left
        if entries_left == 1:
            create_head_to_head_contest.delay({
                "name": f"{contest.name} {contest.id + 1}",
                "entry_fees": contest.entry_fees,
                "user_id": settings.ADMIN_USER_ID,
                "match_id": contest.match.id
            })

        if entries_left <= 0:
            raise ValidationError("no entries left in this contest to participate")

        if UserTeamContest.objects.filter(user=user, user_team=user_team, contest=contest).count() >= 1:
            raise ValidationError("user has already participated in the contest with this team")

        if contest.status != constants.CONTEST_STATUS_NOT_STARTED:
            raise ValidationError("contest is either started or completed")

        if contest.contest_type == 'head_to_head':
            max_team_count = constants.HEAD_TO_HEAD_USER_TEAM_COUNT
            self.validate_head_to_head_join_rules(user, contest)
        elif contest.contest_type == 'takes_all':
            max_team_count = constants.TAKES_ALL_USER_TEAM_COUNT
        elif contest.contest_type == 'mega':
            max_team_count = constants.MEGA_USER_TEAM_COUNT
        else:
            max_team_count = 0

        if UserTeamContest.objects.filter(user=user, contest=contest).count() >= max_team_count:
            raise ValidationError(f"user has already participated in the contest with {max_team_count} teams")

        attrs["user"] = user
        attrs["entry_type"] = "unique" if contest.contest_type == "head_to_head" else "multiple"
        data = super().validate(attrs)
        return data

    @staticmethod
    def validate_head_to_head_join_rules(user, contest):
        # TODO: discuss the private contest sharing link and checks
        if contest.is_private and contest.created_by != user:
            raise ValidationError("cannot join a private contest unless invited")

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["user_name"] = instance.user.name
        data["user_username"] = instance.user.username
        data["team_name"] = instance.user_team.name
        data["team_points"] = instance.user_team.points

        return data
