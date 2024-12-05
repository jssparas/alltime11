from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers
from django.db.models import Q

from alltime11 import constants
from cricket.models import Match
from .match_player import MatchPlayerSerializer
from .team import TeamSerializer
from .tournament import TournamentSerializer


class MatchListSerializer(serializers.ModelSerializer):
    team_a = TeamSerializer(read_only=True)
    team_b = TeamSerializer(read_only=True)
    tournament = TournamentSerializer(read_only=True)
    can_join_contest = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Match
        fields = ["id", "team_a", "team_b", "tournament", "uid", "name", "short_name", "subtitle", "venue_name",
                  "venue_city", "play_status", "title", "match_format", "start_date", "end_date",
                  "can_join_contest", "is_featured"]

    def get_can_join_contest(self, obj):
        if obj.start_date - timezone.now() <= timedelta(days=constants.ADVANCED_TEAM_CREATE_DAYS):
            return True
        else:
            return False


class MatchSerializer(serializers.ModelSerializer):
    match_players = MatchPlayerSerializer(many=True, read_only=True)
    team_a = TeamSerializer(read_only=True)
    team_b = TeamSerializer(read_only=True)
    tournament = TournamentSerializer(read_only=True)
    can_join_contest = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Match
        fields = '__all__'

    def get_can_join_contest(self, obj):
        if obj.start_date - timezone.now() <= timedelta(days=constants.ADVANCED_TEAM_CREATE_DAYS):
            return True
        else:
            return False


class MatchGuideSerializer(serializers.ModelSerializer):
    related_matches = serializers.SerializerMethodField(read_only=True)
    venue_matches = serializers.SerializerMethodField(read_only=True)
    head_to_head_details = serializers.SerializerMethodField(read_only=True)

    def get_related_matches(self, obj):
        team_a_matches = Match.objects.filter(Q(status=constants.MATCH_STATUS_COMPLETED), Q(winner_id__isnull=False), \
                            Q(match_format=obj.match_format), Q(Q(team_a=obj.team_a)|Q(team_b=obj.team_a))).values('winner_id').order_by('-id')[:5]
        team_a_winnings = ["W" if obj.team_a_id == match.get("winner_id") else "L" for match in team_a_matches]
        team_b_matches = Match.objects.filter(Q(status=constants.MATCH_STATUS_COMPLETED), Q(winner_id__isnull=False), \
                            Q(Q(team_a=obj.team_b)|Q(team_b=obj.team_b))).values('winner_id').order_by('-id')[:5]
        team_b_winnings = ["W" if obj.team_b_id == match.get("winner_id") else "L" for match in team_b_matches]
        data = {
                "team_a_name": obj.team_a.name,
                "team_a_last5_winnings": team_a_winnings,
                "team_b_name": obj.team_b.name,
                "team_b_last5_winnings": team_b_winnings,
            }
        return data

    def get_venue_matches(self, obj):
        recent_matches = Match.objects.filter(Q(status=constants.MATCH_STATUS_COMPLETED), Q(match_format=obj.match_format), \
                        Q(Q(team_a_score__isnull=False)|Q(team_b_score__isnull=False))).values('team_a_score', 'team_b_score').order_by('-id')[:5]
        total_runs = 0
        total_team = 0
        total_wickets = 0
        avg_runs = 0
        for match in recent_matches:
            if match.get("team_a_score"):
                team_a_score = match.get("team_a_score")
                if team_a_score.get("wickets"):
                    total_wickets += team_a_score.get("wickets")
                if team_a_score.get("score"):
                    total_team += 1
                    total_runs += team_a_score.get("score").get("runs")
            if match.get("team_b_score"):
                team_b_score = match.get("team_b_score")
                if team_b_score.get("wickets"):
                    total_wickets += team_b_score.get("wickets")
                if team_b_score.get("score"):
                    total_team += 1
                    total_runs += team_b_score.get("score").get("runs")
        if total_team:
            avg_runs = total_runs / total_team
        return  {"total_wickets": total_wickets, "total_avg_runs": round(avg_runs, 2)}

    def get_head_to_head_details(self, obj):
        last_5years_date = timezone.now() - relativedelta(years=5)
        matches = Match.objects.filter(Q(status=constants.MATCH_STATUS_COMPLETED), Q(match_format=obj.match_format), \
                    Q(created_on__gte=last_5years_date), Q(Q(team_a=obj.team_a)|Q(team_a=obj.team_b)), \
                    Q(Q(team_b=obj.team_a)|Q(team_b=obj.team_b))).values("play_status", "winner_id", "win_type")
        total_played_matches = matches.count()
        total_a_winnings = total_b_winnings = total_draws = total_abandoned = 0
        for match in matches:
            if match.get("play_status") == "abandoned":
                total_abandoned += 1
            elif match.get("play_status") == "result":
                if match.get("win_type") == "draw" and not match.get("winner_id"):
                    total_draws += 1
                elif match.get("winner_id"):
                    if match.get("winner_id") == obj.team_a_id:
                        total_a_winnings += 1
                    elif match.get("winner_id") == obj.team_b_id:
                        total_b_winnings += 1
        result_data = {
                        "total_played_matches": total_played_matches,
                        "total_a_winnings": total_a_winnings,
                        "total_b_winnings": total_b_winnings,
                        "total_draws": total_draws,
                        "total_abandoned": total_abandoned,
                    }
        return result_data

    class Meta:
        model = Match
        fields = ('related_matches', 'venue_matches', 'venue_name', 'venue_city', "venue_country", "head_to_head_details")
