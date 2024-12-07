from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from alltime11 import constants
from cricket.models import Match, UserTeam, MatchPlayer, Player
from cricket.serializers import MatchPlayerSerializer

User = get_user_model()


class UserTeamSerializer(serializers.ModelSerializer):
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True
    )

    # captain = MatchPlayerSerializer(read_only=True)
    captain_id = serializers.PrimaryKeyRelatedField(
        queryset=MatchPlayer.objects.all(),
        source='captain',
        write_only=True
    )

    # vice_captain = MatchPlayerSerializer(read_only=True)
    vice_captain_id = serializers.PrimaryKeyRelatedField(
        queryset=MatchPlayer.objects.all(),
        source='vice_captain',
        write_only=True
    )

    class Meta:
        model = UserTeam
        exclude = []

        extra_kwargs = {
            'batsman_count': {'read_only': True},
            'bowler_count': {'read_only': True},
            'all_rounder_count': {'read_only': True},
            'keeper_count': {'read_only': True},
            'user': {'read_only': True},
            'match': {'read_only': True},
            'name': {'read_only': True},
            # 'captain': {'read_only': True},
            # 'vice_captain': {'write_only': True}
        }

    def validate(self, attrs):
        player_ids = attrs.get("players", [])
        match = attrs.get("match")
        captain = attrs.get("captain")
        vice_captain = attrs.get("vice_captain")

        if match.start_date - timedelta(days=constants.ADVANCED_TEAM_CREATE_DAYS) > timezone.now():
            raise ValidationError(
                f"cannot create team from a match, start date is more than {constants.ADVANCED_TEAM_CREATE_DAYS} days")

        if match.start_date < timezone.now():
            raise ValidationError(f"cannot create team from a match, start date is in the past")

        if UserTeam.objects.filter(match=match, user=attrs.get("user")).count() >= constants.MAX_USER_TEAM_COUNT:
            raise ValidationError(f"maximum of {constants.MAX_USER_TEAM_COUNT} teams are allowed per match")

        if captain and vice_captain and captain == vice_captain:
            raise ValidationError("captain and vice_captain can't be same")
        if vice_captain.id not in player_ids or captain.id not in player_ids:
            raise ValidationError("provided captain/vice_captain are not present in player ids")

        match_players = match.match_players.filter(id__in=player_ids)
        non_match_players = set(player_ids) - set(match_players.values_list("pk", flat=True))
        if non_match_players:
            raise ValidationError(f"players {non_match_players} doesn't belong to the match")

        total_player_credits = match_players.aggregate(sum=Sum('player_credits')).get("sum") or 0
        if total_player_credits <= 0 or total_player_credits > 100:
            raise ValidationError(f"sum of selected player credits is greater than 100")

        # not_playing_player = list(match_players.filter(is_playing=False).values_list('pk', flat=True))
        # if not_playing_player:
        #     raise ValidationError(f"players {not_playing_player} are not in the playing 11 from either team")

        batsman_count = 0
        keeper_count = 0
        bowler_count = 0
        all_r_count = 0
        for mp in match_players.values('is_batsman', 'is_bowler', 'is_all_rounder', 'is_keeper'):
            if mp['is_keeper']:
                keeper_count += 1
            elif mp['is_batsman']:
                batsman_count += 1
            elif mp['is_all_rounder']:
                all_r_count += 1
            elif mp['is_bowler']:
                bowler_count += 1

        # individual counts
        if batsman_count < constants.MIN_BAT_COUNT:
            raise ValidationError(f"team must have {constants.MIN_BAT_COUNT} minimum batsman")
        if keeper_count < constants.MIN_KEEPER_COUNT:
            raise ValidationError(f"team must have {constants.MIN_KEEPER_COUNT} minimum keeper")
        if all_r_count < constants.MIN_ALL_R_COUNT:
            raise ValidationError(f"team must have {constants.MIN_ALL_R_COUNT} minimum all rounder")
        if bowler_count < constants.MIN_BOW_COUNT:
            raise ValidationError(f"team must have {constants.MIN_BOW_COUNT} minimum bowler")

        # team count
        if keeper_count + batsman_count + bowler_count + all_r_count < 11:
            raise ValidationError(f"team must have 11 players")

        for row in match_players.values('team').annotate(player_count=Count('team')):
            if row['player_count'] < 4:
                raise ValidationError(f"there are only {row['player_count']} players from team {row['team']}")

        attrs['batsman_count'] = batsman_count
        attrs['bowler_count'] = bowler_count
        attrs['all_rounder_count'] = all_r_count
        attrs['keeper_count'] = keeper_count
        attrs['players'] = {p_id: {} for p_id in attrs['players']}

        data = super().validate(attrs)
        return data

    def save(self, **kwargs):
        super().save(**kwargs)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        player_ids = [int(player_id) for player_id, _ in data.get("players").items()]
        # TODO: optimize this database query by using prefetch for player and loading only name from player table
        match_players = MatchPlayer.objects.filter(id__in=player_ids).all()

        players = []
        for mp in MatchPlayerSerializer(match_players, many=True).data:
            mp["is_captain"] = True if mp["id"] == instance.captain_id else False
            mp["is_vice_captain"] = True if mp["id"] == instance.vice_captain_id else False
            players.append(mp)

        data["players"] = players

        return data


class UserTeamPlayerStatusSerializer(serializers.ModelSerializer):
    players = serializers.SerializerMethodField()

    def get_players(self, obj):
        # fetch all teams for match id
        player_selection_data = {}
        all_teams = UserTeam.objects.filter(match_id=obj.match_id).values('players')
        total_teams = all_teams.count()
        for all_team in all_teams:
            for player_id in all_team.get('players'):
                player_key = f'player_{player_id}'
                if player_key in player_selection_data:
                    player_selection_data[player_key] += 1
                else:
                    player_selection_data[player_key] = 1
        user_team_players = obj.players.keys()
        players_data = Player.objects.filter(id__in=user_team_players).values('id', 'name', 'seasonal_role')
        result_data = []
        for data in players_data:
            player_info = {"player__id":data["id"], "player__name":data["name"], "player__seasonal_role":data["seasonal_role"]}
            match_player = MatchPlayer.objects.filter(player_id=data.get("id"), match_id=obj.match_id).values('player_points').first()
            player_info["player_points"] = 0
            if match_player:
                if data.get('id') == obj.captain_id :
                    player_info["player_points"] = float(match_player["player_points"]) * 2
                if data.get('id') == obj.vice_captain_id:
                    player_info["player_points"] = float(match_player["player_points"]) * 1.5
                else:
                    player_info["player_points"] = match_player["player_points"]
            player_info['selected_by'] = 0
            player_key = f'player_{data.get("id")}'
            if player_key in player_selection_data:
                player_info['selected_by'] = f'{int((player_selection_data[player_key] * 100) / total_teams)}%'
            result_data.append(player_info)
        return result_data

    class Meta:
        model = UserTeam
        fields = ('match_id', 'players', 'captain_id', 'vice_captain_id')


