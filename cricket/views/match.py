from datetime import timedelta
import logging

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response

from alltime11 import constants
from cricket.models import Match, UserTeam, Contest, MatchPlayer, UserTeamContest
from cricket.serializers import MatchListSerializer, MatchSerializer, \
    MatchPlayerScoreCardSerializer, MatchGuideSerializer

logger = logging.getLogger('api')


class MatchListView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # date_today = datetime.today().date()
            match_query = Match.objects
            query_params = request.GET
            user = request.user

            match_query = match_query.filter(match_players__isnull=False)

            contest_only = constants.boolean_mapping.get(query_params.get("contest_only"), False)
            if contest_only is True:
                match_query = match_query.filter(contests__isnull=False).distinct()

            if not (user.is_superuser or user.is_staff):
                exclude_tbc_team = models.Q(team_a__uid='tbc') | models.Q(team_b__uid='tbc')
                till_date = timezone.now() + timedelta(days=8)
                match_query = match_query.filter(start_date__lte=till_date).exclude(exclude_tbc_team)

            match_status = None
            if query_params.get("status"):
                match_status = query_params.get("status")
            elif not (user.is_superuser or user.is_staff):
                match_status = constants.MATCH_STATUS_NOT_STARTED

            if match_status:
                match_query = match_query.filter(status=match_status)

            if match_status == constants.MATCH_STATUS_NOT_STARTED:
                match_query = match_query.filter(start_date__gte=timezone.now())

            my_matches = constants.boolean_mapping.get(query_params.get("my_matches"), False)
            if my_matches:
                match_query = match_query.filter(user_teams__isnull=False, user_teams__user_id=user.id)

            match_query = match_query.order_by('start_date').distinct()
            logger.debug(f"sql query to execute {match_query.query}")
            match_contest_userteam_count = {}
            matches = []
            for match in match_query:
                match_contest_userteam_count[match.id] = {
                    "contest_count": UserTeamContest.objects.filter(user=request.user, contest__match=match).values(
                        "contest").distinct().count(),
                    "userteam_count": UserTeam.objects.filter(match=match, user=request.user).count()
                }
                matches.append(match)

            match_prize_query = Contest.objects.values('match_id').annotate(max_prize=models.Max('prize'))
            match_wise_prize = {}
            for mp in match_prize_query:
                match_wise_prize[mp.get('match_id')] = mp.get('max_prize')

            serialized_data = MatchListSerializer(matches, many=True).data
            for m in serialized_data:
                m["contest_count"] = match_contest_userteam_count[m["id"]]["contest_count"]
                m["userteam_count"] = match_contest_userteam_count[m["id"]]["userteam_count"]
                m["prize"] = match_wise_prize.get(m["id"])
            data = {
                "data": {
                    "matches": serialized_data
                }
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: add logger.error
            return Response(data={"message": {"matches": ["matches does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)


class MatchRetrieveView(RetrieveUpdateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def retrieve(self, request, *args, **kwargs):
        match = self.get_object()
        ms = self.get_serializer(match)
        match_data = ms.data
        match_data["contest_count"] = UserTeamContest.objects.filter(user=request.user, contest__match=match).values(
            "contest").distinct().count()
        match_data["userteam_count"] = UserTeam.objects.filter(match=match, user=request.user).count()
        match_data["prize"] = Contest.objects.filter(match=match).aggregate(models.Max('prize')).get("prize__max")
        return Response({'data': {'match': match_data}}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        match = self.get_object()
        partial = kwargs.pop('partial', False)
        data = {
            "is_featured": request.data.get("is_featured", False)
        }
        ms = self.get_serializer(match, data=data, partial=partial)
        ms.is_valid(raise_exception=True)
        ms.save()
        return Response({'data': {'contest': ms.data}}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self.partial_update(request, *args, **kwargs)


class MatchScoreCardView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            match_data = Match.objects.filter(id=kwargs.get("pk")).values("team_a_id", "team_b_id", "team_a_score",
                                                                          "team_b_score", "team_a__name",
                                                                          "team_b__name", "first_batting_id").first()
            if not match_data:
                return Response(data={"message": {"match": ["matche does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)
            match_data.get('team_a_score').pop('balls_breakup')
            match_data.get('team_b_score').pop('balls_breakup')
            queryset = MatchPlayer.objects.filter(match_id=kwargs.get("pk"), is_playing=True)
            serializer_class = MatchPlayerScoreCardSerializer(queryset, many=True)
            score_card_data = serializer_class.data
            team_segregation = {}
            for sd in score_card_data:
                if sd.get("team_id") == match_data.get("team_a_id"):
                    team_key = f'team_a_player_score'
                else:
                    team_key = f'team_b_player_score'
                team_data = {
                    "batting_stats": sd.get("batting_stats"),
                    "bowling_stats": sd.get("bowling_stats"),
                    "player_name": sd.get("player_name"),
                    "is_captain": sd.get("is_captain"),
                    "is_keeper": sd.get("is_keeper"),
                    "is_batsman": sd.get("is_batsman"),
                    "is_bowler": sd.get("is_bowler"),
                    "is_all_rounder": sd.get("is_all_rounder"),
                    "playing_order": sd.get("playing_order")
                }
                if team_key in team_segregation:
                    team_segregation[team_key].append(team_data)
                else:
                    team_segregation[team_key] = [team_data]
            match_data["team_player_score"] = team_segregation
            return Response({'data': {'match': match_data}}, status=status.HTTP_200_OK)
        except Exception as ex:
            print(f"Error in get match score card api:{ex}")
            return Response(data={"message": {"match": ["Colud not fetch Match Score Card data"]}},
                            status=status.HTTP_400_BAD_REQUEST)


class MatchGuideView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            match = Match.objects.get(id=kwargs.get("pk"))
            mg_serializer = MatchGuideSerializer(match, many=False)
            return Response({'data': {"match":mg_serializer.data}}, status=status.HTTP_200_OK)
        except Match.DoesNotExist:
            # print(f"Error in get match score card api:{ex}")
            return Response(data={"message": {"match": ["Match not found"]}},
                            status=status.HTTP_404_NOT_FOUND)
