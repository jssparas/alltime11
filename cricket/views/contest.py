from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Q, Subquery
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response

from alltime11 import constants
from cricket.models import Match, Contest, UserTeamContest
from cricket.serializers import ContestListSerializer, ContestSerializer


class ContestListCreateView(APIView):
    def get(self, request, match_id):
        try:
            match = Match.objects.get(pk=match_id)
            contest_query = Contest.objects.filter(match=match)

            filter_date = timezone.now() + timedelta(days=constants.ADVANCED_TEAM_CREATE_DAYS)
            if not (request.user.is_superuser or request.user.is_staff):
                contest_query = contest_query.filter(match__start_date__lte=filter_date)
                contest_query = contest_query.filter(is_active=True, is_private=False)

            query_params = request.GET
            # TODO: based on the query params, apply filters

            contests = contest_query.order_by('created_on')
            all_contests = []
            for c in contests:
                if c.entries_left > 0:
                    all_contests.append(c)
            # private_contests = Contest.objects.filter(match=match, match__start_date__lte=filter_date,
            #                                           created_by=request.user, is_private=True).order_by(
            #     'created_on').all()

            # all_contests = contests.union(private_contests)
            data = {
                "data": {
                    "contests": ContestListSerializer(all_contests, many=True).data
                }
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: add logger.error
            return Response(data={"message": {"contests": ["match does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)

    def post(self, request, match_id):
        try:
            # if request.data.get("contest_type") != "head_to_head" and \
            #         not (request.user.is_staff or request.user.is_superuser):
            #     return Response(status=status.HTTP_403_FORBIDDEN)
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(status=status.HTTP_403_FORBIDDEN)

            match = Match.objects.get(pk=match_id)
            contest_serializer = ContestSerializer(data={**request.data, **{'match_id': match.id}})
            if contest_serializer.is_valid(raise_exception=True):
                contest_serializer.save(created_by=request.user)
                data = {
                    "data": {
                        "contest": contest_serializer.data
                    }
                }
                return Response(data=data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as obne:
            # TODO: add logger.error
            return Response(data={"message": {"contests": ["match does not exists"]}},
                            status=status.HTTP_404_NOT_FOUND)


class ContestRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Contest.objects.all()
    serializer_class = ContestSerializer

    def filter_queryset(self, queryset):
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            filter_conditions = Q(is_private=False) | Q(created_by=self.request.user)
            queryset = queryset.filter(filter_conditions)
        return super().filter_queryset(queryset)

    def retrieve(self, request, *args, **kwargs):
        contest = self.get_object()
        cs = self.get_serializer(contest)
        return Response({'data': {'contest': cs.data}}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if "contest_type" in request.data or "match_id" in request.data:
            return Response(data={'message': {'contest': ['cannot update contest_type/match']}},
                            status=status.HTTP_400_BAD_REQUEST)

        contest = self.get_object()
        contest_type = contest.contest_type
        if contest_type != "head_to_head" and not (request.user.is_staff or request.user.is_superuser):
            return Response(status=status.HTTP_403_FORBIDDEN)
        partial = kwargs.pop('partial', False)

        cs = self.get_serializer(contest, data=request.data, partial=partial)
        cs.is_valid(raise_exception=True)
        cs.save(created_by=request.user)
        return Response({'data': {'contest': cs.data}}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class MyContestListView(APIView):
    def get(self, request, *args, **kwargs):
        match_id = kwargs.get("match_id")
        subquery = UserTeamContest.objects.filter(user=request.user, contest__match__id=match_id).values(
            "contest").distinct()
        contests = Contest.objects.filter(pk__in=Subquery(subquery))
        cs = ContestListSerializer(contests, many=True, context={'view': 'mycontests', 'user': request.user})
        return Response(data={
            'data': {
                'contests': cs.data
            }
        }, status=status.HTTP_200_OK)
