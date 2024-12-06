from collections import OrderedDict

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from alltime11 import constants
from cricket.models import Match, Contest, UserTeamContest
from .match import MatchListSerializer


class ContestListSerializer(serializers.ModelSerializer):
    # match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True
    )

    class Meta:
        model = Contest
        fields = ["id", "name", "prize", "entry_fees", "no_of_teams", "contest_type", "is_active", "match_id",
                  "entries_left", "discount_percentage", "prize_distribution", "is_private", "status", "is_featured"]
        extra_kwargs = {
            'tournament': {'read_only': True},
            'created_by': {'read_only': True},
            'prize': {'read_only': True},
            'status': {'read_only': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('view') == 'mycontests':
            my_teams = []
            user = self.context.get('user')
            for row in UserTeamContest.objects.filter(contest=instance, user=user).values('rank', 'user_team__name'):
                my_teams.append({
                    'rank': row.get('rank'),
                    'team_name': row.get('user_team__name'),
                    'user_name': user.name
                })
            data['my_teams'] = my_teams
        return data


class ContestSerializer(serializers.ModelSerializer):
    match = MatchListSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True
    )

    class Meta:
        model = Contest
        fields = ["id", "name", "prize", "entry_fees", "no_of_teams", "contest_type", "is_active", "match_id", "match",
                  "entries_left", "discount_percentage", "prize_distribution", "is_private", "status", "is_featured"]
        extra_kwargs = {
            'tournament': {'read_only': True},
            'created_by': {'read_only': True},
            'prize': {'read_only': True},
            'status': {'read_only': True},
            'is_private': {'read_only': True},
        }

    def validate(self, attrs):
        match = attrs.get("match") or self.instance.match

        if match.status != constants.MATCH_STATUS_NOT_STARTED:
            raise ValidationError("match is already started or completed")

        if not self.instance and Contest.objects.filter(name=attrs.get("name"), match=match).exists():
            raise ValidationError("contest with this name already exists for the provided match")
        elif self.instance:
            if attrs.get('name') and Contest.objects.filter(name=attrs.get("name")).exists() and \
                    match.status == 'started':
                raise ValidationError("contest with this name already exists for another active match")
            if attrs.get('is_active') is False:
                if self.instance.is_active and self.instance.entries_left != self.instance.no_of_teams:
                    raise ValidationError("contest already has participating teams, cannot mark inactive")
            if attrs.get('is_active') is True:
                if not self.instance.is_active and match.status != 'not_started':
                    raise ValidationError("associated match is started/in_play/completed, cannot mark active")

        attrs["tournament_id"] = match.tournament.id
        entry_fees = attrs.get("entry_fees") or self.instance.entry_fees
        no_of_teams = attrs.get("no_of_teams") or self.instance.no_of_teams
        prize = no_of_teams * entry_fees
        attrs["prize"] = prize

        contest_type = attrs.get("contest_type")
        if contest_type == "head_to_head":
            self.validate_head_to_head_contest(attrs)
        elif contest_type == "takes_all":
            self.validate_takes_all_contest(attrs)
        elif contest_type in {"mega", "medium"}:
            if "prize_distribution" not in attrs:
                raise ValidationError(f"please provide prize distribution for {contest_type} contest")
            self.validate_mega_contest(attrs)

        data = super().validate(attrs)
        return data

    def validate_takes_all_contest(self, attrs):
        no_of_teams = attrs.get("no_of_teams") or self.instance.no_of_teams
        if not (3 <= no_of_teams <= 9):
            raise ValidationError("number of participating teams should be at least 3 and max 9")

        attrs["prize_distribution"] = {
            str(attrs["prize"] - (attrs["prize"] * constants.PLATFORM_FEES)): "1"
        }

    def validate_head_to_head_contest(self, attrs):
        no_of_teams = attrs.get("no_of_teams") or self.instance.no_of_teams
        if no_of_teams != 2:
            raise ValidationError("number of participating teams should be 2")

        attrs["prize_distribution"] = {
            str(attrs["prize"] - (attrs["prize"] * constants.PLATFORM_FEES)): "1"
        }

    def validate_mega_contest(self, attrs):
        """
        {
            10000: "1",
            7000: "2",
            5000: "3-5",
            100: "6-10",
        }
        """
        prize_distribution = attrs.pop("prize_distribution", None)
        sorted_prize_money = sorted(map(lambda x: int(x), prize_distribution.keys()), reverse=True)

        money_in_distribution = 0
        pz = OrderedDict()

        for pm in sorted_prize_money:
            rank_range = prize_distribution[str(pm)]
            pz[pm] = rank_range
            if "-" in rank_range:
                min_rank, max_rank = rank_range.split("-")
                winner_count = int(max_rank) - int(min_rank) + 1
            else:
                winner_count = 1
            money_in_distribution += winner_count * pm

        # check on total prize money distribution
        total_money = attrs["prize"] - (attrs["prize"] * constants.PLATFORM_FEES)
        if total_money < money_in_distribution:
            raise ValidationError("prize distribution does not satisfy the 12% platform fees criteria")

        attrs["prize_distribution"] = pz
        attrs["is_private"] = False
        return attrs
